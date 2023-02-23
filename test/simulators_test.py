import unittest, logging, os, sys
import config.root # Set source directory

from simulators.main.oeeAPI import ProfileCreateMode, OeeAPI, substitute
from simulators.main.simulator import get_or_create_device_id, load
from simulators.main.cumulocityAPI import CumulocityAPI, C8Y_TENANT
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
        device_id = Utils.create_device(self.device_model)
        # null device_id will fail the test
        self.assertIsNotNone(device_id)
        self.cumulocity_api.delete_managed_object(device_id)
        log.info(f"Removed the test device with id {device_id}")
        log.info('-' * 100)

    def test_get_or_create_device_id_with_missing_id(self):
        device_id = Utils.create_device(self.device_model_no_id)
        # null device_id will fail the test
        self.assertIsNone(device_id)
        log.info('-' * 100)

    def test_get_or_create_device_id_with_missing_label(self):
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
        managed_object = self.oee_api.create_update_asset_hierarchy(type="LINE", hierarchy_array=[{"profileID": '', "ID": ''}], description="test LINE", oee_target=80)
        self.assertIsNotNone(managed_object)
        id = managed_object.get('id')
        self.cumulocity_api.delete_managed_object(id)
        log.info(f"Removed the test organization structure with id {id}")
        log.info('-' * 100)

class Utils:
    @staticmethod
    def create_device(device_model):
        log.info(f"Created device model: {device_model}")
        log.info("Start testing create device and adding external id")
        device_id = get_or_create_device_id(device_model=device_model)
        return device_id



if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()