import unittest, logging, os, sys
from datetime import datetime

import config.root # Set source directory

from simulators.main.oeeAPI import ProfileCreateMode, OeeAPI, substitute
from simulators.main.simulator import get_or_create_device_id, load
from simulators.main.cumulocityAPI import CumulocityAPI, C8Y_TENANT
from simulators.main.interface import datetime_to_string
from unittest.mock import patch

log = logging.getLogger("Test")
logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.DEBUG)


class Test(unittest.TestCase):
    def setUp(self):
        self.oee_api = OeeAPI()
        self.cumulocity_api = CumulocityAPI()
        # Get Tenant Options and configure Simulator
        self.MICROSERVICE_OPTIONS = self.cumulocity_api.get_tenant_option_by_category("simulators")
        self.PROFILE_CREATE_MODE = ProfileCreateMode[self.MICROSERVICE_OPTIONS.get("CREATE_PROFILES", "CREATE_IF_NOT_EXISTS")]
        self.CREATE_PROFILES_ARGUMENTS = self.MICROSERVICE_OPTIONS.get("CREATE_PROFILES_ARGUMENTS", "")
        self.CREATE_ASSET_HIERARCHY = self.MICROSERVICE_OPTIONS.get("CREATE_ASSET_HIERARCHY", "False")
        self.DELETE_PROFILES = self.MICROSERVICE_OPTIONS.get("DELETE_PROFILES", "False")
        self.device_model = {
            "type": "Simulator",
            "id": "sim_001_test",
            "label": "Test Simulator #1",
            "enabled": "true"
        }
        self.device_model_no_id = {
            "type": "Simulator",
            "label": "Test Simulator #1",
            "enabled": "true"
        }
        self.device_model_no_label = {
            "type": "Simulator",
            "id": "sim_001_test",
            "enabled": "true"
        }

    def test_get_or_create_device_id_with_full_model_and_delete(self):
        log.info("Start testing create device and adding external id")
        device_id = Utils.create_device(self.device_model)
        # null device_id will fail the test
        self.assertIsNotNone(device_id)
        self.cumulocity_api.delete_managed_object(device_id)
        log.info(f"Removed the test device with id {device_id}")
        log.info('-' * 100)

    def test_get_or_create_device_id_with_missing_id(self):
        log.info("Start testing create device with no id")
        device_id = Utils.create_device(self.device_model_no_id)
        # null device_id will fail the test
        self.assertIsNone(device_id)
        log.info('-' * 100)

    def test_get_or_create_device_id_with_missing_label(self):
        log.info("Start testing create device with no label")
        device_id = Utils.create_device(self.device_model_no_label)
        # null device_id will fail the test
        self.assertIsNone(device_id)
        log.info('-' * 100)

    @patch('logging.Logger.error')  # patch to hide the log.error method
    def test_load_json_file(self, mock_error):
        log.info("Start testing load json file")
        model = load("simulators/main/simulator.json") # Load model for unittest CLI
        if not model:
            model = load("../simulators/main/simulator.json") # Load model for unittest on IDE
        self.assertIsNotNone(model)
        log.info('-' * 100)

    def test_create_and_activate_oee_profile(self):
        log.info("Start testing create and activate oee profile")
        device_id = Utils.create_device(device_model=self.device_model)
        device_profile_info = self.oee_api.create_and_activate_profile(external_id=self.device_model.get('id'))
        # null device_profile_info will fail the test
        self.assertIsNotNone(device_profile_info)
        self.cumulocity_api.delete_managed_object(device_profile_info.get('id'))
        log.info(f"Removed the test oee profile with id {device_profile_info.get('id')}")
        self.cumulocity_api.delete_managed_object(device_id)
        log.info(f"Removed the test device with id {device_id}")
        log.info('-' * 100)

    def test_create_update_organization_structure(self):
        log.info("Start testing create hierarchy asset (organization structure)")
        device_id = Utils.create_device(self.device_model)
        line_managed_object, site_managed_object = self.oee_api.create_or_update_asset_hierarchy(deviceIDs=device_id, line_description = "Simulator LINE", line_type = "LINE", site_description = "Simulator SITE", site_type = "SITE", oee_target = 80)
        self.assertIsNotNone(line_managed_object.get('hierarchy'))
        self.assertIsNotNone(site_managed_object.get('hierarchy'))
        line_id = line_managed_object.get('id')
        site_id = site_managed_object.get('id')
        self.cumulocity_api.delete_managed_object(site_id)
        log.info(f"Removed the test SITE with id {site_id}")
        self.cumulocity_api.delete_managed_object(line_id)
        log.info(f"Removed the test LINE structure with id {line_id}")
        self.cumulocity_api.delete_managed_object(device_id)
        log.info(f"Removed the test device with id {device_id}")
        log.info('-' * 100)

    def test_send_event(self):
        log.info("Start testing sending event")
        device_id = Utils.create_device(self.device_model)
        log.info(f"Created the {self.device_model.get('label')} with id {device_id}")
        event = {
             'source': {
                 'id': f'{device_id}'
             },
             'time': f'{datetime_to_string(datetime.utcnow())}',
             'type': 'Availability',
             'text': 'Availability',
             'status': 'up',
             'production_time_s': 0.0,
             'production_speed_h': 25.0,
             'pieces_produced': 0.0
        }
        response = self.cumulocity_api.send_event(event)
        self.assertIsNotNone(response)
        self.cumulocity_api.delete_managed_object(device_id)
        log.info(f"Removed the {self.device_model.get('label')} with id {device_id}")


    def test_send_measurement(self):
        log.info("Start testing create measurement")
        device_id = Utils.create_device(self.device_model)
        log.info(f"Created the {self.device_model.get('label')} with id {device_id}")

        measurement = {
              'type': 'PumpPressure',
              'time': f'{datetime_to_string(datetime.utcnow())}',
              'source': {
                  'id': f'{device_id}'
              },
              'Pressure': {
                  'P':
                      {
                          'unit': 'hPa',
                          'value': 1179.26
                      }
              }

        }
        response = self.cumulocity_api.create_measurements(measurement)
        self.assertIsNotNone(response)
        self.cumulocity_api.delete_managed_object(device_id)
        log.info(f"Removed the {self.device_model.get('label')} with id {device_id}")

class Utils:
    @staticmethod
    def create_device(device_model):
        log.info(f"Created device model: {device_model}")
        device_id = get_or_create_device_id(device_model=device_model)
        return device_id



if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()