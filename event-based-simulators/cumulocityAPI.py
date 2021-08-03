import time, json, os, logging, requests, base64
from datetime import datetime
from random import randint, uniform

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


# JSON-PYTHON mapping, to get json.load() working
null = None
false = False
true = True
######################


C8Y_SIMULATORS_GROUP = "c8y_EventBasedSimulators"

OEE_DATA_MODEL_FIELD_NAME = "@com_adamos_oee_datamodel_MachineOEEConfiguration"


__counter = 0
def global_counter():
    __counter = __counter + 1
    return __counter

class CumulocityAPI:
    def __init__(self) -> None:
        self.mocking = MOCK_RUEQUESTS.lower() == 'true'

    def send_event(self, event):
        if self.mocking:
            print("mock: send event ", json.dumps(event), ' to ', C8Y_BASE + '/event/events')
            return json.dumps({'response': 200})
        else:
            response = requests.post(C8Y_BASE + '/event/events', headers=C8Y_HEADERS, data=json.dumps(event))
            if not response.ok:
                logging.warning(f'response status code is not ok: {response}')
            return response.json()

    def get_or_create_device(self, sim_id, label):
        if self.mocking:
            print("mock: get or create device with external id", sim_id)
            return sim_id
        
        # Check if device already created
        return self.__get_device(sim_id) or self.__create_device(sim_id, label)

    def count_profiles(self, device_id):
        if self.mocking:
            print(f'mock: count_profiles(${device_id})')
            return 10
        request_query = f'{C8Y_BASE}/inventory/managedObjects/count?type=OEECalculationProfile&text={device_id}'
        response = requests.get(request_query, headers=C8Y_HEADERS)
        if response.ok:
            try:
                return int(response.text)
            except Exception as e:
                logging.warn(f'cannot convert "${response.text}" to number. exception: {e}')
                return 0
        else:
            logging.warning("bad response:" + response)
            return 0
    
    def create_managed_object(self, fragment: str):
        if self.mocking:
            print(f'mock: create_managed_object()')
            return {'id': '0'}
        response = requests.post(C8Y_BASE + '/inventory/managedObjects', headers=C8Y_HEADERS, data=fragment)
        if response.ok:
            return response.json
        logging.warning(f'cannot create managed object. response:{response}')
        #TODO: check for errors
        return {}

    def update_managed_object(self, device_id, fragment):
        if self.mocking:
            print(f'mock: update_managed_object()')
            return {'id': '0'}

        response = requests.put(f'{C8Y_BASE}/inventory/managedObjects/{device_id}', headers=C8Y_HEADERS, data=fragment)
        if response.ok:
            return response.json()
        logging.warning(f'cannot update managed object. response:{response}')
        return {}

    def __get_device(self, sim_id):
        response = requests.get(f'{C8Y_BASE}/identity/externalIds/{C8Y_SIMULATORS_GROUP}/{sim_id}', headers=C8Y_HEADERS)
        if response.ok:
            device_id = response.json()['managedObject']['id']
            logging.info(f' Device({device_id}) has been found by its external id "{C8Y_SIMULATORS_GROUP}/{sim_id}".')
            return device_id        
        return None
    
    def __create_device(self, sim_id, label):
        logging.info(f'Creating a new device with following external id "{C8Y_SIMULATORS_GROUP}/{sim_id}"')
        device = {
            'name': label,
            'c8y_IsDevice': {}
        }
        response = self.create_managed_object(json.dumps(device))
        device_id = response.json()['id']
        logging.info(device_id)

        external_id = {
            'type': C8Y_SIMULATORS_GROUP,
            'externalId': sim_id
        }
        response = requests.post(C8Y_BASE + '/identity/globalIds/' + device_id + '/externalIds', headers=C8Y_HEADERS, data=json.dumps(external_id))
        logging.info(response)
        return device_id


print(C8Y_BASE)



def to_variable(name: str):
    return '${' + name + '}'

def substitute(template: str, replacers: dict):
    result = template
    for key in replacers:
        result = result.replace(to_variable(key), replacers[key])
    return result

template = open('sim_001_profile.template', 'r').read()
replacers = {
    'deviceId': '131356012',
    'tenantId': 't7690037',
    'profileId': '134999993',
    'counter': '100'
}

cumulocityAPI = CumulocityAPI()

print(f'test c8y API. {cumulocityAPI.count_profiles(21839972)}')


profileTemplate = {
    'name': 'Generated Profile 1',
    'type': 'OEECalculationProfile'
}


# profile = cumulocityAPI.update_managed_object('134999993', substitute(template, replacers))
profile = cumulocityAPI.update_managed_object('131356012', json.dumps({'@com_adamos_oee_datamodel_MachineOEEConfiguration': {}}))

# profile = cumulocityAPI.create_managed_object(json.dumps(profileTemplate))

print(json.dumps(profile))