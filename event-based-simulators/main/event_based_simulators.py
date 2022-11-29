import time, json, os, logging
from datetime import datetime, timedelta
from random import randint, uniform, choices

from cumulocityAPI import C8Y_BASE, C8Y_TENANT, C8Y_USER, C8Y_PASSWORD, CumulocityAPI
from oeeAPI import OeeAPI, ProfileCreateMode

def current_timestamp(format = "%Y-%m-%dT%H:%M:%S.%f"):
    return datetime.utcnow().strftime(format)[:-3] + 'Z'

cumulocityAPI = CumulocityAPI()
oeeAPI = OeeAPI()

#TODO: Parameter to delete all Profiles
#Get Tenant Options and configure Simulator
microservice_options = cumulocityAPI.get_tenant_option_by_category("event-based-simulators")
PROFILE_CREATE_MODE = ProfileCreateMode[microservice_options.get("CREATE_PROFILES", "CREATE_IF_NOT_EXISTS")]
CREATE_PROFILES_ARGUMENTS = microservice_options.get("CREATE_PROFILES_ARGUMENTS", "")
CREATE_ASSET_HIERACHY = microservice_options.get("CREATE_ASSET_HIERACHY", "False")
LOG_LEVEL = microservice_options.get("LOG_LEVEL", "INFO")
DELETE_PROFILES = microservice_options.get("DELETE_PROFILES", "False")
if LOG_LEVEL == "DEBUG":
    logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.INFO)
##########################################

log = logging.getLogger("sims")
log.info(f"started at {current_timestamp()}")
log.debug(f'Tenant options: {microservice_options}')
log.info(f'CREATE_PROFILES:{PROFILE_CREATE_MODE}')


#Setting up the Array for shiftplans and time for polling interval
shiftplans = []
one_day = 86400 
shiftplan_polling_interval = one_day
log.info(f'Shiftplan polling interval is set to {shiftplan_polling_interval:,} secs')
shiftplan_dateformat='%Y-%m-%dT%H:%M:%SZ'
##########################################

log.debug(C8Y_BASE)
log.debug(C8Y_TENANT)
log.debug(C8Y_USER)

def try_event(probability: float):
    ''' Returns True if event occurs.        
    '''
    return uniform(0.0, 1.0) <= probability

def get_random_status(statusses, durations, probabilites):
    '''returns a random status and duration of the given lists of status, durations and probabilites.    
    '''
    if len(statusses) != len(probabilites) or len(durations) != len(probabilites):
        log.info(
            "Length of statusses, duration and probabilites does not match. Set status to up")
        return "up", 0
    choice = choices([i for i in range(len(probabilites))], probabilites)[0]
    return statusses[choice], durations[choice]

class Task:
    def __init__(self, start_in_seconds: int, run_block) -> None:
        self.extra = {}
        self.run_block = run_block
        self.next_run = time.time() + start_in_seconds
    
    def tick(self):
        if (time.time() - self.next_run) > 0:
            self.run_block(self)

class PeriodicTask:
    def __init__(self, minInterval: int, maxInterval: int, run_block) -> None:
        self.run_block = run_block
        self.min_interval_in_seconds = minInterval
        self.max_interval_in_seconds = maxInterval
        self.next_run = self.__calculate_next_run()
     
    def __calculate_next_run(self) -> int: 
        return time.time() + randint(self.min_interval_in_seconds, self.max_interval_in_seconds)
    
    def __reschedule_and_run(self):
        duration = self.run_block(self)
        duration = duration.pop() or 0  # Why is duration a set?
        self.next_run = self.__calculate_next_run() + duration
        log.debug(f"Reschedule next run and wait for additional {duration} seconds. Next run is at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.next_run))}")

    def tick(self):
        if (time.time() - self.next_run) > 0:
            self.__reschedule_and_run()    

