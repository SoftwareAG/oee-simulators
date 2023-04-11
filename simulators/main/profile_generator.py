import time, json, os, logging, requests

from cumulocityAPI import C8Y_BASEURL, C8Y_TENANT, C8Y_HEADERS, CumulocityAPI
from oeeAPI import OeeAPI
from argparse import ArgumentParser

def try_int(value):
    try:
        return int(value)
    except:
        return None

PROFILES_PER_DEVICE = try_int(os.environ.get('PROFILES_PER_DEVICE')) or 1
SLEEP_TIME_FOR_PROFILE_CREATION_LOOP = try_int(os.environ.get('SLEEP_TIME_FOR_PROFILE_CREATION_LOOP')) or 60 * 12

parser = ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-c", "--create-profiles", action="store_true", dest="createProfiles",
                    help="create profiles")
group.add_argument("-r", "--remove-simulator-profiles-via-oee", action="store_true", dest="removeSimulatorProfilesViaOee",
                    help="remove all simulator profiles using the OEE API provided by oee-bundle")
group.add_argument("-d", "--delete-simulator-profiles", action="store_true", dest="deleteSimulatorProfiles", help="delete all simulator profiles using the C8Y inventory API (useful if oee-bundle is not working/available")
group.add_argument("-ds", "--delete-simulators", action="store_true", dest="deleteSimulators", help="delete all simulators using the C8Y inventory API (useful if oee-bundle is not working/available")
group.add_argument("-cat", "--create-categories", action="store_true", dest="createCalculationCategories", help="create or update calclation categories")
group.add_argument("--delete-categories", action="store_true", dest="deleteCalculationCategories", help="delete all calclation categories")
args = parser.parse_args()

# JSON-PYTHON mapping, to get json.load() working
null = None
false = False
true = True
######################

logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.INFO)
log = logging.getLogger("profile-generator")
log.info("using C8Y backend:" + C8Y_BASEURL)
log.info("using C8Y tenant:" + C8Y_TENANT)

c8y_api = CumulocityAPI()    
oee_api = OeeAPI()

def delete_profiles():
    simulator_ids = oee_api.get_simulator_ids()
    deleted_profiles = 0
    for simulator_id in simulator_ids:
        log.info(f'deleting profiles for {simulator_id}')
        response = requests.get(f'{C8Y_BASEURL}/inventory/managedObjects/{simulator_id}', headers=C8Y_HEADERS)
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
    
if args.deleteCalculationCategories:
    log.info('===================================')
    log.info('starting to delete all calculation categories ...')
    log.info(
        f'existing category managed objects: {c8y_api.count_all_categories()}')
    deleted_categories = 0
    for category in c8y_api.get_calculation_categories():
        deleted_categories += c8y_api.delete_managed_object(category['id'])
    log.info(f'Managed_objects deleted: {deleted_categories}')

if args.createCalculationCategories:
    log.info('===================================')
    log.info('starting to create calculation categories ...')
    with open('./categories.json', 'r') as f:
        categories = f.read()
    if (c8y_api.count_all_categories()) == 0:
        log.info('Create category managed object')
        c8y_api.create_managed_object(categories)
    elif (c8y_api.count_all_categories()) == 1:
        log.info('Update category managed object')
        categories_by_id = {}
        for c in json.loads(categories)['categories'] + c8y_api.get_calculation_categories()[0]['categories']:
            categories_by_id[c['id']] = c
        mo_id = c8y_api.get_calculation_categories()[0]['id']
        fragment = {
            'categories': list(categories_by_id.values())
        }
        c8y_api.update_managed_object(mo_id, json.dumps(fragment))
    else:
        log.warning('More than 1 category managed object! Unable to update managed object')
    log.info('==========Categories created==========')

if args.deleteSimulators:
    simulator_ids = oee_api.get_simulator_ids()
    deleted_simulators = 0
    for simulator_id in simulator_ids:
        log.info(f'Deleting simulator #{simulator_id}')
        response = c8y_api.delete_managed_object(simulator_id)
        if response:
            log.info(f'Deleted successfully simulator #{simulator_id}')
            deleted_simulators += 1
        else:
            log.info(f'Failed to delete simulator #{simulator_id}')

    log.info(f'Total simulators: {len(simulator_ids)}')
    log.info(f'Total deleted simulators: {deleted_simulators}')
