import time, json, os, logging, requests, base64
from datetime import datetime
from random import randint, uniform

C8Y_BASE = os.environ.get('C8Y_BASEURL') or 'http://localhost:8080'
C8Y_TENANT = os.environ.get('C8Y_TENANT') or 't100'
C8Y_USER = os.environ.get('C8Y_USER') or 'test'
C8Y_PASSWORD = os.environ.get('C8Y_PASSWORD') or 'test'

MOCK_REQUESTS = os.environ.get('MOCK_C8Y_REQUESTS') or 'false'

user_and_pass_bytes = base64.b64encode((C8Y_TENANT + "/" + C8Y_USER + ':' + C8Y_PASSWORD).encode('ascii')) # bytes
user_and_pass = user_and_pass_bytes.decode('ascii') # decode to str 

C8Y_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Basic ' + user_and_pass
}

# JSON-PYTHON mapping, to get json.load() working
null = None
false = False
true = True
######################
log = logging.getLogger("C8yAPI")

OEE_DATA_MODEL_FIELD_NAME = "@com_adamos_oee_datamodel_MachineOEEConfiguration"

class CumulocityAPI:

    C8Y_SIMULATORS_GROUP = "c8y_EventBasedSimulator"
    OEE_CALCULATION_PROFILE_TYPE = "OEECalculationProfile"
    OEE_CALUCLATION_CATEGORY = "OEECategoryConfiguration"

    def __init__(self) -> None:
        self.mocking = MOCK_REQUESTS.lower() == 'true'
        log.info(f'MOCK_REQUESTS: {self.mocking}')

    def send_event(self, event):
        if self.mocking:
            log.info(f"mock: send event {json.dumps(event)} to {C8Y_BASE}/event/events")
            return json.dumps({'response': 200})
        else:
            response = requests.post(C8Y_BASE + '/event/events', headers=C8Y_HEADERS, data=json.dumps(event))
            if response.ok:
                return response.json()
            self.log_warning_on_bad_repsonse(response)
            return None
            

    def log_warning_on_bad_repsonse(self, response):
        if not response.ok:
            log.warning(f'response status code is not ok: {response}, content: {response.text}')

    def get_or_create_device(self, sim_id, label):
        if self.mocking:
            log.info(f"mock: get or create device with external id {sim_id}")
            return sim_id
        
        # Check if device already created
        return self.get_device_by_external_id(sim_id) or self.__create_device(sim_id, label)
    def count_all_profiles(self):
        return self.__count_all(self.OEE_CALCULATION_PROFILE_TYPE)
    
    def count_all_categories(self):
        return self.__count_all(self.OEE_CALUCLATION_CATEGORY)
    def __count_all(self, oee_type):
        if self.mocking:
            log.info(f'mock: count_all types({oee_type})')
            return 5

        request_query = f'{C8Y_BASE}/inventory/managedObjects/count?type={oee_type}'
        repsonse = requests.get(request_query, headers=C8Y_HEADERS)
        if repsonse.ok:
            return repsonse.json()

    def count_profiles(self, device_id):
        ''' count all profiles for the given device id.
        '''
        if self.mocking:
            log.info(f'mock: count_profiles(${device_id})')
            return 10
        request_query = f'{C8Y_BASE}/inventory/managedObjects/count?type={self.OEE_CALCULATION_PROFILE_TYPE}&text={device_id}'
        response = requests.get(request_query, headers=C8Y_HEADERS)
        if response.ok:
            try:
                return int(response.text)
            except Exception as e:
                log.warn(f'cannot convert "${response.text}" to number. exception: {e}')
                return 0
        else:
            self.log_warning_on_bad_repsonse(response)
            return 0
    
    def create_managed_object(self, fragment: str):
        if self.mocking:
            log.info(f'mock: create_managed_object()')
            return {'id': '0'}
        response = requests.post(C8Y_BASE + '/inventory/managedObjects', headers=C8Y_HEADERS, data=fragment)
        if response.ok:
            return response.json()
        self.log_warning_on_bad_repsonse(response)
        #TODO: check for errors
        return {}

    def get_managed_object(self, id: str):
        if self.mocking:
            log.info(f'mock: get_managed_object()')
            return {'id': '0'}
        response = requests.get(C8Y_BASE + f'/inventory/managedObjects/{id}', headers=C8Y_HEADERS)
        if response.ok:
            return response.json()
        self.log_warning_on_bad_repsonse(response)
        #TODO: check for errors
        return {}
    
    def get_calculation_categories(self):
        if self.mocking:
            log.info(f'mock: get_managed_object()')
            return [{'id': '0'}]
        response = requests.get(C8Y_BASE + f'/inventory/managedObjects?type={self.OEE_CALUCLATION_CATEGORY}', headers=C8Y_HEADERS)
        if response.ok:
            return response.json()['managedObjects']
        self.log_warning_on_bad_repsonse(response)        
        return {}

    def delete_managed_object(self, id: str):
        if self.mocking:
            log.info(f'mock: delete_managed_object()')
            return {'id': '0'}
        response = requests.delete(C8Y_BASE + f'/inventory/managedObjects/{id}', headers=C8Y_HEADERS)
        if response.ok:
            return 1
        self.log_warning_on_bad_repsonse(response)
        #TODO: check for errors
        return 0

    def update_managed_object(self, device_id, fragment):
        if self.mocking:
            log.info(f'mock: update_managed_object()')
            return {'id': '0'}

        response = requests.put(f'{C8Y_BASE}/inventory/managedObjects/{device_id}', headers=C8Y_HEADERS, data=fragment)
        if response.ok:
            return response.json()
        self.log_warning_on_bad_repsonse(response)
        return {}

    def add_child_object(self, device_id: str, child_id: str):
        if self.mocking:
            log.info(f'mock: add_child_device()')
            return {'id': '0'}

        data = {"managedObject": {"id": child_id}}
        response = requests.post(f'{C8Y_BASE}/inventory/managedObjects/{device_id}/childDevices', headers=C8Y_HEADERS, data=json.dumps(data))
        if response.ok:
            return response.json()

        self.log_warning_on_bad_repsonse(response)
        return {}

    def find_simulators(self):
        if self.mocking:
            log.info(f'mock: find_simulators()')
            return []
        response = requests.get(f'{C8Y_BASE}/inventory/managedObjects?type={self.C8Y_SIMULATORS_GROUP}&fragmentType=c8y_IsDevice&pageSize=100', headers=C8Y_HEADERS)
        if response.ok:
            mangaged_objects = response.json()['managedObjects']
            return [mo['id'] for mo in mangaged_objects]
        log.warning(f'Cannot find simulators: {response}, content:{response.text}')
        return []

    def get_external_ids(self, device_ids):
        external_ids = []
        for id in device_ids:
            external_id_response = requests.get(C8Y_BASE + '/identity/globalIds/' + id + '/externalIds', headers=C8Y_HEADERS)
            if external_id_response.ok:
                external_ids.append(external_id_response.json()['externalIds'][0]['externalId'])
        
        return external_ids

    def get_device_by_external_id(self, external_id):
        response = requests.get(f'{C8Y_BASE}/identity/externalIds/{self.C8Y_SIMULATORS_GROUP}/{external_id}', headers=C8Y_HEADERS)
        if response.ok:
            device_id = response.json()['managedObject']['id']
            log.info(f'Device({device_id}) has been found by its external id "{self.C8Y_SIMULATORS_GROUP}/{external_id}".')
            return device_id
        log.warning(f'No device has been found for the external id "{self.C8Y_SIMULATORS_GROUP}/{external_id}".')
        return None
    
    def __create_device(self, external_id, name):
        log.info(f'Creating a new device with following external id "{self.C8Y_SIMULATORS_GROUP}/{external_id}"')
        device = {
            'name': name,
            'c8y_IsDevice': {},
            'type': self.C8Y_SIMULATORS_GROUP
        }
        device = self.create_managed_object(json.dumps(device))
        device_id = device['id']
        if device_id:
            log.info(f'new device created({device_id})')
            return self.__add_external_id(device_id, external_id)
        return device_id

    def __add_external_id(self, device_id, ext_id, type = C8Y_SIMULATORS_GROUP):
        external_id = {
            'type': type,
            'externalId': ext_id
        }
        response = requests.post(C8Y_BASE + '/identity/globalIds/' + device_id + '/externalIds', headers=C8Y_HEADERS, data=json.dumps(external_id))
        self.log_warning_on_bad_repsonse(response)
        return device_id

    def get_tenant_option_by_category(self, category):
        log.info(f'Receiving Tenant option: ')
        response = requests.get(C8Y_BASE + f'/tenant/options/{category}', headers=C8Y_HEADERS)
        if response.ok:
            log.info(f'Got options: {response.json()} for category {category}')
            return
        log.warn(f'Could not get any tenant options for category {category}. response status code is: {response}, content: {response.text}')

