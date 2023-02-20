from simulators.main.oeeAPI import ProfileCreateMode, OeeAPI
from simulators.main.simulator import get_or_create_device_id, load
from simulators.main.cumulocityAPI import CumulocityAPI
import unittest
from unittest.mock import patch
import logging

cumulocity_api = CumulocityAPI()
log = logging.getLogger("Test")
logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.DEBUG)

cumulocityAPI = CumulocityAPI()
oeeAPI = OeeAPI()

# Get Tenant Options and configure Simulator
MICROSERVICE_OPTIONS = cumulocityAPI.get_tenant_option_by_category("simulators")
PROFILE_CREATE_MODE = ProfileCreateMode[MICROSERVICE_OPTIONS.get("CREATE_PROFILES", "CREATE_IF_NOT_EXISTS")]
CREATE_PROFILES_ARGUMENTS = MICROSERVICE_OPTIONS.get("CREATE_PROFILES_ARGUMENTS", "")
CREATE_ASSET_HIERARCHY = MICROSERVICE_OPTIONS.get("CREATE_ASSET_HIERARCHY", "False")
LOG_LEVEL = MICROSERVICE_OPTIONS.get("LOG_LEVEL", "INFO")
DELETE_PROFILES = MICROSERVICE_OPTIONS.get("DELETE_PROFILES", "False")


class Test(unittest.TestCase):

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
        cumulocity_api.delete_managed_object(self.device_id)
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

    @patch('logging.Logger.error')  # patch the log.error method
    def test_load_json_file(self, mock_error):
        log.info("Start testing load json file")
        self.model = load("simulators/main/simulator.json") # Load model for unittest CLI
        if not self.model:
            self.model = load("../simulators/main/simulator.json") # Load model for unittest on IDE
        self.assertIsNotNone(self.model)
        log.info('-' * 100)


if __name__ == '__main__':
    # begin the unittest.main()
    unittest.main()