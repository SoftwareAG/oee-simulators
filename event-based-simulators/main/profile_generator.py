import time, json, os, logging, requests, base64
from datetime import datetime

from cumulocityAPI import C8Y_BASE, C8Y_TENANT, C8Y_HEADERS, CumulocityAPI

VERSION = '1.0.1'

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


cumulocityAPI = CumulocityAPI()

def to_variable(name: str):
    return '${' + name + '}'

def substitute(template: str, replacers: dict):
    result = template
    for key in replacers:
        result = result.replace(to_variable(key), replacers[key])
    return result

external_ids = [f'SIM_00{number}' for number in range(1,8)]

class OeeApi:
    CONF_REST_ENDPOINT = f'{C8Y_BASE}/service/oee-bundle/configurationmanager/2/configuration'
    c8y_api = CumulocityAPI()

    templates = {}

    def new_profile(self, external_id):
        template = self.find_template(external_id)
        device_id = self.find_device(external_id)
        existing_profile_count = self.count_profiles_for(device_id)

        if not template or not device_id:
            logging.warn(f'cannot create profile for the external id {external_id}')
            return None

        replacers = {
            'deviceId': device_id,
            'counter': str(existing_profile_count + 1),
            'tenantId': C8Y_TENANT
        }

        profile_def = substitute(template, replacers)

        print(f'creating new_profile for device {device_id}. Number of already existing profiles: {existing_profile_count}')

        profile = self.__create_profile(profile_def)
        if profile:
            result = self.c8y_api.add_child_object(device_id, profile["id"])
            if result:
                logging.info(f'profile {profile["id"]} added to the device {device_id}')
            else:
                logging.info(f'cannot add profile {profile["id"]} to the device {device_id}')
        return profile
    
    def activate(self, profile):
        profile["status"] = "ACTIVE"
        response = requests.put(f'{self.CONF_REST_ENDPOINT}/{C8Y_TENANT}/{profile["id"]}', headers=C8Y_HEADERS, data=json.dumps(profile))
        if response.ok:
            return response.json()
        
        logging.warn(f'cannot activate profile. response: {response}, content: {response.text}')
        return {}

    def __create_profile(self, profile_definition):
        response = requests.post(self.CONF_REST_ENDPOINT, headers=C8Y_HEADERS, data=profile_definition)
        if response.ok:
            return response.json()
        logging.warn(f'cannot create profile. response was nok: {response}, message: {response.text}')
        return None

    def find_device(self, external_id):
        ids = self.c8y_api.find_device_by_external_id(external_id)
        if ids:
            return ids[0]
        return None

    def find_template(self, external_id: str):
        template_name = f'{external_id.lower()}_profile.template'
        if template_name in self.templates.keys():
            return self.templates[template_name]
        try:
            template = open(template_name, 'r').read()
            self.templates[template_name] = template
            return template
        except Exception as e:
            logging.warn(f'cannot read file {template_name} due to {e}')
        return None
    
    def count_profiles_for(self, device_id):
        return self.c8y_api.count_profiles(device_id)
    
    def delete_all_simulators_profile(self):
        simulator_ids = [api.find_device(id) for id in external_ids]

        profiles = self.get_profiles()
        deleted_profiles = 0
        for profile in profiles:
            if profile['deviceId'] in simulator_ids and profile["locationId"] == "Matrix":
                if self.delete_profile(profile):
                    deleted_profiles = deleted_profiles + 1

        print("profiles deleted:", deleted_profiles)

    def get_profiles(self):
        response = requests.get(f'{self.CONF_REST_ENDPOINT}', headers=C8Y_HEADERS)
        if response.ok:
            return response.json()
        logging.warn(f'Cannot get profiles: {response}, content:{response.text}')
        return {}
    
    def delete_profile(self, profile):
        response = requests.delete(f'{self.CONF_REST_ENDPOINT}/{C8Y_TENANT}/{profile["id"]}', headers=C8Y_HEADERS)
        if response.ok:
            logging.info(f'Profile {profile["name"]} deleted.')
            return True
        logging.warn(f'Cannot delete profile: {response}, content:{response.text}')
        return False

api = OeeApi()

def create_and_activate_profile(external_id: str):
    try:
        profile = api.new_profile(external_id)
        if profile:
            profile = api.activate(profile)
            if profile['status'] == 'ACTIVE':
                logging.info(f'New profile {profile["name"]}({profile["id"]}) for the device {profile["deviceId"]} has been created and activated.')
                return profile
    except Exception as e:
        logging.warn(f'Couldn\'t create profile for {external_id} due to {e}')
    return None

def delete_profile(id):
    response = requests.delete(f'{C8Y_BASE}/inventory/managedObjects/{id}', headers=C8Y_HEADERS)
    if response.ok:
        logging.info(f'deleted managed object {id}')
    else:
        logging.warning(f'Couldn\'t delete managed object. response: {response}, content: {response.text}')


# api.delete_all_simulators_profile()

PROFILES_PER_DEVICE = 1

for id in external_ids:
    for _ in range(PROFILES_PER_DEVICE):
       profile = create_and_activate_profile(id)

