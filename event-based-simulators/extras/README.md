# Generic scripts information
This scripts folder contains:
- The [Export Script](./ExportOrImportProfileData.py) can be used to export a json file for any managed object. This json file can then be used for the import.
- The [Environment File](./Environment.py) is used to set up environment parameters.
- The [Import Script](./ImportData.py) can be used to import alarms and measurements into cumulocity.

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

## Run the export script
If the environment **optional** parameters were not setup, they can be input as arguments when running the script.
```shell
ExportProfileData.py [-h] [--device-id DEVICE_ID]
                            [--create-from CREATE_FROM]
                            [--create-to CREATE_TO]
                            [--data-type {measurements,alarms,all}]
                            [--log {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                            [--username USERNAME] [--password PASSWORD]
                            [--baseurl BASEURL] [--tenant TENANT]

```

optional arguments:\
  -h, --help : show this help message and exit\
  --device-id DEVICE_ID, -i DEVICE_ID : Input device id\
  --create-from CREATE_FROM, -from CREATE_FROM : Input "create from" milestone\
  --create-to CREATE_TO, -to CREATE_TO : Input "create to" milestone\
  --data-type {measurements,alarms,all}, -d {measurements,alarms,all} : Export "alarms" or "measurements"\
  --log {DEBUG,INFO,WARNING,ERROR,CRITICAL}, -l {DEBUG,INFO,WARNING,ERROR,CRITICAL} : Log-level\
  --username USERNAME, -u USERNAME : C8Y Username\
  --password PASSWORD, -p PASSWORD : C8Y Password\
  --baseurl BASEURL, -b BASEURL : C8Y Baseurl\
  --tenant TENANT, -t TENANT : C8Y TenantID\

### Credentials Arguments
Credentials for the C8Y instance can be handed to the script using cli arguments as shown in the example above. The script will try to extract the crendentials from the [Environment File](./Environment.py) if no credentials are presented as arguments.

### Logging
Log-level: five log levels can be set using the --log argument {DEBUG, INFO, WARNING, ERROR, CRITICAL}. From left to right is the decreasing order of log info amount can be seen: DEBUG>INFO>WARNING>ERROR>CRITICAL. For example, if INFO level is set, DEBUG level messages can not be seen.

### Export time period
Input both create-from and create-to to set export time. The time format should be: "%Y-%m-%dT%H:%M:%S.%fZ" (i.e 2022-11-14T13:45:15.893Z)


## Run the import script
 
```shell
ImportData.py [-h] --ifile INPUTFILE [--log {DEBUG, INFO, WARNING, ERROR, CRITICAL}] [--username C8Y_USERNAME] [--password C8Y_PASSWORD] [--baseurl C8Y_BASEURL] [--tenant C8Y_TENANT_ID]
```
Example:
```shell
python ImportData.py --ifile export_data\simulator_normal-#1.json --log DEBUG --username admin --password abcxzy123
```
### INPUTFILE **REQUIRED**
The inputfile that should be used for this script should has the external_id of the managed object as name. For example: ```sim_001_profile.json```.

### Credentials Arguments
Credentials for the C8Y instance can be handed to the script using cli arguments as shown in the example above. The script will try to extract the crendentials from the [Environment File](./Environment.py) if no credentials are presented as arguments.

### Logging
Log-level: five log levels can be set using the --log argument {DEBUG, INFO, WARNING, ERROR, CRITICAL}. From left to right is the decreasing order of log info amount can be seen: DEBUG>INFO>WARNING>ERROR>CRITICAL. For example, if INFO level is set, DEBUG level messages can not be seen.


The schema of the inputfile is:
```json
{
  "alarms":[],
  "measurements":[]
}
```
Example files can be found [here](./export_data/).