class Shiftplan:
    def __init__(self, shiftplan_model) -> None:
        self.locationId = ""
        self.recurringTimeSlots = []
        self.set_timeslots_for_shiftplan(shiftplan_model)
        self.add_Shiftplan_to_OEE()
        self.task = self.__create_task()

    def set_timeslots_for_shiftplan(self, shiftplan):
        self.locationId = shiftplan["locationId"]
        self.recurringTimeSlots = shiftplan["recurringTimeslots"]

    def add_Shiftplan_to_OEE(self):
        oeeAPI.add_timeslots_for_shiftplan(self)
        log.info(f'Added shiftplan to OEE for location: {self.locationId}')

    def __create_task(self):
        task_callback = lambda:  {self.fetchNewShiftplan()}
        task = PeriodicTask(shiftplan_polling_interval, shiftplan_polling_interval, task_callback)
        log.debug(f'Create periodic task for pulling shiftplans - location {self.locationId} - running every {shiftplan_polling_interval}')
        return task

    def fetchNewShiftplan(self):
        log.debug(f'Getting Shiftplan for location: {self.locationId}')
        self.setShiftplan(oeeAPI.get_shiftplan(self.locationId, f'{datetime.utcnow():{shiftplan_dateformat}}', f'{datetime.utcnow() + timedelta(seconds=shiftplan_polling_interval):{shiftplan_dateformat}}'))

    def setShiftplan(self, shiftplan):
        log.info(f'Setting Shiftplan for location: {self.locationId}')
        self.recurringTimeSlots = shiftplan.get('recurringTimeSlots', [])

    def tick(self):
        self.task.tick()

    class RecurringTimeSlot:
        def __init__(self, recurringTimeSlotModel):
            self.id = recurringTimeSlotModel.get("id")
            self.seriesPostfix = recurringTimeSlotModel.get("seriesPostfix")
            self.slotType = recurringTimeSlotModel.get("slotType")
            self.slotStart = recurringTimeSlotModel.get("slotStart")
            self.slotEnd = recurringTimeSlotModel.get("slotEnd")
            self.description = recurringTimeSlotModel.get("description")
            self.active = recurringTimeSlotModel.get("active")
            self.slotRecurrence = self.SlotRecurrence(recurringTimeSlotModel.get("slotRecurrence"))
        
        class SlotRecurrence:
            def __init__(self, slotRecurrence):
                self.weekdays = slotRecurrence.get("weekdays")
            

