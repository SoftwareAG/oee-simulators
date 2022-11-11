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
- create from
- create to
- time unit
- period to export

Notice: 
- if **'create from'** and **'create to'** are set, set **'time unit'** and **'period to export'** to **None**, and vice versa.
- if you would like to export all data from every child devices, set **'device id'** to **None**

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

## Run the import script
The [Import Script](./ImportData.py) can be used to import alarms and measurements into cumulocity. The [Export Script](./ExportOrImportProfileData.py) can be used to export a file for any managed object. This exact file can then be used for the import.
```shell
ImportData.py [-h] [--ifile INPUTFILE] [--log {DEBUG, INFO}] [--username C8Y_USERNAME] [--password C8Y_PASSWORD] [--baseurl C8Y_BASEURL] [--tenant C8Y_TENANT_ID]
```
### Credentials Arguments
Credentials for the C8Y instance can be handed to the script using cli arguments as shown in the example above. The script will try to extract the crendentials from the [Environment File](./Environment.py) if no credentials are presented as arguments.

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
Example files can be found [here](./export_data/).