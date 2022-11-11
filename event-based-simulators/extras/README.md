# Generic scripts information
This scripts folder contains:
- The **ExportOrImportProfileData.py** which is used to export measurements or alarms data from devices.
- The **Environment.py** which is used to set up environment parameters.

## Setup environment parameters:
Input necessary configuration in **Environment.py** file\

Required:
- base url f
- tenant ID 
- username 
- password

Optional:
- action
- mode
- data type
- device name

## Install cumulocity-python-api package
Follow the instructions in: https://github.com/SoftwareAG/cumulocity-python-api

### Installation from PyPI
```shell
pip install c8y_api
```

## Run the script
If the environment **optional** parameters were not setup, they can be input as arguments when running the script
```shell
ExportOrImportProfileData.py [-h] [--device-id DEVICE_ID]
                                    [--action {export,import}]
                                    [--data-type {measurements,alarms,all}]
```
optional arguments:\
  -h, --help                                                              : show this help message and exit. \
  --action {export,import}, -a {export,import}                            : "Export" or "Import" data.\
  --data-type {measurements,alarms, all}, -d {measurements,alarms, all}   : Export "alarms" or "measurements".\
  --device-id DEVICE_NAME, -i DEVICE_NAME                                 : Input device id\

## Run the import script
The [Import Script](./ImportData.py) can be used to import alarms and measurements into cumulocity. The [Export Script](./ExportOrImportProfileData.py) can be used to export a file for any managed object. This exact file can then be used for the import.
```shell
ImportData.py [-h] [--ifile INPUTFILE] [--log {DEBUG, INFO}]
```
### Logging
Log-level: two log level can be set using the --log argument {DEBUG, INFO}. Log-level INFO is default. DEBUG can be used to get more output of the script execution.

### INPUTFILE
The inputfile that should be used for this script should has the external_id of the managed object as name. For example: ```sim_001_profile.json```

The schema of the inputfile is:
```json
{
  "alarms":[],
  "measurements":[]
}
```
Example files can be found [here](./export_data/)