import sys
import json, os, logging, requests, base64
from datetime import datetime, timedelta, time
from random import randint, uniform, choices, gauss
from cumulocityAPI import C8Y_BASE, C8Y_TENANT, C8Y_USER, C8Y_PASSWORD, CumulocityAPI
from task import PeriodicTask, Task

logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.DEBUG)
log = logging.getLogger("measurement")
cumulocityAPI = CumulocityAPI()


class Measurements:

    def __init__(self, model) -> None:
        self.model = model
        self.device_id = None
        self.enabled = model.get('enabled', True)
        self.simulated_data = []
        self.measurements_definition = self.model["measurements"]
        self.timestamp = datetime.utcnow()
        if self.enabled:
            self.tasks = list(map(self.__create_task, self.model["measurements"]))

    def __create_task(self, measurement_definition):
        min_per_hour = measurement_definition.get("minimumFrequency", measurement_definition.get("frequency"))
        max_per_hour = measurement_definition.get("maximumFrequency", measurement_definition.get("frequency"))

        min_interval_in_seconds = int(3600 / min_per_hour)
        max_interval_in_seconds = int(3600 / max_per_hour)

        event_callback = lambda task, timestamp: {
            Measurements.generate_measurement(self, measurement_definition, task, timestamp)}

        task = PeriodicTask(min_interval_in_seconds, max_interval_in_seconds, event_callback)
        return task

    def tick(self):
        if not self.enabled: return
        for task in self.tasks:
            task.tick()

    def send_create_measurements(self):
        json_measurement_list = []
        if not self.simulated_data:
            log.info(f"No measurement definition to create measurements for device #{self.device_id}, external id {self.model.get('id')}")
            return
        for data_dict in self.simulated_data:
            log.info('Send create measurements requests')
            base_dict = Measurements.create_extra_info_dict(self=self, data=data_dict)
            measurement_dict = Measurements.create_individual_measurement_dict(self=self, data=data_dict)
            base_dict.update(measurement_dict)
            json_measurement_list.append(base_dict)
        cumulocityAPI.create_measurements(self=self, measurements=json_measurement_list)
        log.info("Finished create new measurements")

    def create_extra_info_dict(self, data):
        extraInfoDict = {
            "type": f"{data.get('type')}",
            "time": f"{data.get('time')}",
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
                            "value": f"{data.get('value')}"
                        }
                }
        }
        return measurementDict

    def generate_measurement(self):
        for measurement_def in self.measurements_definition:
            distribution = measurement_def.get("valueDistribution", "uniform")
            value = 0.0
            if (distribution == "uniform"):
                min_value = measurement_def.get("minimumValue", measurement_def.get("value"))
                max_value = measurement_def.get("maximumValue", measurement_def.get("value"))
                value = round(uniform(min_value, max_value), 2)
            elif (distribution == "uniformint"):
                min_value = measurement_def.get("minimumValue", measurement_def.get("value"))
                max_value = measurement_def.get("maximumValue", measurement_def.get("value"))
                value = randint(min_value, max_value)
            elif (distribution == "normal"):
                mu = measurement_def.get("mu")
                sigma = measurement_def.get("sigma")
                value = round(gauss(mu, sigma), 2)
            self.simulated_data.append({
                'type': measurement_def.get("type"),
                'series': measurement_def.get("series"),
                'value': value,
                'unit': measurement_def.get("unit"),
                'time': f"{self.timestamp}"
            })

    def get_or_create_device_id(self):
        sim_id = self.model['id']
        label = self.model['label']
        self.device_id = cumulocityAPI.get_or_create_device(sim_id, label)


def load(filename):
    try:
        with open(filename) as f_obj:
            return json.load(f_obj)
    except Exception as e:
        print(e, type(e))
        return {}


log.info(f'cwd:{os.getcwd()}')
SIMULATOR_MODELS = load("simulators.json")

simulators = list(map(lambda model: Measurements(model), SIMULATOR_MODELS))

# set device id for each managed object in simulators
[item.get_or_create_device_id() for item in simulators]

for item in simulators:
    Measurements.generate_measurement(item)
    Measurements.send_create_measurements(item)

while True:
    for simulator in simulators:
        simulator.tick()
    time.sleep(1)

log.info(f'Finished simulation')
