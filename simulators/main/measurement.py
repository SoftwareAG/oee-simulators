import logging
from datetime import datetime
from random import uniform, randint, gauss
from cumulocityAPI import CumulocityAPI
from task import PeriodicTask
import interface

cumulocityAPI = CumulocityAPI()
log = logging.getLogger("measurements generation")


class Measurement:
    # Measurements functions #
    def __init__(self, model) -> None:
        self.model = model
        self.device_id = self.model.get("device_id")
        self.simulated_data = {}
        self.measurements_definitions = self.model.get('measurements', [])
        self.enabled = self.model.get('enabled', True)
        if self.enabled:
            self.tasks = list(map(self.__create_task, self.measurements_definitions))
            log.debug(f'measurements: {self.measurements_definitions}')

    def __create_task(self, definition):
        measurement_callback = lambda task: {Measurement.measurement_functions(self, definition, task)}
        min_interval_in_seconds, max_interval_in_seconds = interface.calculate_interval_in_seconds(definition)
        if definition:
            log.debug(f'Machine {self.model.get("label")}, id {self.model.get("id")}: create periodic task for measurement {definition["series"]}, interval ({min_interval_in_seconds}, {max_interval_in_seconds}) seconds')
        else:
            log.debug(f'No definition of measurement in machine {self.model.get("label")}, id {self.model.get("id")}')

        task = PeriodicTask(min_interval_in_seconds, max_interval_in_seconds, measurement_callback)

        return task

    def measurement_functions(self, measurement_definition, task):
        Measurement.generate_measurement(self=self, measurement_definition=measurement_definition)
        Measurement.send_measurements(self=self, measurement_definition=measurement_definition)

    def generate_measurement(self, measurement_definition):
        log.info(f"Generating value of measurement {measurement_definition.get('series')} of device {self.model.get('id')}")
        distribution = measurement_definition.get("valueDistribution", "uniform")
        value = 0.0
        if distribution == "uniform":
            min_value = measurement_definition.get("minimumValue", measurement_definition.get("value"))
            max_value = measurement_definition.get("maximumValue", measurement_definition.get("value"))
            value = round(uniform(min_value, max_value), 2)
        elif distribution == "uniformint":
            min_value = measurement_definition.get("minimumValue", measurement_definition.get("value"))
            max_value = measurement_definition.get("maximumValue", measurement_definition.get("value"))
            value = randint(min_value, max_value)
        elif distribution == "normal":
            mu = measurement_definition.get("mu")
            sigma = measurement_definition.get("sigma")
            value = round(gauss(mu, sigma), 2)
        self.simulated_data = {
            'type': measurement_definition.get("type"),
            'series': measurement_definition.get("series"),
            'value': value,
            'unit': measurement_definition.get("unit"),
            'time': datetime.utcnow()
        }

    def send_measurements(self, measurement_definition):
        if not self.simulated_data:
            log.info(f"No measurement definition to create measurements for device #{self.device_id}, external id {self.model.get('id')}")
            return
        base_dict = Measurement.create_extra_info_dict(self=self, data=self.simulated_data)
        measurement_dict = Measurement.create_individual_measurement_dict(self=self, data=self.simulated_data)
        base_dict.update(measurement_dict)
        log.info('Send create measurements requests')
        response = cumulocityAPI.create_measurements(measurement=base_dict)
        if response:
            log.info(f"Created new {measurement_definition.get('type')} measurement, series {measurement_definition.get('series')} with value {self.simulated_data.get('value')}{self.simulated_data.get('unit')} for device {self.model.get('label')}, id {self.model.get('id')}")

    def create_extra_info_dict(self, data):
        extraInfoDict = {
            "type": f"{data.get('type')}",
            "time": f"{interface.datetime_to_string(data.get('time'))}",
            "source": {
                "id": f"{self.device_id}"
            }
        }
        return extraInfoDict

    def create_individual_measurement_dict(self, data):
        measurementDict = {
            f"{data.get('type')}":
                {
                    f"{data.get('series')}":
                        {
                            "unit": f"{data.get('unit')}",
                            "value": data.get('value')
                        }
                }
        }
        return measurementDict

    def tick(self):
        if not self.enabled:
            return
        for task in self.tasks:
            if task:
                task.tick()