import time, json, os, logging, requests, base64
from datetime import datetime
from random import randint, uniform

from cumulocityAPI import C8Y_BASE, C8Y_TENANT, C8Y_USER, C8Y_PASSWORD, CumulocityAPI

VERSION = '1.0.3'

logging.basicConfig(level=logging.INFO)
logging.info(os.environ)
logging.info(f"version: {VERSION}")


# JSON-PYTHON mapping, to get json.load() working
null = None
false = False
true = True
######################

logging.info(C8Y_BASE)
logging.info(C8Y_TENANT)
logging.info(C8Y_USER)
logging.info(C8Y_PASSWORD)

def try_event(probability: float):
    ''' Returns True if event occurs.        
    '''
    return uniform(0.0, 1.0) <= probability

cumulocityAPI = CumulocityAPI()

class Task:
    def __init__(self, start_in_seconds: int, run_block) -> None:
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
        # TODO: 
        # self.__run_and_reschedule()
     
    def __calculate_next_run(self) -> int: 
        return time.time() + randint(self.min_interval_in_seconds, self.max_interval_in_seconds)
    
    def __reschedule_and_run(self):
        self.next_run = self.__calculate_next_run()
        self.run_block(self)        

    def tick(self):
        if (time.time() - self.next_run) > 0:
            self.__reschedule_and_run()                

class MachineSimulator:
    
    def __init__(self, model) -> None:
        self.model = model        
        self.device_id = None
        self.machine_up = False
        self.shutdown = False
        self.enabled = model.get('enabled', True)
        if self.enabled:
            self.tasks = list(map(self.__create_task, self.model["events"]))
        # print(f'events: {self.model["events"]}')

    def __type_fragment(self, event_definition, text = None):
        return {
            'type': event_definition["type"],
            'text': text or event_definition["type"]
        }

    def __log_ignore(self, event_definition):
        print(f'{self.device_id} is down -> ignore event {event_definition["type"]}')        

    def __on_availability_event(self, event_definition, task):             
        event = self.__type_fragment(event_definition)

        status_up_probability = event_definition.get("statusUpProbability") or 0.5
        
        if try_event(status_up_probability):
            event.update({'status': 'up'})
            self.machine_up = True
        else:
            event.update({'status': 'down'})
            self.machine_up = False

        self.__send_event(event)        

    def __on_piece_produced_event(self, event_definition, task):
        if not self.machine_up: return self.__log_ignore(event_definition)            

        event = self.__type_fragment(event_definition)
        self.__send_event(event)
        
        self.__send_following_event(event_definition)

    def __on_pieces_produced_event(self, event_definition, task):
        if not self.machine_up: return self.__log_ignore(event_definition)            

        count_min_hits = event_definition.get("countMinHits") or 0
        count_max_hits = event_definition.get("countMaxHits") or 10

        event = self.__type_fragment(event_definition)
        event.update({"count": randint(count_min_hits, count_max_hits)})

        self.__send_event(event)

        self.__send_following_event(event_definition)
        
    
    def __on_piece_ok_event(self, event_definition, task):
        if not self.machine_up: return self.__log_ignore(event_definition)            

        event = self.__type_fragment(event_definition)
        self.__send_event(event)
    
    def __on_pieces_ok_event(self, event_definition, task):
        if not self.machine_up: return self.__log_ignore(event_definition)            

        event = self.__type_fragment(event_definition)

        count_min_hits = event_definition.get("countMinHits") or 0
        count_max_hits = event_definition.get("countMaxHits") or 10
        event.update({"count": randint(count_min_hits, count_max_hits)})
        self.__send_event(event)

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
        self.shutdown = True

        min_duration = event_definition.get("minDuration") or 0
        max_duration = event_definition.get("maxDuration") or 5
        duration = int(uniform(min_duration, max_duration) * 60)
        logging.info(f'shutdown {self.device_id} for the next {duration} seconds.')
        task = self.create_one_time_task({}, duration, MachineSimulator.__on_machine_up_event)
        self.tasks.append(task)
        
    def __on_machine_up_event(self, event_definition, task):
        self.shutdown = False
        logging.info(f'Device({self.device_id}) is up now.')

    def __send_following_event(self, event_definition):        
        if "followedBy" in event_definition:
            followed_by_definition = event_definition["followedBy"]
            followed_by_hits = followed_by_definition["hits"]
            this_hits = event_definition["hits"]

            # should followedBy event be sent?
            if try_event(followed_by_hits / this_hits):
                followed_by_task = self.create_one_time_task(followed_by_definition)
                self.tasks.append(followed_by_task)                
                logging.debug(f'{self.device_id} task({id(followed_by_task)}) added: {json.dumps(followed_by_definition)}, tasks: {len(self.tasks)}')      
            else:
                  logging.debug(f'{self.device_id} followedBy task missed. probability = {1 - followed_by_hits / this_hits} , def: {json.dumps(followed_by_definition)}')         

    def create_one_time_task(self, event_definition, duration = 2, event_callback = None):
        callback = event_callback or MachineSimulator.event_mapping[event_definition["type"]]
        task = Task(duration, lambda task: {self.__execute_callback_and_remove_task(callback, event_definition, task)})
        return task        
        
    def __execute_callback_and_remove_task(self, callback, event_definition, task):
        callback(self, event_definition, task)
        if task in self.tasks:
            self.tasks.remove(task)
            logging.debug(f'{self.device_id} task({id(task)}) removed: {json.dumps(event_definition)}, tasks: {len(self.tasks)}')        
    
    def tick(self):
        if not self.enabled: return

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
        min_hits_per_hour = event_definition.get("minHits", event_definition.get("hits"))
        max_hits_per_hour = event_definition.get("maxHits", event_definition.get("hits"))

        min_interval_in_seconds = int(3600 / max_hits_per_hour)
        max_interval_in_seconds = int(3600 / min_hits_per_hour)

        event_callback = lambda task:  {MachineSimulator.event_mapping[event_definition["type"]](self, event_definition, task)}

        task = PeriodicTask(min_interval_in_seconds, max_interval_in_seconds, event_callback)
        
        logging.debug(f'create periodic task for {event_definition["type"]} ({min_hits_per_hour}, {max_hits_per_hour})')        
        # event_callback()
        return task
    
    def __send_event(self, event_fragment):
        base_event = {
            'source': {
                'id': self.device_id
            },
            'time': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        }
        base_event.update(event_fragment)

        if self.shutdown:
            logging.info(f'{self.model["id"]} is down -> ignore event: {json.dumps(base_event)}')
        else:
            cumulocityAPI.send_event(base_event)

def load(filename):
    try:
        with open(filename) as f_obj:
            return json.load(f_obj)
    except Exception as e:
        print(e, type(e))
        return {}
    
SIMULATOR_MODELS = load("simulators.json")

simulators = list(map(lambda model: MachineSimulator(model), SIMULATOR_MODELS))

# create managed object for every simulator
[item.get_or_create_device_id() for item in simulators]

while True:
    for simulator in simulators:
        simulator.tick()        
    time.sleep(1)