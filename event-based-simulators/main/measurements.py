import time, json, os, logging
from datetime import datetime
from random import randint, uniform, choices, gauss
from cumulocityAPI import CumulocityAPI
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
        self.measurements_definitions = self.model["measurements"]
        self.current_time = datetime.utcnow()
        self.is_first_time = True
        if self.enabled and len(self.measurements_definitions) > 0 :
            self.tasks = self.__create_task(self.measurements_definitions[0])

    def __create_task(self, measurement_definition):
        min_frequency_per_hour = measurement_definition.get("minimumFrequency", measurement_definition.get("frequency"))
        max_frequency_per_hour = measurement_definition.get("maximumFrequency", measurement_definition.get("frequency"))

        min_interval_in_seconds = int(3600 / max_frequency_per_hour)
        max_interval_in_seconds = int(3600 / min_frequency_per_hour)

        measurements_callback = lambda task: {self.main_function}(task)

        task = PeriodicTask(min_interval_in_seconds, max_interval_in_seconds, measurements_callback)
        return task

    def tick(self):
        if not self.enabled: return
        #for task in self.tasks:
        self.tasks.tick()

    def main_function(self, measurement_definition):
        print('abc')

    def generate_measurement(self, measurement_definition, next_datetime):
        print(f"Generating value of measurement {measurement_definition.get('series')} of device {self.model.get('id')}")
        self.simulated_data = []
        distribution = measurement_definition.get("valueDistribution", "uniform")
        value = 0.0
        if (distribution == "uniform"):
            min_value = measurement_definition.get("minimumValue", measurement_definition.get("value"))
            max_value = measurement_definition.get("maximumValue", measurement_definition.get("value"))
            value = round(uniform(min_value, max_value), 2)
        elif (distribution == "uniformint"):
            min_value = measurement_definition.get("minimumValue", measurement_definition.get("value"))
            max_value = measurement_definition.get("maximumValue", measurement_definition.get("value"))
            value = randint(min_value, max_value)
        elif (distribution == "normal"):
            mu = measurement_definition.get("mu")
            sigma = measurement_definition.get("sigma")
            value = round(gauss(mu, sigma), 2)
        self.simulated_data.append({
            'type': measurement_definition.get("type"),
            'series': measurement_definition.get("series"),
            'value': value,
            'unit': measurement_definition.get("unit"),
            'time': self.current_time,
            'next_time': next_datetime
        })
        measurement_definition.update({'next_time': next_datetime})
        log.info(f"Next simulated time of {self.model.get('id')}: {measurement_definition.get('next_time')}")
        print("abc")

    def create_next_timestamp(self):
        next_timestamp = []
        for task in self.tasks:
            next_timestamp.append(datetime.fromtimestamp(task.next_run))
            print(next_timestamp)
        return next_timestamp

    def send_create_measurements(self, measurement_definition):
        json_measurements_list = []
        if not self.simulated_data:
            log.info(
                f"No measurement definition to create measurements for device #{self.device_id}, external id {self.model.get('id')}")
            return
    #for data_dict in self.simulated_data:
        base_dict = Measurements.create_extra_info_dict(self=self, data=self.simulated_data[0])
        measurement_dict = Measurements.create_individual_measurement_dict(self=self, data=self.simulated_data[0])
        base_dict.update(measurement_dict)
        json_measurements_list.append(base_dict)
    #for item in json_measurements_list:
        log.info('Send create measurements requests')
        cumulocityAPI.create_measurements(measurement=json_measurements_list[0])
        log.info(f"Created new {measurement_definition.get('type')} measurement, series {measurement_definition.get('series')} with value {self.simulated_data[0].get('value')}{self.simulated_data[0].get('unit')} for device {self.model.get('label')}")

    def create_extra_info_dict(self, data):
        extraInfoDict = {
            "type": f"{data.get('type')}",
            "time": f"{datetime_to_string(data.get('time'))}",
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


def datetime_to_string(date_time, time_string_format="%Y-%m-%dT%H:%M:%S.%f"):
    return date_time.strftime(time_string_format)[:-3] + 'Z'


###################################################################################
log.info(f'cwd:{os.getcwd()}')
SIMULATOR_MODELS = load("simulators.json")

simulators = list(map(lambda model: Measurements(model), SIMULATOR_MODELS))

# set device id for each managed object in simulators
[item.get_or_create_device_id() for item in simulators]
count = 1
'''
while True:

    for simulator in simulators:
        log.info(f"Running measurements generation for device with id {simulator.model.get('id')} time {count}")
        if simulator.is_first_time:
            next_datetime = Measurements.create_next_timestamp(simulator)
            for pointer in range(len(simulator.measurements_definitions)):
                print(pointer)
                print(f"measurement definition: {simulator.measurements_definitions[pointer]}")
                print(f"Next datetime: {next_datetime[pointer]}")
                Measurements.generate_measurement(self=simulator, measurement_definition=simulator.measurements_definitions[pointer], next_datetime=next_datetime[pointer])
                Measurements.send_create_measurements(self=simulator, measurement_definition=simulator.measurements_definitions[pointer])
            simulator.is_first_time = False
        else:
            next_datetime = Measurements.create_next_timestamp(simulator)
            for pointer in range(len(simulator.measurements_definitions)):
                log.info(simulator.measurements_definitions[pointer].get('next_time'))
                log.info(datetime.utcnow())
                if simulator.measurements_definitions[pointer].get('next_time') <= datetime.utcnow():
                    Measurements.generate_measurement(self=simulator,
                                                      measurement_definition=simulator.measurements_definitions[pointer],
                                                      next_datetime=next_datetime[pointer])
                    Measurements.send_create_measurements(self=simulator,
                                                          measurement_definition=simulator.measurements_definitions[
                                                              pointer])
    count += 1
    simulator.tick()
    time.sleep(1)
'''
while True:
    for simulator in simulators:
        simulator.tick()
    time.sleep(1)
