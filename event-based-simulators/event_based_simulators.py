import time, json, os, logging, requests, base64
from datetime import datetime
from random import randint, uniform

logging.basicConfig(level=logging.INFO)
logging.info(os.environ)

'''
Start configuration
'''

C8Y_BASE = os.environ.get('C8Y_BASEURL')
C8Y_TENANT = os.environ.get('C8Y_TENANT')
C8Y_USER = os.environ.get('C8Y_USER')
C8Y_PASSWORD = os.environ.get('C8Y_PASSWORD')

MOCK_RUEQUESTS = os.environ.get('MOCK_C8Y_REQUESTS') or 'false'

user_and_pass_bytes = base64.b64encode((C8Y_TENANT + "/" + C8Y_USER + ':' + C8Y_PASSWORD).encode('ascii')) # bytes
user_and_pass = user_and_pass_bytes.decode('ascii') # decode to str 

C8Y_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Basic ' + user_and_pass
}

'''
End configuration
'''

logging.info(C8Y_BASE)
logging.info(C8Y_TENANT)
logging.info(C8Y_USER)
logging.info(C8Y_PASSWORD)


C8Y_SIMULATORS_GROUP = "c8y_EventBasedSimulators"

def try_event(probability: float):
    ''' Returns True if event occurs.        
    '''
    return uniform(0.0, 1.0) <= probability

class CumulocityAPI:
    def __init__(self) -> None:
        self.mocking = MOCK_RUEQUESTS.lower() == 'true'

    def send_event(self, event):
        if self.mocking:
            print("mock: send event ", json.dumps(event), ' to ', C8Y_BASE + '/event/events')
            return json.dumps({'response': 200})
        else:
            response = requests.post(C8Y_BASE + '/event/events', headers=C8Y_HEADERS, data=json.dumps(event))
            if not response.ok():
                logging.warning(f'response status code is not ok: {response}')
            return response.json()

    def get_or_create_device(self, sim_id, label):
        if self.mocking:
            print("mock: get or create device with external id", sim_id)
            return sim_id
        
        # Check if device already created
        return self.__get_device(sim_id) or self.__create_device(sim_id, label)
                
    def __get_device(self, sim_id):
        response = requests.get(f'{C8Y_BASE}/identity/externalIds/{C8Y_SIMULATORS_GROUP}/{sim_id}', headers=C8Y_HEADERS)
        if response.ok():
            device_id = response.json()['managedObject']['id']
            logging.info(f'Device({device_id}) for the simulator({sim_id}) found.')
            return device_id        
        return None
    
    def __create_device(self, sim_id, label):
        logging.info("create device...")
        device = {
            'name': label,
            'c8y_IsDevice': {}
        }
        response = requests.post(C8Y_BASE + '/inventory/managedObjects', headers=C8Y_HEADERS, data=json.dumps(device))
        device_id = response.json()['id']
        logging.info(device_id)

        external_id = {
            'type': C8Y_SIMULATORS_GROUP,
            'externalId': sim_id
        }
        response = requests.post(C8Y_BASE + '/identity/globalIds/' + device_id + '/externalIds', headers=C8Y_HEADERS, data=json.dumps(external_id))
        logging.info(response)
        return device_id


cumulocityAPI = CumulocityAPI()
class Task:
    def __init__(self, start_in_seconds, run_block) -> None:
        self.run_block = run_block
        self.next_run = time.time() + start_in_seconds
    
    def tick(self):
        if (time.time() - self.next_run) > 0:
            self.run_block(self)

class PeriodicTask:
    def __init__(self, minInterval, maxInterval, run_block) -> None:
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

        status_up_probability = event_definition["statusUpProbability"] or 0.5
        
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

        count_min_hits = event_definition["countMinHits"] or 0
        count_max_hits = event_definition["countMaxHits"] or 10

        event = self.__type_fragment(event_definition)
        event.update({"count": randint(count_min_hits, count_max_hits)})

        self.__send_event(event)

        self.__send_following_event(event_definition)
        
    
    def __on_piece_ok_event(self, event_definition, task):
        if not self.machine_up: return self.__log_ignore(event_definition)            

        event = self.__type_fragment(event_definition)
        self.__send_event(event)

    def __on_piece_quality_event(self, event_definition, task):
        if not self.machine_up: return self.__log_ignore(event_definition)            

        event = self.__type_fragment(event_definition)

        status_ok_probability = event_definition["statusOkProbability"] or 0.5
        if try_event(status_ok_probability):
            event.update({"status": "ok"})
        else:
            event.update({"status": "nok"})

        self.__send_event(event)

    def __send_following_event(self, event_definition):        
        if "followedBy" in event_definition:
            followed_by_definition = event_definition["followedBy"]
            followed_by_hits = followed_by_definition["hits"]
            this_hits = event_definition["hits"]

            # should followedBy event be sent?
            if try_event(followed_by_hits / this_hits):
                followed_by_task = self.create_one_time_task(followed_by_definition)
                self.tasks.append(followed_by_task)                


    def create_one_time_task(self, event_definition):
        event_callback = MachineSimulator.event_mapping[event_definition["type"]]
        task = Task(2, lambda task: {self.__execute_callback_and_remove_task(event_callback, event_definition, task)})
        return task        
        
    def __execute_callback_and_remove_task(self, callback, event_definition, task):
        callback(self, event_definition, task)
        if task in self.tasks:
            self.tasks.remove(task)        
    
    def tick(self):
        # print("tick " + self.model["id"])
        for task in self.tasks:
            task.tick()

    def get_or_create_device_id(self):        
        # TODO: get or create device id
        sim_id = self.model['id']
        label = self.model['label']
        self.device_id = cumulocityAPI.get_or_create_device(sim_id, label)

    event_mapping = {'Availability': __on_availability_event,
                     'Piece_Produced': __on_piece_produced_event,
                     'Pieces_Produced': __on_pieces_produced_event,
                     'Piece_Ok': __on_piece_ok_event,
                     'Piece_Quality': __on_piece_quality_event }

    def __create_task(self, event_definition):
        min_hits_per_hour = event_definition.get("minHits", event_definition.get("hits"))
        max_hits_per_hour = event_definition.get("maxHits", event_definition.get("hits"))

        min_interval_in_seconds = 3600 / max_hits_per_hour
        max_interval_in_seconds = 3600 / min_hits_per_hour

        event_callback = lambda task:  {MachineSimulator.event_mapping[event_definition["type"]](self, event_definition, task)}

        task = PeriodicTask(min_interval_in_seconds, max_interval_in_seconds, event_callback)
        
        print(f'create periodic task for {event_definition["type"]} ({min_hits_per_hour}, {max_hits_per_hour})')        
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
