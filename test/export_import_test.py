import shutil, unittest, logging, os
import config.root # Set source directory

from unittest.mock import patch
from subprocess import call

log = logging.getLogger("Test Import Export")
logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.DEBUG)

class Test(unittest.TestCase):
    def test_export_profile_data(self):
        # Get current working directory
        current_dir = os.getcwd()
        # Change working directory to extras to run script and export data
        os.chdir("../simulators/extras")

        # Run the ExportProfileData.py script
        call(["python", "ExportProfileData.py"])

        # Check if the export_data folder is created
        self.assertTrue(os.path.exists("export_data"), msg="export_data folder not found")

        # Remove the export_data directory and its contents
        shutil.rmtree("export_data")

        # Change back to the original working directory
        os.chdir(current_dir)

if __name__ == '__main__':
    unittest.main()
