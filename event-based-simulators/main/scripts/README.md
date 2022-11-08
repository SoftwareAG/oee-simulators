# Generic scripts information
This scripts folder contains:
- The **ExportOrImportProfileData.py** which is used to export measurements or alarms data from devices.
- The **Environment.py** which is used to set up environment parameters.

## Setup environment parameters:
Input necessary configuration in **Environment.py** file\

Required:
- base url 
- tenant ID 
- username 
- password

Optional:
- action
- mode
- data type

## Install cumulocity-python-api package
Follow the instructions in: https://github.com/SoftwareAG/cumulocity-python-api

### Installation from PyPI
```shell
pip install c8y_api
```

## Run the script
If the environment **optional** parameters were not setup, they can be input as arguments when running the script
```shell
ExportOrImportProfileData.py [-h] --action {export,import} --mode {all,specific} --data-type {measurements,alarms}

```
optional arguments:\
  -h, --help                                                    : show this help message and exit. \
  --action {export,import}, -a {export,import}                  : "Export" or "Import" data.\
  --mode {all,specific}, -m {all,specific}                      : Extract data from "all" device, or from "specific" device.\
  --data-type {measurements,alarms}, -d {measurements,alarms}   : Export "alarms" or "measurements".\
