import base64
import json
import logging
import os
import requests

import ArgumentsAndCredentialsHandler
import Environment

from datetime import datetime, timedelta, timezone
from os.path import isfile, join

####################################################
if not os.path.exists('logs'):
    os.makedirs('logs')
logger = logging.getLogger('ExportImportProfileData')
relativeFilePath = f"logs\log{datetime.strftime(datetime.now(), '%Y%m%d%H%M%S_%f')}.log"
filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
hdlr = logging.FileHandler(filePath)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)
####################################################
# Setup for additional API request message
user_and_pass_bytes = base64.b64encode(
    (Environment.C8Y_TENANT + "/" + Environment.C8Y_USER + ':' + Environment.C8Y_PASSWORD).encode('ascii'))  # bytes
user_and_pass = user_and_pass_bytes.decode('ascii')  # decode to str

C8Y_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Basic ' + user_and_pass
}


#####################################################


def exportAllProfileData(c8y, DATA_TYPE, createFrom, createTo):
    # Loop through the list of device in Device management
    for device in c8y.device_inventory.select(type="c8y_EventBasedSimulator"):
        logger.info(f"Found device '{device.name}', id: #{device.id}, "
                     f"owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        logger.info(f"List of {device.name}'s child devices: ")
        for childDevice in device.child_devices:
            logger.info(f"Child device {childDevice.name}, id #{childDevice.id}")
            if DATA_TYPE == "alarms":
                listAlarms(c8y, childDevice, createFrom, createTo, DATA_TYPE)
            elif DATA_TYPE == "measurements":
                # listing measurements of child device
                listMeasurements(c8y, childDevice, createFrom, createTo, DATA_TYPE)
            else:
                listAlarms(c8y, childDevice, createFrom, createTo, 'alarms')
                listMeasurements(c8y, childDevice, createFrom, createTo, 'measurement')


def ExportSpecificProfileDataWithDeviceId(c8y, DATA_TYPE, createFrom, createTo, DEVICE_ID):
    logger.info(f"Search for {DATA_TYPE} data from device {DEVICE_ID} ")
    deviceCount = 0
    response = requests.get(f'{Environment.C8Y_BASE}/inventory/managedObjects/{DEVICE_ID}',
                            headers=C8Y_HEADERS)
    deviceName = response.json()['name']
    for device in c8y.device_inventory.select(name=deviceName):
        deviceCount += 1
        logger.info(f"Child device {device.name}, id #{device.id}")
        if DATA_TYPE == "alarms":
            listAlarms(c8y, device, createFrom, createTo, DATA_TYPE)
        elif DATA_TYPE == "measurements":
            # listing measurements of child device
            listMeasurements(c8y, device, createFrom, createTo, DATA_TYPE)
        else:
            listAlarms(c8y, device, createFrom, createTo, 'alarms')
            listMeasurements(c8y, device, createFrom, createTo, 'measurement')

    if deviceCount == 0:
        logger.deug(f"No device with id {DEVICE_ID} found")


def listAlarms(c8y, device, createFrom, createTo, DATA_TYPE):
    filePath = createFilePathFromDateTime(DATA_TYPE, device.id)
    # Create a count variable as a json/dict key to save json data
    count = 0
    for alarm in c8y.alarms.select(source=device.id, created_after=createFrom, created_before=createTo):
        logger.info(
            f"Found alarm id #{alarm.id}, severity: {alarm.severity}, time: {alarm.time}, creation time: {alarm.creation_time}, update time : {alarm.updated_time}\n")
        count += 1
        appendDataToJsonFile(alarm.to_json(), filePath, count, 'alarms')


def listMeasurements(c8y, device, createFrom, createTo, DATA_TYPE):
    filePath = createFilePathFromDateTime(DATA_TYPE, device.id)
    # Create a count variable as a json/dict key to save json data
    count = 0
    for measurement in c8y.measurements.select(source=device.id, after=createFrom, before=createTo):
        logger.info(f"Found measurement id #{measurement.id}\n")
        count += 1
        appendDataToJsonFile(measurement.to_json(), filePath, count, 'measurements')


def appendDataToJsonFile(jsonData, filePath, count, data_type, json_data={}):
    try:
        # Load content of existing json data file
        with open(filePath, 'r') as f:
            json_data = json.load(f)
            logger.info(json_data)
    except:
        logger.debug(f"Create new data json file {filePath}")

    # Create new json file or add data to an existing json file
    with open(filePath, 'w') as f:
        json_data[f"{count}"] = jsonData
        json.dump(json_data, f, indent=2)
        print(f"{data_type} data {count}th is added to file {filePath}")


def createFilePathFromDateTime(DATA_TYPE, deviceId):
    # Check if folder containing data files exists and make one if not
    if not os.path.exists('export_data'):
        os.makedirs('export_data')
    # Make data folder bases on device ID
    if not os.path.exists(f'export_data\{deviceId}'):
        os.makedirs(f'export_data\{deviceId}')
    if deviceId:
        # dd/mm/YY H:M:S
        deviceId = deviceId.replace(" ", "")
        dateTimeString = datetime.now().strftime(f"{deviceId}_{DATA_TYPE}_%d_%m_%Y_%H_%M_%S")
    else:
        dateTimeString = datetime.now().strftime(f"{DATA_TYPE}_%d_%m_%Y_%H_%M_%S")
    relativeFilePath = f'export_data\{deviceId}\{dateTimeString}.json'
    filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
    logger.info(filePath)
    return filePath


def checkFileList():
    if not os.path.exists('export_data'):
        logger.debug("No folder with name export_data")
    else:
        onlyfiles = [f for f in os.listdir('export_data') if isfile(join('export_data', f))]
        return onlyfiles


def SetTimePeriodToExportData(CREATE_FROM, CREATE_TO):
    if not CREATE_FROM or CREATE_TO:
        createTo = datetime.now().replace(tzinfo=timezone.utc)
        TimeUnit = Environment.TIME_UNIT

        if TimeUnit == 'seconds' or not TimeUnit:
            createFrom = createTo - timedelta(seconds=Environment.PERIOD_TO_EXPORT)
            return createFrom, createTo

        if TimeUnit == 'days':
            createFrom = createTo - timedelta(days=Environment.PERIOD_TO_EXPORT)
        elif TimeUnit == 'weeks':
            createFrom = createTo - timedelta(weeks=Environment.PERIOD_TO_EXPORT)
        elif TimeUnit == 'hours':
            createFrom = createTo - timedelta(hours=Environment.PERIOD_TO_EXPORT)
        elif TimeUnit == 'minutes':
            createFrom = createTo - timedelta(minutes=Environment.PERIOD_TO_EXPORT)
        return createFrom, createTo

    return CREATE_FROM, CREATE_TO


# Main function to run the script
if __name__ == '__main__':
    c8y = ArgumentsAndCredentialsHandler.c8yPlatformConnection()
    DATA_TYPE, DEVICE_ID, CREATE_FROM, CREATE_TO = ArgumentsAndCredentialsHandler.argumentsParser()

    createFrom, createTo = SetTimePeriodToExportData(CREATE_FROM, CREATE_TO)
    logger.debug(f"Export data which is created after/from: {createFrom}")
    logger.debug(f"and created before/to: {createTo}")

    if not DEVICE_ID:
        exportAllProfileData(c8y, DATA_TYPE, createFrom, createTo)
    else:
        ExportSpecificProfileDataWithDeviceId(c8y, DATA_TYPE, createFrom, createTo, DEVICE_ID)

