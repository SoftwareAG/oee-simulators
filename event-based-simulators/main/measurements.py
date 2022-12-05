import sys
import json, os, logging, requests, base64
from datetime import datetime, timedelta, time
from random import randint, uniform, choices, gauss
from cumulocityAPI import CumulocityAPI
from oeeAPI import OeeAPI
import logging
from event_based_simulators import MachineSimulator

log = logging.getLogger("measurements")

cumulocityAPI = CumulocityAPI()
oeeAPI = OeeAPI()

class Measurements:

    def __init__(self, start_time, model) -> None:
        self.model = model
        self.device_id = None
        self.enabled = model.get('enabled', True)
        self.start = start_time
        self.simulated_data = []
        self.measurements = self.model["measurements"]


    def send_create_measurements(self, timestamp, measurements):
        log.info('Create measurements')
        for i in range(len(measurements)):
            measurements[i]['time'] = timestamp
            measurements[i]['source']['id'] = id
        measurements_object = {
            "measurements": measurements
        }
        cumulocityAPI.create_measurements(measurements=measurements_object)
        log.info("Measurements import finished")


    def generate_measurement(self, measurement_definition, task, timestamp):
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
            mu = measurement_definition["mu"]
            sigma = measurement_definition["sigma"]
            value = round(gauss(mu, sigma), 2)
        self.simulated_data.append({
            'type': measurement_definition["type"],
            'series': measurement_definition["series"],
            'value': value,
            'unit': measurement_definition["unit"],
            'time': timestamp
        })


    def calculate_next_timestamp(self, minFrequency, maxFrequency):
        model = load("simulators.json")
        min_per_hour = measurement_definition.get("minimumFrequency", measurement_definition.get("frequency"))
        max_per_hour = measurement_definition.get("maximumFrequency", measurement_definition.get("frequency"))

        min_interval_in_seconds = int(3600 / min_per_hour)
        max_interval_in_seconds = int(3600 / max_per_hour)


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
log.info(simulators)
log.info("FINISH")