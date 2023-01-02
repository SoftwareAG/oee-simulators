import time, json, os, logging
from cumulocityAPI import (C8Y_BASE, C8Y_TENANT, C8Y_USER, CumulocityAPI)
from oeeAPI import OeeAPI, ProfileCreateMode
from shiftplan import Shiftplan
from event import Event
from measurement import Measurement
from task import PeriodicTask
import interface

cumulocityAPI = CumulocityAPI()
oeeAPI = OeeAPI()

# Get Tenant Options and configure Simulator
MICROSERVICE_OPTIONS = cumulocityAPI.get_tenant_option_by_category("simulators")
PROFILE_CREATE_MODE = ProfileCreateMode[MICROSERVICE_OPTIONS.get("CREATE_PROFILES", "CREATE_IF_NOT_EXISTS")]
CREATE_PROFILES_ARGUMENTS = MICROSERVICE_OPTIONS.get("CREATE_PROFILES_ARGUMENTS", "")
CREATE_ASSET_HIERARCHY = MICROSERVICE_OPTIONS.get("CREATE_ASSET_HIERARCHY", "False")
LOG_LEVEL = MICROSERVICE_OPTIONS.get("LOG_LEVEL", "INFO")
DELETE_PROFILES = MICROSERVICE_OPTIONS.get("DELETE_PROFILES", "False")

if LOG_LEVEL == "DEBUG":
    logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.INFO)

log = logging.getLogger("sims")
log.info(f"started at {interface.current_timestamp()}")
log.debug(f'Tenant options: {MICROSERVICE_OPTIONS}')
log.info(f'CREATE_PROFILES:{PROFILE_CREATE_MODE}')

# Setting up the Array for shiftplans and time for polling interval
shiftplans = []
log.info(f'Shiftplan polling interval is set to {Shiftplan.polling_interval:,} secs')
##########################################

log.debug(C8Y_BASE)
log.debug(C8Y_TENANT)
log.debug(C8Y_USER)


class MachineSimulator:
    def __init__(self, machine: interface.MachineType) -> None:
        self.machine = machine
        if self.machine.enabled:
            self.machine.tasks = list(map(self.__create_task, self.machine.definitions))
            log.debug(f'{self.machine.definitions}')

    def __create_task(self, definition):
        min_interval_in_seconds, max_interval_in_seconds = interface.calculate_interval_in_seconds(definition)
        measurement_callback = self.machine.callback(definition, min_interval_in_seconds, max_interval_in_seconds)
        task = PeriodicTask(min_interval_in_seconds, max_interval_in_seconds, measurement_callback)
        return task

    def tick(self):
        if self.machine.should_tick():
            for task in self.machine.tasks:
                if task:
                    task.tick()


def get_or_create_device_id(device_definition):
    sim_id = device_definition.get("id")
    label = device_definition.get("model")
    device_id = cumulocityAPI.get_or_create_device(sim_id, label)
    return device_id


def load(filename):
    try:
        with open(filename) as f_obj:
            return json.load(f_obj)
    except Exception as e:
        log.error(e, type(e))
        return {}


###################################################################################
log.info(f'cwd:{os.getcwd()}')
DEVICE_MODELS = load("simulators.json")
DEVICE_EVENT_MODELS = []
DEVICE_MEASUREMENT_MODELS = []

# Add device id to the model of devices
for device_model in DEVICE_MODELS:
    device_id = get_or_create_device_id(device_model)
    device_model["device_id"] = device_id
    if device_model.get("events"):
        DEVICE_EVENT_MODELS.append(device_model)
    if device_model.get("measurements"):
        DEVICE_MEASUREMENT_MODELS.append(device_model)

# read & update Shiftplans
SHIFTPLANS_MODELS = load("shiftplans.json")
shiftplans = list(map(lambda shiftplan_model: Shiftplan(shiftplan_model), SHIFTPLANS_MODELS))

if DELETE_PROFILES.lower() == "true":
    log.debug(f'Deleting all Profiles')
    oeeAPI.delete_all_simulators_profiles()

# Create Simulator Profiles
[oeeAPI.create_and_activate_profile(id, PROFILE_CREATE_MODE) for id in oeeAPI.get_simulator_external_ids()]

os.system(f'python profile_generator.py -cat {CREATE_PROFILES_ARGUMENTS}')

if CREATE_ASSET_HIERARCHY.lower() == "true":
    log.info("Creating the OEE asset hierarchy")
    ids = []
    [ids.append(simulator.get("device_id")) for simulator in DEVICE_MODELS]
    oeeAPI.create_or_update_asset_hierachy(deviceIDs=ids)

# create list of objects for events and measurements
event_device_list = list(map(lambda model: MachineSimulator(Event(model, shiftplans)), DEVICE_EVENT_MODELS))
measurement_device_list = list(map(lambda model: MachineSimulator(Measurement(model)), DEVICE_MEASUREMENT_MODELS))
devices_list = event_device_list + measurement_device_list

while True:
    for shiftplan in shiftplans:
        shiftplan.tick()

    for device in devices_list:
        device.tick()

    time.sleep(1)
