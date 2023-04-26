import contextlib, json, logging, os, sys
import interface, time

from cumulocityAPI import C8Y_BASEURL, C8Y_TENANT, C8Y_USER, TEST_FLAG, CumulocityAPI
from datetime import datetime
from oeeAPI import OeeAPI, ProfileCreateMode
from shiftplan import Shiftplan
from event import Event
from measurement import Measurement
from task import PeriodicTask


cumulocityAPI = CumulocityAPI()
oeeAPI = OeeAPI()

# Get Tenant Options and configure Simulator
MICROSERVICE_OPTIONS = cumulocityAPI.get_tenant_option_by_category("simulators")
PROFILE_CREATE_MODE = ProfileCreateMode[MICROSERVICE_OPTIONS.get("CREATE_PROFILES", "CREATE_IF_NOT_EXISTS")]
CREATE_PROFILES_ARGUMENTS = MICROSERVICE_OPTIONS.get("CREATE_PROFILES_ARGUMENTS", "")
CREATE_ASSET_HIERARCHY = MICROSERVICE_OPTIONS.get("CREATE_ASSET_HIERARCHY", "True")
REPLACE_EXISTING_TIMESLOTS = MICROSERVICE_OPTIONS.get("REPLACE_EXISTING_TIMESLOTS", "False")
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

##########################################

log.debug(C8Y_BASEURL)
log.debug(C8Y_TENANT)
log.debug(C8Y_USER)


class MachineSimulator:
    def __init__(self, machine: interface.MachineType) -> None:
        self.machine = machine
        self.machine.shiftplans = shiftplans
        self.machine.device_id = self.machine.model.get("device_id")
        self.machine.locationId = self.machine.model.get("locationId", "")
        self.machine.enabled = self.machine.model.get('enabled', True)
        self.machine.out_of_production_time_logged = False
        self.machine.back_in_production_time_logged = False
        self.machine.id = self.machine.model.get('id')
        if self.machine.enabled:
            self.machine.tasks = list(map(self.__create_task, self.machine.definitions))
            log.debug(f'{self.machine.definitions}')

    def __create_task(self, definition):
        min_interval_in_seconds, max_interval_in_seconds = interface.calculate_interval_in_seconds(definition)
        callback = self.machine.callback(definition, min_interval_in_seconds, max_interval_in_seconds)
        task = PeriodicTask(min_interval_in_seconds, max_interval_in_seconds, callback)
        return task

    def tick(self):
        if not self.machine.enabled:
            return
        if self.should_tick():
            for task in self.machine.tasks:
                self.is_first_time(task)
                if task:
                    task.tick()

    def should_tick(self):
        if not self.is_in_production_time():
            # If machine is out of production time continuously, the log won't be generated
            if not self.machine.out_of_production_time_logged:
                self.log_not_in_shift()
                self.machine.out_of_production_time_logged = True # Checkpoint that machine is out of production time
                self.machine.back_in_production_time_logged = False
            return False
        else:
            # If machine is in of production time continuously, the log won't be generated
            if not self.machine.back_in_production_time_logged:
                self.log_back_in_shift()
                self.machine.back_in_production_time_logged = True # Checkpoint that machine is in of production time
                self.machine.out_of_production_time_logged = False
            return True

    def is_first_time(self, task):
        with contextlib.suppress(Exception):
            if self.machine.first_time:
                # set the next_run time to always let the measurement generation to run in the first time
                task.next_run = datetime.timestamp(datetime.utcnow()) + 1
                self.machine.first_time = False

    def is_in_production_time(self):
        if self.machine.locationId:
            shiftplan_status = oeeAPI.get_shiftplan_status(self.machine.locationId)

            if shiftplan_status:
                if shiftplan_status.get('status') == "PRODUCTION":
                    return True
            else:
                log.debug(f'Can not get the status of machine {self.machine.model.get("label")}, it is out of production time by default')

            return False
        return True # if there are no shiftplans for a device, the production time should not be affected by them

    def log_not_in_shift(self):
        log.info(f'Device: {self.machine.device_id} [{self.machine.model["label"]}] is not in PRODUCTION shift -> ignoring events and measurements')

    def log_back_in_shift(self):
        log.info(f'Device: {self.machine.device_id} [{self.machine.model["label"]}] is now in PRODUCTION shift -> generating events and measurements')


def get_or_create_device_id(device_model):
    sim_id = device_model.get("id")
    label = device_model.get("label")
    if not sim_id or not label:
        if not sim_id:
            log.debug("No definition info of device id")
        if not label:
            log.debug(f"No definition info of device name")
        log.info(f"Simulator device won't be created")
        return None

    device_id = cumulocityAPI.get_or_create_device(sim_id, label)
    return device_id


def load(filename):
    try:
        with open(filename) as f_obj:
            return json.load(f_obj)
    except Exception as e:
        log.error(e, type(e))
        return None


###################################################################################
if __name__ == '__main__':
    current_dir = os.getcwd()
    log.info(f'cwd:{current_dir}')

    if TEST_FLAG:
        # Change to the 'test' directory
        os.chdir("../../test")

    # read & update Shiftplans
    SHIFTPLANS_MODELS = load("shiftplans.json")
    if not SHIFTPLANS_MODELS:
        sys.exit()
    shiftplans = list(map(lambda shiftplan_model: Shiftplan(shiftplan_model, REPLACE_EXISTING_TIMESLOTS), SHIFTPLANS_MODELS))

    DEVICE_MODELS = load("simulator.json")
    if not DEVICE_MODELS:
        sys.exit()
    DEVICE_EVENT_MODELS = []
    DEVICE_MEASUREMENT_MODELS = []
    CREATED_DEVICE_IDS = []

    # Add device id to the model of devices
    for device_model in DEVICE_MODELS:
        device_model["device_id"] = get_or_create_device_id(device_model)
        if not device_model["device_id"]:
            continue
        else:
            CREATED_DEVICE_IDS.append(device_model["device_id"])
        if device_model.get("events"):
            DEVICE_EVENT_MODELS.append(device_model)
        if device_model.get("measurements"):
            DEVICE_MEASUREMENT_MODELS.append(device_model)

    if DELETE_PROFILES.lower() == "true":
        log.debug(f'Deleting all Profiles')
        oeeAPI.delete_all_simulators_profiles()

    # Get a list of simulator external IDs
    external_ids = cumulocityAPI.get_external_ids(CREATED_DEVICE_IDS)
    # Create and activate a profile for each external ID
    for id in external_ids:
        oeeAPI.create_and_activate_profile(id, PROFILE_CREATE_MODE)

    os.system(f'python profile_generator.py -cat {CREATE_PROFILES_ARGUMENTS}')

    if CREATE_ASSET_HIERARCHY.lower() == "true":
        log.info("Creating the OEE asset hierarchy")
        ids = []
        for simulator in DEVICE_MODELS:
            ids.append(simulator.get("device_id"))
        oeeAPI.create_or_update_asset_hierarchy(deviceIDs=ids)


    # create list of objects for events and measurements
    event_device_list = list(map(lambda model: MachineSimulator(Event(model)), DEVICE_EVENT_MODELS))
    measurement_device_list = list(map(lambda model: MachineSimulator(Measurement(model)), DEVICE_MEASUREMENT_MODELS))
    devices_list = event_device_list + measurement_device_list

    while True:
        for device in devices_list:
            device.tick()

        time.sleep(1)
