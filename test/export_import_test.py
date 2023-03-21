import unittest, logging, os
import config.root # Set source directory

from unittest.mock import patch
from subprocess import call

class Test(unittest.TestCase):
    def test_export_profile_data(self):
        # Run the ExportProfileData.py script
        call(["python", "../simulators/extras/ExportProfileData.py"])

        # Check if the export_data folder is created
        self.assertTrue(os.path.exists("export_data"), msg="export_data folder not found")

        # Remove the export_data folder
        os.rmdir("export_data")

if __name__ == '__main__':
    unittest.main()
