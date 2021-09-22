import time, json, os, logging, requests
from datetime import datetime
from argparse import ArgumentParser

from cumulocityAPI import C8Y_BASE, C8Y_TENANT, C8Y_HEADERS, CumulocityAPI

PROFILES_PER_DEVICE = os.environ.get('PROFILES_PER_DEVICE') or 1
SLEEP_TIME_FOR_PROFILE_CREATION_LOOP = os.environ.get('SLEEP_TIME_FOR_PROFILE_CREATION_LOOP') or 60 * 12

parser = ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-c", "--create-profiles", action="store_true", dest="createProfiles",
                    help="create profiles")
group.add_argument("-r", "--remove-simulator-profiles-via-oee", action="store_true", dest="removeSimulatorProfilesViaOee",
                    help="remove all simulator profiles using the OEE API provided by oee-bundle")
group.add_argument("-d", "--delete-simulator-profiles", action="store_true", dest="deleteSimulatorProfiles",
                    help="delete all simulator profiles using the C8Y inventory API (useful if oee-bundle is not working/available")
args = parser.parse_args()

# JSON-PYTHON mapping, to get json.load() working
null = None
false = False
true = True
######################

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logging.info("using C8Y backend:" + C8Y_BASE)
logging.info("using C8Y tenant:" + C8Y_TENANT)

c8y_api = CumulocityAPI()

def to_variable(name: str):
    return '${' + name + '}'

def substitute(template: str, replacers: dict):
    result = template
    for key in replacers:
        result = result.replace(to_variable(key), replacers[key])
    return result

class OeeApi:
    CONF_REST_ENDPOINT = f'{C8Y_BASE}/service/oee-bundle/configurationmanager/2/configuration'
    c8y_api = CumulocityAPI()

    templates = {}

    def new_profile(self, external_id):
        template = self.find_template(external_id)
        device_id = self.c8y_api.get_device_by_external_id(external_id)
        existing_profile_count = self.count_profiles_for(device_id)

        if not template:
            logging.warning(f'cannot create profile for the external id {external_id} b/c no template is found')
            return None
        if not template or not device_id:
            logging.warning(f'cannot create profile for the external id {external_id} b/c not deviceId is found: {device_id}')
            return None


        replacers = {
            'deviceId': device_id,
            'counter': str(existing_profile_count + 1),
            'tenantId': C8Y_TENANT
        }

        profile_def = substitute(template, replacers)

        logging.info(f'creating new_profile for device {device_id}. Number of already existing profiles: {existing_profile_count}')

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
        response = requests.put(f'{self.CONF_REST_ENDPOINT}/{profile["id"]}', headers=C8Y_HEADERS, data=json.dumps(profile))
        if response.ok:
            return response.json()
        
        logging.warning(f'cannot activate profile. response: {response}, content: {response.text}')
        return {}

    def __create_profile(self, profile_definition):
        response = requests.post(self.CONF_REST_ENDPOINT, headers=C8Y_HEADERS, data=profile_definition)
        if response.ok:
            return response.json()
        logging.warning(f'cannot create profile with request: {self.CONF_REST_ENDPOINT}. response was nok: {response}, message: {response.text}')
        return None

    def find_template(self, external_id: str):
        template_name = f'main/{external_id.lower()}_profile.template'
        if template_name in self.templates.keys():
            return self.templates[template_name]
        try:
            template = open(template_name, 'r').read()
            self.templates[template_name] = template
            return template
        except Exception as e:
            logging.warning(f'cannot read file {template_name} due to {e}')
        return None
    
    def count_profiles_for(self, device_id):
        return self.c8y_api.count_profiles(device_id)
    
    def delete_all_simulators_profiles(self):
        simulator_ids = oee_api.get_simulator_ids()

        profiles = self.get_profiles()
        deleted_profiles = 0
        for profile in profiles:
            if profile['deviceId'] in simulator_ids and profile["locationId"] == "Matrix":
                if self.remove_profile(profile):
                    deleted_profiles = deleted_profiles + 1

        logging.info(f'profiles deleted: {deleted_profiles}')

    def get_profiles(self):
        response = requests.get(f'{self.CONF_REST_ENDPOINT}', headers=C8Y_HEADERS)
        if response.ok:
            return response.json()
        logging.warning(f'Cannot get profiles: {response}, content:{response.text}')
        return {}
    
    def remove_profile(self, profile):
        response = requests.delete(f'{self.CONF_REST_ENDPOINT}/{profile["id"]}', headers=C8Y_HEADERS)
        if response.ok:
            logging.info(f'Profile {profile["name"]} deleted.')
            return True
        logging.warning(f'Cannot delete profile: {response}, content:{response.text}')
        return False

    def get_simulator_ids(self):
        ids = self.c8y_api.find_simulators()
        if ids:
            return ids
        logging.warning(f'Didnt find any simulators: {ids}')
        return []

    def get_simulator_external_ids(self):
        ids = self.get_simulator_ids()
        if ids:
            return self.c8y_api.get_external_ids(ids)
        logging.warning(f'Didnt find any simulators: {ids}')
        return []    
    