class MachineSimulator:
    
    def __init__(self, model) -> None:
        self.model = model        
        self.device_id = None
        self.locationId = model.get("locationId", "")
        self.machine_up = False
        self.shutdown = False
        self.enabled = model.get('enabled', True)
        self.production_time_s = 0.0
        self.last_production_time_update = time.time()
        self.out_of_production_time_logged = False
        if self.enabled:
            self.tasks = list(map(self.__create_task, self.model["events"]))
            self.production_speed_s = self.__get_production_speed_s(self.model["events"])
            log.debug(f'events: {self.model["events"]}')

    def __get_production_speed_s(self, events) -> float:
        """Returns pieces/s""" 
        for event_definition in events:
            event_type = event_definition.get("type") or ""
            if event_type == "Piece_Produced":
                frequency = event_definition.get("frequency")
                return frequency / 3600.0
            if event_type == "Pieces_Produced":
                frequency = event_definition.get("frequency")
                countMaximumFrequency = event_definition.get("countMaximumFrequency")
                return frequency * countMaximumFrequency / 3600.0

        return 0.0

    def __produce_pieces(self):
        production_time = time.time() - self.last_production_time_update
        self.last_production_time_update = time.time()
        if self.machine_up and not self.shutdown:
            self.production_time_s = self.production_time_s + production_time
            log.debug(f'{self.device_id} production time: {self.production_time_s}s')

    def __pick_one_piece(self, pieces_per_seconds: float):
        piece_production_time = 1.0 / pieces_per_seconds
        if (self.production_time_s > piece_production_time):
            self.production_time_s = self.production_time_s - piece_production_time
            log.debug(f'{self.device_id} one piece produced, remained time: {self.production_time_s}s')
            return True
        log.debug(f'{self.device_id} piece not yet produced, production time: {self.production_time_s}s')
        return False
    
    def __pick_pieces(self, pieces_per_seconds: float):
        pieces_produced = int(pieces_per_seconds * self.production_time_s)
        self.production_time_s = self.production_time_s - pieces_produced / pieces_per_seconds
        log.debug(f'{self.device_id} pieces produced: {pieces_produced}, remained time: {self.production_time_s}s')
        return pieces_produced

    def __type_fragment(self, event_definition, text = None):
        return {
            'type': event_definition["type"],
            'text': text or event_definition["type"]
        }

    def __log_ignore(self, event_definition):
        log.info(f'Device: {self.device_id} [{self.model["label"]}] is down -> ignore event {event_definition["type"]}')

    def __log_not_in_shift(self):
        log.info(f'Device: {self.device_id} [{self.model["label"]}] is not in PRODUCTION shift -> ignore event')

    def __on_availability_event(self, event_definition, task):         
        
        self.__produce_pieces()

        event = self.__type_fragment(event_definition)

        statusses = event_definition.get("status") or ["up"]
        probabilities = event_definition.get("probabilities") or [0.5]
        durations = event_definition.get("durations") or [0]
        status, duration = get_random_status(
            statusses, durations, probabilities)
        self.machine_up = (status == "up")
        event.update({'status': status})

        event.update(self.__get_production_info())
        self.__send_event(event)

        # Send Piece_Produced as soon as possible(to get OEE calculation quicker for Slow Producers)
        # Might make sense to configure the behavior per simulator in json.
        if self.__is_whole_piece_available():
            self.__force_production_event()

        return duration

    def __force_production_event(self):
        for event_definition in self.model["events"]:
            event_type = event_definition.get("type")
            if event_type == "Piece_Produced":
                task = self.create_one_time_task(event_definition)
                self.tasks.append(task)


    def __get_production_info(self):
        return {
            'production_time_s': self.production_time_s,
            'production_speed_h': self.production_speed_s * 3600.0,
            'pieces_produced': self.production_speed_s * self.production_time_s
        }

    def __on_piece_produced_event(self, event_definition, task):
        if not self.machine_up: return self.__log_ignore(event_definition) 

        self.__produce_pieces()
        
        pieces_per_hour = event_definition.get("frequency") or 1

        if self.__pick_one_piece(pieces_per_hour / 3600.0):
            event = self.__type_fragment(event_definition)
            event.update(self.__get_production_info())
            timestamp = self.__send_event(event)            
            self.__send_following_event(event_definition, timestamp)

        if self.__is_whole_piece_available():
            # send piece_produced again.
            next_task = self.create_one_time_task(event_definition)
            self.tasks.append(next_task)               

    def __is_whole_piece_available(self):
        return int(self.production_time_s * self.production_speed_s) >= 1

    def __on_pieces_produced_event(self, event_definition, task):
        if not self.machine_up: return self.__log_ignore(event_definition)

        self.__produce_pieces()           

        countMaximumFrequency = event_definition.get("countMaximumFrequency") or 10

        frequency = event_definition.get("frequency") or 1

        event = self.__type_fragment(event_definition)
        pieces_produced = self.__pick_pieces(frequency * countMaximumFrequency / 3600.0)
        event.update({"count": pieces_produced})
        event.update(self.__get_production_info())

        timestamp = self.__send_event(event)
        if timestamp and pieces_produced > 0:
            extra_params = {"pieces_produced": pieces_produced}
            self.__send_following_event(event_definition, timestamp, extra_params)
        
    
    def __on_piece_ok_event(self, event_definition, task):
        event = self.__type_fragment(event_definition)

        piece_produced_timestamp = None
        if hasattr(task, 'extra'):
            piece_produced_timestamp = task.extra["timestamp"]

        self.__send_event(event, piece_produced_timestamp)
    
    def __on_pieces_ok_event(self, event_definition, task):
        event = self.__type_fragment(event_definition)

        countMinimumFrequency = event_definition.get("countMinimumFrequency") or 0
        countMaximumFrequency = event_definition.get("countMaximumFrequency") or 10

        piece_produced_timestamp = None
        if hasattr(task, 'extra'):
            piece_produced_timestamp = task.extra["timestamp"]
            countMaximumFrequency = task.extra.get("pieces_produced") or countMaximumFrequency

        event.update({"count": randint(min(countMinimumFrequency, countMaximumFrequency), countMaximumFrequency)})

        self.__send_event(event, piece_produced_timestamp)

    def __on_piece_quality_event(self, event_definition, task):
        if not self.machine_up: return self.__log_ignore(event_definition)            

        event = self.__type_fragment(event_definition)

        status_ok_probability = event_definition.get("statusOkProbability") or 0.5
        if try_event(status_ok_probability):
            event.update({"status": "ok"})
        else:
            event.update({"status": "nok"})

        self.__send_event(event)

    def __on_shutdown_event(self, event_definition, task):
        self.__produce_pieces()
        self.shutdown = True

        min_duration = event_definition.get("minDuration") or 0
        max_duration = event_definition.get("maxDuration") or 5
        duration = int(uniform(min_duration, max_duration) * 60)
        log.info(f'shutdown {self.device_id} for the next {duration} seconds.')
        task = self.create_one_time_task({}, duration, MachineSimulator.__on_machine_up_event)
        self.tasks.append(task)
        
    def __on_machine_up_event(self, event_definition, task):
        self.__produce_pieces()
        self.shutdown = False
        log.info(f'Device({self.device_id}) is up now.')

    def __send_following_event(self, event_definition, timestamp = None, extra_params = {}):        
        if "followedBy" in event_definition:
            followed_by_definition = event_definition["followedBy"]
            followed_by_frequency = followed_by_definition["frequency"]
            this_frequency = event_definition["frequency"]

            # should followedBy event be sent?
            if try_event(followed_by_frequency / this_frequency):
                followed_by_task = self.create_one_time_task(followed_by_definition)
                followed_by_task.extra["timestamp"] = timestamp
                followed_by_task.extra.update(extra_params)
                self.tasks.append(followed_by_task)                
                log.debug(f'{self.device_id} task({id(followed_by_task)}) added: {json.dumps(followed_by_definition)}, tasks: {len(self.tasks)}')      
            else:
                  log.debug(f'{self.device_id} followedBy task missed. probability = {1 - followed_by_frequency / this_frequency} , def: {json.dumps(followed_by_definition)}')         

    def create_one_time_task(self, event_definition, start_in_seconds = 2, event_callback = None):
        callback = event_callback or MachineSimulator.event_mapping[event_definition["type"]]
        task = Task(start_in_seconds, lambda task: {self.__execute_callback_and_remove_task(callback, event_definition, task)})
        return task        
        
    def __execute_callback_and_remove_task(self, callback, event_definition, task):
        callback(self, event_definition, task)
        if task in self.tasks:
            self.tasks.remove(task)
            log.debug(f'{self.device_id} task({id(task)}) removed: {json.dumps(event_definition)}, tasks: {len(self.tasks)}')        
    
    def tick(self):
        if not self.enabled: return
        if not self.is_in_productionTime():
            if not self.out_of_production_time_logged:
                self.__log_not_in_shift()
            self.out_of_production_time_logged = True
            return
        else:
            self.out_of_production_time_logged = False
        for task in self.tasks:
            task.tick()

    def get_or_create_device_id(self):        
        sim_id = self.model['id']
        label = self.model['label']
        self.device_id = cumulocityAPI.get_or_create_device(sim_id, label)

    event_mapping = {'Availability': __on_availability_event,
                     'Piece_Produced': __on_piece_produced_event,
                     'Pieces_Produced': __on_pieces_produced_event,
                     'Piece_Ok': __on_piece_ok_event,
                     'Pieces_Ok': __on_pieces_ok_event,
                     'Piece_Quality': __on_piece_quality_event,
                     'Shutdown': __on_shutdown_event}

    def __create_task(self, event_definition):
        min_frequency_per_hour = event_definition.get("minimumFrequency", event_definition.get("frequency"))
        max_frequency_per_hour = event_definition.get("maximumFrequency", event_definition.get("frequency"))

        min_interval_in_seconds = int(3600 / max_frequency_per_hour)
        max_interval_in_seconds = int(3600 / min_frequency_per_hour)

        event_callback = lambda task:  {MachineSimulator.event_mapping[event_definition["type"]](self, event_definition, task)}

        task = PeriodicTask(min_interval_in_seconds, max_interval_in_seconds, event_callback)
        
        log.debug(f'create periodic task for {event_definition["type"]} ({min_frequency_per_hour}, {max_frequency_per_hour})')        
        # event_callback()
        return task
    
    def __send_event(self, event_fragment, timestamp = None):
        newTimestamp = timestamp or current_timestamp()
        base_event = {
            'source': {
                'id': self.device_id
            },
            'time': newTimestamp
        }
        base_event.update(event_fragment)

        if self.shutdown:
            log.info(f'{self.model["id"]} is down -> ignore event: {json.dumps(base_event)}')
            return None
        else:
            cumulocityAPI.send_event(base_event)
            return newTimestamp

    def is_in_productionTime(self):
        #if there are no shiftplans for a device, it should not be affected by production-time
        has_no_shiftplan = True
        for shiftplan in shiftplans:
            if shiftplan.locationId == self.locationId:
                has_no_shiftplan = False
                for timeslot in shiftplan.recurringTimeSlots:
                    if timeslot.slotType == "PRODUCTION":
                        now = datetime.utcnow()
                        start = datetime.strptime(timeslot.slotStart, shiftplan_dateformat)
                        end = datetime.strptime(timeslot.slotEnd, shiftplan_dateformat)
                        if start < now and end > now:
                            return True
        return has_no_shiftplan


