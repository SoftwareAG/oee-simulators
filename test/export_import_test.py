import shutil, unittest, logging, os
import config.root # Set source directory

from unittest.mock import patch
from subprocess import call

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

        # Run the ExportProfileData.py script
        call(["python", "ExportProfileData.py"])

        # Check if the export_data folder is created
        self.assertTrue(os.path.exists("export_data"), msg="export_data folder not found")

        # Run the ImportData.py script and get the exit code
        exit_code = call(["python", "ImportData.py"])

        # Check if the exit code is 0
        self.assertEqual(exit_code, 0, msg="ImportData.py script failed to run")

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