oee_api = OeeApi()

def create_and_activate_profile(external_id: str):
    try:
        profile = oee_api.new_profile(external_id)
        if profile:
            profile = oee_api.activate(profile)
            if profile['status'] == 'ACTIVE':
                logging.info(f'New profile {profile["name"]}({profile["id"]}) for the device {profile["deviceId"]} has been created and activated.')
                return profile
    except Exception as e:
        logging.warning(f'Couldn\'t create profile for {external_id} due to: {e}')
    return None

def delete_profiles():
    simulator_ids = oee_api.get_simulator_ids()
    deleted_profiles = 0
    for simulator_id in simulator_ids:
        logging.info(f'deleting profiles for {simulator_id}')
        response = requests.get(f'{C8Y_BASE}/inventory/managedObjects/{simulator_id}', headers=C8Y_HEADERS)
        if response.ok:            
            child_devices = response.json()['childDevices']['references']
            for child_device in child_devices:
                child_device_id = child_device['managedObject']['id']
                child_device_json = c8y_api.get_managed_object(child_device_id)
                if child_device_json['type'] == c8y_api.OEE_CALCULATION_PROFILE_TYPE:
                    logging.info(f'deleting managed object {child_device_id}')
                    deleted_profiles = deleted_profiles + c8y_api.delete_managed_object(child_device_id)
        else:
            logging.warning(f'Couldn\'t find the managed object. response: {response}, content: {response.text}')
    logging.info(f'profiles deleted: {deleted_profiles}')

if args.createProfiles:
    logging.info('===============================')
    logging.info('starting to create profiles ...')
    logging.info(f'existing profiles: {c8y_api.count_all_profiles()}')

    counter = 0
    for _ in range(PROFILES_PER_DEVICE):
        for external_id in oee_api.get_simulator_external_ids():
            profile = create_and_activate_profile(external_id)
            counter = counter + 1
            if counter % 200 == 0:
                logging.info(f'profiles: {c8y_api.count_all_profiles()}. Wait for {SLEEP_TIME_FOR_PROFILE_CREATION_LOOP} minutes')
                # sleep for some time to be able to verify if calculation is still working with the given number of profiles
                time.sleep(SLEEP_TIME_FOR_PROFILE_CREATION_LOOP) 
    logging.info(f'profiles after execution: {c8y_api.count_all_profiles()}')

if args.removeSimulatorProfilesViaOee:
    logging.info('===============================================')
    logging.info('starting to remove all simulator profiles via OEE API ...')
    logging.info(f'existing profiles: {c8y_api.count_all_profiles()}')
    oee_api.delete_all_simulators_profiles()
    logging.info(f'profiles after execution: {c8y_api.count_all_profiles()}')

if args.deleteSimulatorProfiles:
    logging.info('===================================')
    logging.info('starting to delete all simulator profiles ...')
    logging.info(f'existing profiles: {c8y_api.count_all_profiles()}')
    delete_profiles()
    logging.info(f'profiles after execution: {c8y_api.count_all_profiles()}')
    
