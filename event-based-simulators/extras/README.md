# Generic scripts information
This scripts folder contains:
- The **ExportProfileData.py** which is used to export measurements or alarms data from devices.
- The **Environment.py** which is used to set up environment parameters.

## Setup environment parameters:
Input necessary configuration in **Environment.py** file\

Required:
- base url
- tenant ID 
- username 
- password

Optional:
- data type
- device id

## Install cumulocity-python-api package
Follow the instructions in: https://github.com/SoftwareAG/cumulocity-python-api

### Installation from PyPI
```shell
pip install c8y_api
```

## Run the script
If the environment **optional** parameters were not setup, they can be input as arguments when running the script
```shell
ExportProfileData.py [-h] [--device-id DEVICE_ID]
                                    [--action {export,import}]
                                    [--data-type {measurements,alarms,all}]
```
optional arguments:\
  -h, --help                                                              : show this help message and exit. \
  --data-type {measurements,alarms, all}, -d {measurements,alarms, all}   : Export "alarms" or "measurements".\
  --device-id DEVICE_NAME, -i DEVICE_NAME                                 : Input device id\