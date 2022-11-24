import json, logging, requests
from enum import Enum

from cumulocityAPI import C8Y_BASE, C8Y_TENANT, C8Y_HEADERS, CumulocityAPI

log = logging.getLogger("OeeAPI")

def to_variable(name: str):
    return '${' + name + '}'

def substitute(template: str, replacers: dict):
    result = template
    for key in replacers:
        result = result.replace(to_variable(key), replacers[key])
    return result

class ProfileCreateMode(Enum):
    CREATE = 1
    CREATE_IF_NOT_EXISTS = 2

class OeeAPI:
    OEE_BASE = f'{C8Y_BASE}/service/oee-bundle'
    CONF_REST_ENDPOINT = f'{OEE_BASE}/configurationmanager/2/configuration'
    SHIFTPLAN_REST_ENDPOINT = f'{OEE_BASE}/mes/shiftplan'
    c8y_api = CumulocityAPI()

    templates = {}

    def new_profile(self, external_id):
        template = self.find_template(external_id)
        device_id = self.c8y_api.get_device_by_external_id(external_id)
        existing_profile_count = self.count_profiles_for(device_id)

        if not template:
            log.warning(f'cannot create profile for the external id {external_id} b/c no template is found')
            return None
        if not template or not device_id:
            log.warning(f'cannot create profile for the external id {external_id} b/c not deviceId is found: {device_id}')
            return None


        replacers = {
            'deviceId': device_id,
            'counter': str(existing_profile_count + 1),
            'tenantId': C8Y_TENANT
        }

        profile_def = substitute(template, replacers)

        log.info(f'creating new_profile for device {device_id}. Number of already existing profiles: {existing_profile_count}')

        profile = self.__create_profile(profile_def)
        if profile:
            result = self.c8y_api.add_child_object(device_id, profile["id"])
            if result:
                log.info(f'profile {profile["id"]} added to the device {device_id}')
            else:
                log.info(f'cannot add profile {profile["id"]} to the device {device_id}')
            self.c8y_api.add_external_id(device_id=profile["id"], ext_id=f'{external_id.lower()}_profile', type="c8y_EventBasedSimulatorProfile")
        return profile
    
    def activate(self, profile):
        profile["status"] = "ACTIVE"
        response = requests.put(f'{self.CONF_REST_ENDPOINT}/{profile["id"]}', headers=C8Y_HEADERS, data=json.dumps(profile))
        if response.ok:
            return response.json()
        
        log.warning(f'cannot activate profile. response: {response}, content: {response.text}')
        return {}

    def create_and_activate_profile(self, external_id: str, mode: ProfileCreateMode = ProfileCreateMode.CREATE):
        try:            
         
            if mode == ProfileCreateMode.CREATE_IF_NOT_EXISTS:
                device_id = self.c8y_api.get_device_by_external_id(external_id)
                if self.count_profiles_for(device_id) > 0:
                    log.info(f'At least one profile exists already for the device {device_id}.')
                    return None
                    
            profile = self.new_profile(external_id)
            if profile:
                profile = self.activate(profile)
                if profile['status'] == 'ACTIVE':
                    log.info(f'New profile {profile["name"]}({profile["id"]}) for the device {profile["deviceId"]} has been created and activated.')
                    return profile
        except Exception as e:
            log.warning(f'Couldn\'t create profile for {external_id} due to: {e}')
        return None

    def __create_profile(self, profile_definition):
        response = requests.post(self.CONF_REST_ENDPOINT, headers=C8Y_HEADERS, data=profile_definition)
        if response.ok:
            return response.json()
        log.warning(f'cannot create profile with request: {self.CONF_REST_ENDPOINT}. response was nok: {response}, message: {response.text}')
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
            log.warning(f'cannot read file {template_name} due to {e}')
        return None
    
    def count_profiles_for(self, device_id):
        return self.c8y_api.count_profiles(device_id)
    
    def delete_all_simulators_profiles(self):
        simulator_ids = self.get_simulator_ids()

        profiles = self.get_profiles()
        deleted_profiles = 0
        for profile in profiles:
            if profile['deviceId'] in simulator_ids and profile["locationId"] == "Matrix":
                if self.remove_profile(profile):
                    deleted_profiles = deleted_profiles + 1

        log.info(f'profiles deleted: {deleted_profiles}')

    def get_profiles(self):
        log.info(f'Trying to get Profiles URL:{self.CONF_REST_ENDPOINT} with Headers: {C8Y_HEADERS}')
        response = requests.get(self.CONF_REST_ENDPOINT, headers=C8Y_HEADERS)
        if response.ok:
            return response.json()
        log.warning(f'Cannot get profiles: {response}, content:{response.text}')
        return {}
    
    def remove_profile(self, profile):
        response = requests.delete(f'{self.CONF_REST_ENDPOINT}/{profile["id"]}', headers=C8Y_HEADERS)
        if response.ok:
            log.info(f'Profile {profile["name"]} deleted.')
            return True
        log.warning(f'Cannot delete profile: {response}, content:{response.text}')
        return False

    def get_simulator_ids(self):
        ids = self.c8y_api.find_simulators()
        if ids:
            return ids
        log.warning(f'Didnt find any simulators: {ids}')
        return []

    def get_simulator_external_ids(self):
        ids = self.get_simulator_ids()
        if ids:
            return self.c8y_api.get_external_ids(ids)
        log.warning(f'Didnt find any simulators: {ids}')
        return []  
    
    def add_timeslots_for_shiftplan(self,shiftplan):
        locationId = shiftplan.locationId
        for timeslot in shiftplan.recurringTimeSlots:
            self.add_timeslot(locationId, timeslot)
        return True

    def add_timeslot(self, locationId, timeslot):
        url = f'{self.SHIFTPLAN_REST_ENDPOINT}/{locationId}/timeslot'
        response = requests.post(url, headers=C8Y_HEADERS, data = json.dumps(timeslot))
        if response.ok:
            log.info(f'Timeslot for {locationId} was created')
            return True
        log.warning(f'Cannot create Timeslot for location:{locationId}, content: {response.status_code} - {response.text}, url: {url}, data: {json.dumps(timeslot)}')
        return False

    def get_shiftplan(self, locationId, dateFrom, dateTo):
        url = f'{self.SHIFTPLAN_REST_ENDPOINT}/{locationId}?dateFrom={dateFrom}&dateTo={dateTo}'
        response = requests.get(url, headers=C8Y_HEADERS)
        if response.ok:
            return response.json()
        log.warning(f'Cannot get shiftplan for {locationId}, url: {url},  response: {response.status_code}: {response.text} ')
        return {'locationId':locationId,'timeslots':{}}

    def create_asset_hierachy(self, deviceIDs):
        lineHierarchy = []
        for deviceID in deviceIDs:
            profileID = self.c8y_api.get_profile_id(deviceID=deviceID)
            if profileID != "":
                lineHierarchy.append({"profileID":profileID, "ID":deviceID})
            
        lineMO = self.c8y_api.createISAType(type="LINE", hierachy=lineHierarchy, description="Simulator LINE", oeetarget=80)

        if lineMO != {}:
            siteMO = self.c8y_api.createISAType(type="SITE", hierachy=[{"profileID": None, "ID": lineMO['id']}], description="Simulator SITE", oeetarget=80)
            log.info(f'Created asset hierachy. Line-ID {lineMO["id"]} Site-ID {siteMO["id"]}')