def load(filename):
    try:
        with open(filename) as f_obj:
            return json.load(f_obj)
    except Exception as e:
        log.error(e, type(e))
        return {}

    
log.info(f'cwd:{os.getcwd()}')
SIMULATOR_MODELS = load("simulators.json")

simulators = list(map(lambda model: MachineSimulator(model), SIMULATOR_MODELS))


# create managed object for every simulator
[item.get_or_create_device_id() for item in simulators]


#read & update Shiftplans
SHIFTPLANS_MODELS = load("shiftplans.json")
shiftplans = list(map(lambda model: Shiftplan(model), SHIFTPLANS_MODELS))

if DELETE_PROFILES.lower() == "true":
    log.debug(f'Deleting all Profiles')
    oeeAPI.delete_all_simulators_profiles()

if PROFILE_CREATE_MODE:    
    [oeeAPI.create_and_activate_profile(id, PROFILE_CREATE_MODE) 
        for id in oeeAPI.get_simulator_external_ids()]

    os.system(f'python profile_generator.py -cat {CREATE_PROFILES_ARGUMENTS}')

if CREATE_ASSET_HIERACHY.lower() == "true":
    log.info("Creating the OEE asset hierachy")
    ids = []
    [ids.append(simulator.device_id) for simulator in simulators]
    oeeAPI.create_or_update_asset_hierachy(deviceIDs=ids)


while True:
    for shiftplan in shiftplans:
        shiftplan.tick()

    for simulator in simulators:
        simulator.tick()
    time.sleep(1)
