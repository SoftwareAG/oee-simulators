import shutil, unittest, logging, os
import config.root # Set source directory

from unittest.mock import patch
from subprocess import call
from simulators.main.simulator import load

log = logging.getLogger("Test Import Export")
logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.DEBUG)

class Test(unittest.TestCase):
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
            # Run the ExportProfileData.py script
            call(["python", "ExportProfileData.py"])

            # Check if the sim_001_profile.json is created
            profile_path = os.path.join("export_data", "sim_001_profile.json")
            self.assertTrue(os.path.exists(profile_path), msg="sim_001_profile.json not found")

            # Open the JSON file and load its contents
            data = load(profile_path)
            # Check if the data file is empty
            self.assertNotEqual(len(data),0, msg="No content in sim_001_profile.json file")


            # Run the ImportData.py script and get the exit code
            exit_code = call(["python", "ImportData.py"])

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

            # Change back to the original working directory
            os.chdir(current_dir)

if __name__ == '__main__':
    unittest.main()
