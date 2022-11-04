# Generic scripts information
This scripts folder contains:
- The **ExportProfileData.py** which is used to export measurements or alarms data from devices
- The **Environment.py** which is used to setup environment parameters

## Setup environment parameters:
Input base url, tenant ID, username, password in Environment.py file

## Install cumulocity-python-api package
Follow the instructions in: https://github.com/SoftwareAG/cumulocity-python-api

### Installation from PyPI
```shell
pip install c8y_api
```

## Run the script
If the environment parameters were not setup, they can be input as arguments when running the script
```shell
python ExportProfilesData.py [-h] [--baseurl BASEURL] [--id-tenant ID_TENANT]
                             [--username USERNAME --password PASSWORD]
                             [--data-type {measurements,alarms}]
                             [--mode {all,specific}]
```
optional arguments:
  -h, --help            show this help message and exit
  --baseurl BASEURL, -b BASEURL
                        Base URL of the tenant
  --id-tenant ID_TENANT, -i ID_TENANT
                        Tenant ID
  --username USERNAME, -u USERNAME
                        Tenant's username
  --password PASSWORD, -p PASSWORD
                        Tenant's password
  --data-type {measurements,alarms}, -d {measurements,alarms}
                        Choose data type between "measurement" or "alarm"
  --mode {all,specific}, -m {all,specific}
                        Extract "all" devices data or only data from a
                        "specific" device
