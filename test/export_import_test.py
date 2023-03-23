import shutil, unittest, logging, os
from datetime import timezone, datetime, timedelta

import config.root # Set source directory
import simulators.extras.Environment as Ex_Im_Env

from simulators.main.oeeAPI import ProfileCreateMode, OeeAPI
from simulators.main.cumulocityAPI import CumulocityAPI
from unittest.mock import patch
from subprocess import call
from simulators.main.simulator import load
from simulators.main.interface import datetime_to_string


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
            # Take export time period
            date_from, date_to = Utils.set_time_period()
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

            log.info("Delete all extract data")
            self.cumulocity_api.delete_alarms(date_from=date_from,date_to=date_to,device_id=profile_id)
            self.cumulocity_api.delete_measurements(date_from=date_from,date_to=date_to,device_id=profile_id)

            log.info("Begin import data")
            # Run the ImportData.py script and get the exit code
            exit_code = call(["python", "ImportData.py", "--ifiles", f"{filename}"])
            # Check if the exit code is 0
            self.assertEqual(exit_code, 0, msg="ImportData.py script failed to run")

            # Get measurements and alarms from c8y
            measurements = self.cumulocity_api.get_measurements(date_from=date_from, date_to=date_to, device_id=profile_id)
            alarms = self.cumulocity_api.get_alarms(date_from=date_from, date_to=date_to, device_id=profile_id)
            self.assertIsNotNone(measurements)
            self.assertIsNotNone(alarms)

        finally:
            # Change back to the original working directory
            os.chdir(current_dir)

class Utils():
    @staticmethod
    def set_time_period():
        date_to = datetime.now().replace(tzinfo=timezone.utc)
        time_unit = Ex_Im_Env.TIME_UNIT

        if time_unit == 'seconds' or not time_unit:
            date_from = date_to - timedelta(seconds=Ex_Im_Env.PERIOD_TO_EXPORT)
            return date_from, date_to

        if time_unit == 'days':
            date_from = date_to - timedelta(days=Ex_Im_Env.PERIOD_TO_EXPORT)
        elif time_unit == 'weeks':
            date_from = date_to - timedelta(weeks=Ex_Im_Env.PERIOD_TO_EXPORT)
        elif time_unit == 'hours':
            date_from = date_to - timedelta(hours=Ex_Im_Env.PERIOD_TO_EXPORT)
        elif time_unit == 'minutes':
            date_from = date_to - timedelta(minutes=Ex_Im_Env.PERIOD_TO_EXPORT)

        date_from = datetime_to_string(date_from)
        date_to = datetime_to_string(date_to)

        return date_from, date_to

if __name__ == '__main__':
    unittest.main()
