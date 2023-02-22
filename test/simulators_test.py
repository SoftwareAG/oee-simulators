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

    def test_get_or_create_device_id_with_full_model_and_delete(self):
        self.device_model = {
            "type": "Simulator",
            "id": "sim_001_test",
            "label": "Test Simulator #1",
            "enabled": "true"
        }
        log.info(f"Created device model: {self.device_model}")
        log.info("Start testing create device and adding external id")
        self.device_id = get_or_create_device_id(device_model=self.device_model)
        # null device_id will fail the test
        self.assertIsNotNone(self.device_id)
        self.cumulocity_api.delete_managed_object(self.device_id)
        log.info(f"Removed the test device with id {self.device_id}")
        log.info('-' * 100)

    def test_get_or_create_device_id_with_missing_id(self):
        self.device_model = {
            "type": "Simulator",
            "label": "Test Simulator #1",
            "enabled": "true"
        }
        log.info(f"Created device model without id: {self.device_model}")
        log.info("Start testing create device without id definition")
        self.device_id = get_or_create_device_id(device_model=self.device_model)
        # null device_id will fail the test
        self.assertIsNone(self.device_id)
        log.info('-' * 100)

    def test_get_or_create_device_id_with_missing_label(self):
        self.device_model = {
            "type": "Simulator",
            "id": "sim_001_test",
            "enabled": "true"
        }
        log.info(f"Created device model without label: {self.device_model}")
        log.info("Start testing create device without label")
        self.device_id = get_or_create_device_id(device_model=self.device_model)
        # null device_id will fail the test
        self.assertIsNone(self.device_id)
        log.info('-' * 100)

    @patch('logging.Logger.error')  # patch to hide the log.error method
    def test_load_json_file(self, mock_error):
        log.info("Start testing load json file")
        self.model = load("simulators/main/simulator.json") # Load model for unittest CLI
        if not self.model:
            self.model = load("../simulators/main/simulator.json") # Load model for unittest on IDE
        self.assertIsNotNone(self.model)
        log.info('-' * 100)

    def test_create_and_activate_oee_profile(self):
        self.device_model = {
            "type": "Simulator",
            "id": "sim_001_test",
            "label": "Test Simulator #1",
            "enabled": "true"
        }
        self.device_id = get_or_create_device_id(device_model=self.device_model)
        self.device_profile_info = self.oee_api.create_and_activate_profile(external_id=self.device_model.get('id'))
        # null device_id will fail the test
        self.assertIsNotNone(self.device_profile_info)
        self.cumulocity_api.delete_managed_object(self.device_profile_info.get('id'))
        log.info(f"Removed the test oee profile with id {self.device_profile_info.get('id')}")
        self.cumulocity_api.delete_managed_object(self.device_id)
        log.info(f"Removed the test device with id {self.device_id}")
        log.info('-' * 100)


if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()