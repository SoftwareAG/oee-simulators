import time, json, os, logging, requests
from datetime import datetime
from argparse import ArgumentParser

from cumulocityAPI import C8Y_BASE, C8Y_TENANT, C8Y_HEADERS, CumulocityAPI
from oeeAPI import OeeAPI, ProfileCreateMode

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

logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.INFO)
log = logging.getLogger("profile-generator")
log.info("using C8Y backend:" + C8Y_BASE)
log.info("using C8Y tenant:" + C8Y_TENANT)

c8y_api = CumulocityAPI()    
oee_api = OeeAPI()

def delete_profiles():
    simulator_ids = oee_api.get_simulator_ids()
    deleted_profiles = 0
    for simulator_id in simulator_ids:
        log.info(f'deleting profiles for {simulator_id}')
        response = requests.get(f'{C8Y_BASE}/inventory/managedObjects/{simulator_id}', headers=C8Y_HEADERS)
        if response.ok:            
            child_devices = response.json()['childDevices']['references']
            for child_device in child_devices:
                child_device_id = child_device['managedObject']['id']
                child_device_json = c8y_api.get_managed_object(child_device_id)
                if child_device_json['type'] == c8y_api.OEE_CALCULATION_PROFILE_TYPE:
                    log.info(f'deleting managed object {child_device_id}')
                    deleted_profiles = deleted_profiles + c8y_api.delete_managed_object(child_device_id)
        else:
            log.warning(f'Couldn\'t find the managed object. response: {response}, content: {response.text}')
    log.info(f'profiles deleted: {deleted_profiles}')

if args.createProfiles:
    log.info('===============================')
    log.info('starting to create profiles ...')
    log.info(f'existing profiles: {c8y_api.count_all_profiles()}')

    counter = 0
    for _ in range(PROFILES_PER_DEVICE):
        for external_id in oee_api.get_simulator_external_ids():
            profile = oee_api.create_and_activate_profile(external_id)
            counter = counter + 1
            if counter % 200 == 0:
                log.info(f'profiles: {c8y_api.count_all_profiles()}. Wait for {SLEEP_TIME_FOR_PROFILE_CREATION_LOOP} minutes')
                # sleep for some time to be able to verify if calculation is still working with the given number of profiles
                time.sleep(SLEEP_TIME_FOR_PROFILE_CREATION_LOOP) 
    log.info(f'profiles after execution: {c8y_api.count_all_profiles()}')

if args.removeSimulatorProfilesViaOee:
    log.info('===============================================')
    log.info('starting to remove all simulator profiles via OEE API ...')
    log.info(f'existing profiles: {c8y_api.count_all_profiles()}')
    oee_api.delete_all_simulators_profiles()
    log.info(f'profiles after execution: {c8y_api.count_all_profiles()}')

if args.deleteSimulatorProfiles:
    log.info('===================================')
    log.info('starting to delete all simulator profiles ...')
    log.info(f'existing profiles: {c8y_api.count_all_profiles()}')
    delete_profiles()
    log.info(f'profiles after execution: {c8y_api.count_all_profiles()}')
    
