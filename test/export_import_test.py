import shutil, unittest, logging, os
import config.root # Set source directory

from simulators.main.interface import datetime_to_string
from datetime import datetime, timedelta
from simulators.main.oeeAPI import ProfileCreateMode, OeeAPI
from simulators.main.cumulocityAPI import CumulocityAPI
from unittest.mock import patch
from subprocess import call
from simulators.main.simulator import load
from test.simulators_test import Utils

log = logging.getLogger("Test Import Export")
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

    @patch('logging.Logger.error')
    def test_export_import_profile_data(self, mock_error):
        # Get current working directory
        current_dir = os.getcwd()
        # Change working directory to extras to run script and export data
        try:
            os.chdir("../simulators/extras") # IDE
        except:
            os.chdir("simulators/extras") # Command line

        try:
            external_device_id = "sim_001"
            device_id = self.cumulocity_api.get_device_by_external_id(external_id=f"{external_device_id}")
            profile_id = self.cumulocity_api.get_profile_id(deviceID=device_id)

            log.info("Begin export data")
            # Run the ExportProfileData.py script
            call(["python", "ExportProfileData.py", "--device-ids", f"{profile_id}"])
            filename = f"{external_device_id}_profile"
            # Check if the sim_001_profile.json is created
            profile_path = f"export_data/{filename}.json"
            self.assertTrue(os.path.exists(profile_path), msg=f"{filename}.json not found")

            # Open the JSON file and load its contents
            data = load(profile_path)
            # Check if the data file is empty
            self.assertNotEqual(len(data),0, msg=f"No content in {filename}.json file")

            log.info("Begin import data")
            # Run the ImportData.py script and get the exit code
            exit_code = call(["python", "ImportData.py", "--ifiles", f"{filename}"])

            # Check if the exit code is 0
            self.assertEqual(exit_code, 0, msg="ImportData.py script failed to run")

        finally:
            # Iterate over all files and subdirectories in dir_path
            for filename in os.listdir("export_data"):
                # Create the full file path by joining the directory and filename
                file_path = os.path.join("export_data", filename)

                # Check if the file_path is a file or directory and remove it accordingly
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                log.info(f"Removed {file_path}")

            # Change back to the original working directory
            os.chdir(current_dir)

if __name__ == '__main__':
    unittest.main()
