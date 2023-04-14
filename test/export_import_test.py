import sys, unittest, logging, os
import config.root # Configure root directories
import simulators.extras.Environment as Ex_Im_Env

from datetime import timezone, datetime, timedelta
from simulators.main.oeeAPI import ProfileCreateMode, OeeAPI
from simulators.main.cumulocityAPI import CumulocityAPI, C8Y_USER, C8Y_PASSWORD, C8Y_TENANT, C8Y_BASEURL
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
        # Extracts the base name of the current directory
        base_dir = os.path.basename(current_dir)
        # If the working directory is test then change to extras
        if base_dir == "oee-simulators":
            os.chdir("simulators/extras")
        elif base_dir == "test":
            os.chdir("../simulators/extras")

        try:
            external_device_id = "sim_001"
            device_id = self.cumulocity_api.get_device_by_external_id(external_id=f"{external_device_id}")
            profile_id = self.cumulocity_api.get_profile_id(deviceID=device_id)

            log.info("Begin export data")
            # Take export time period

            date_from, date_to = Utils.set_time_period()

            # Run the ExportProfileData.py script
            call(["python", "ExportProfileData.py", "--device-ids", f"{profile_id}", "--username", f"{C8Y_USER}", "--password", f"{C8Y_PASSWORD}", "--tenant-id", f"{C8Y_TENANT}", "--baseurl", f"{C8Y_BASEURL}", "--test"])

            filename = f"{external_device_id}_profile"
            # Check if the sim_001_profile.json is created
            profile_path = f"export_data/{filename}.json"

            Utils.change_working_dir_between_extras_and_test()

            self.assertTrue(os.path.exists(profile_path), msg=f"{filename}.json not found")

            # Open the JSON file and load its contents
            data = load(profile_path)
            # Check if the data file is empty
            self.assertTrue(len(data.get('measurements')) > 0 or len(data.get('alarms')) > 0, msg=f"No data in {filename}.json")

            log.info("Delete all extract data")
            self.cumulocity_api.delete_alarms(date_from=date_from,date_to=date_to,device_id=profile_id)
            self.cumulocity_api.delete_measurements(date_from=date_from,date_to=date_to,device_id=profile_id)

            log.info("Begin import data")

            Utils.change_working_dir_between_extras_and_test()

            # Run the ImportData.py script and get the exit code
            exit_code = call(["python", "ImportData.py", "--ifiles", f"{filename}", "--username", f"{C8Y_USER}", "--password", f"{C8Y_PASSWORD}", "--tenant-id", f"{C8Y_TENANT}", "--baseurl", f"{C8Y_BASEURL}", "--test"])
            # Check if the exit code is 0
            self.assertEqual(exit_code, 0, msg="ImportData.py script failed to run")

            # Get measurements and alarms from c8y
            measurements = self.cumulocity_api.get_measurements(date_from=date_from, date_to=date_to, device_id=profile_id)
            alarms = self.cumulocity_api.get_alarms(date_from=date_from, date_to=date_to, device_id=profile_id)
            self.assertTrue(len(measurements.get('measurements')) > 0 or len(alarms.get('alarms')) > 0, msg="No data after deleting and re-importing data")


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
    @staticmethod
    def change_working_dir_between_extras_and_test():
        base_dir = os.path.basename(os.getcwd())
        # If the working directory is test then change to extras
        if base_dir == "test":
            os.chdir("../simulators/extras")
        elif base_dir == "extras":
            os.chdir("../../test")

if __name__ == '__main__':
    # create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)

    # create a test runner
    runner = unittest.TextTestRunner()

    # run the test suite using the test runner
    result = runner.run(suite)

    # print the test result summary
    log.info(f"Executed: {result.testsRun}")
    log.info(f"Failed: {len(result.failures)}")
    log.info(f"Errors: {len(result.errors)}")

    # return True if no failures or errors, False otherwise
    if len(result.failures) == 0 and len(result.errors) == 0:
        sys.exit(0)
    else:
        sys.exit(1)
