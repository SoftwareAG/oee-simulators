import json
import logging
import os
from datetime import datetime, timedelta, timezone
from os.path import isfile, join

import ArgumentsAndCredentialsHandler


def exportAllProfileData(c8y, DATA_TYPE, createFrom, createTo):
    filePath = createFilePathFromDateTime(DATA_TYPE, None)
    # Loop through the list of device in Device management
    for device in c8y.device_inventory.select(type="c8y_EventBasedSimulator"):
        logging.info(f"Found device '{device.name}', id: #{device.id}, "
              f"owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        logging.info(f"List of {device.name}'s child devices: ")
        for childDevice in device.child_devices:
            logging.info(f"Child device {childDevice.name}, id #{childDevice.id}")
            if DATA_TYPE == "alarms":
                listAlarms(c8y, childDevice, createFrom, createTo, filePath)
            elif DATA_TYPE == "measurements":
                # listing measurements of child device
                listMeasurements(c8y, childDevice, createFrom, createTo, filePath)


def exportSpecificProfileData(c8y, DATA_TYPE, createFrom, createTo, DEVICE_NAME):
    logging.info(f"Search for {DATA_TYPE} data from device {DEVICE_NAME} ")
    filePath = createFilePathFromDateTime(DATA_TYPE, DEVICE_NAME)
    deviceCount = 0
    for device in c8y.device_inventory.select(type="c8y_EventBasedSimulator", name=DEVICE_NAME):
        logging.info(f"Found device '{device.name}', id: #{device.id}")
        deviceCount += 1
        logging.info(f"List of {device.name}'s child devices: ")
        for childDevice in device.child_devices:
            logging.info(f"Child device {childDevice.name}, id #{childDevice.id}")
            if DATA_TYPE == "alarms":
                listAlarms(c8y, childDevice, createFrom, createTo, filePath)
            elif DATA_TYPE == "measurements":
                # listing measurements of child device
                listMeasurements(c8y, childDevice, createFrom, createTo, filePath)

    if deviceCount == 0:
        logging.info(f"No device with name {DEVICE_NAME} found")


def listAlarms(c8y, childDevice, createFrom, createTo, filePath):
    count = 0
    for alarm in c8y.alarms.select(source=childDevice.id, created_after=createFrom, created_before=createTo):
        logging.info(
            f"Found alarm id #{alarm.id}, severity: {alarm.severity}, time: {alarm.time}, creation time: {alarm.creation_time}, update time : {alarm.updated_time}\n")
        count += 1
        appendDataToJsonFile(alarm.to_json(), filePath, count)


def listMeasurements(c8y, childDevice, createFrom, createTo, filePath):
    # Create a count variable as a json/dict key to save json data
    count = 0
    for measurement in c8y.measurements.select(source=childDevice.id, after=createFrom, before=createTo):
        logging.info(f"Found measurement id #{measurement.id}\n, type: {measurement.type}\n")
        count += 1
        appendDataToJsonFile(measurement.to_json(), filePath, count)


def appendDataToJsonFile(jsonData, filePath, count, json_data={}):
    try:
        # Load content of existing json data file
        with open(filePath, 'r') as f:
            json_data = json.load(f)
            logging.info(json_data)
    except:
        logging.info(f"Create new data json file {filePath}")

    # Create new json file or add data to an existing json file
    with open(filePath, 'w') as f:
        json_data[f"{count}"] = jsonData
        json.dump(json_data, f, indent=2)
        logging.info("New data is added to file")


def createFilePathFromDateTime(DATA_TYPE, deviceName):
    # Check if folder containing data files exists and make one if not
    if not os.path.exists('export_data'):
        os.makedirs('export_data')
    if deviceName:
        # dd/mm/YY H:M:S
        deviceName = deviceName.replace(" ", "")
        dateTimeString = datetime.now().strftime(f"{deviceName}_{DATA_TYPE}_%d_%m_%Y_%H_%M_%S")
    else:
        dateTimeString = datetime.now().strftime(f"{DATA_TYPE}_%d_%m_%Y_%H_%M_%S")
    relativeFilePath = f'export_data\{dateTimeString}.json'
    filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
    logging.info(filePath)
    return filePath


def checkFileList():
    if not os.path.exists('export_data'):
        logging.info("No folder with name export_data")
    else:
        onlyfiles = [f for f in os.listdir('export_data') if isfile(join('export_data', f))]
        return onlyfiles


# Main function to run the script
if __name__ == '__main__':
    c8y = ArgumentsAndCredentialsHandler.c8yPlatformConnection()
    MODE, DATA_TYPE, ACTION, DEVICE_NAME = ArgumentsAndCredentialsHandler.argumentsParser()
    if ACTION == "export":
        createTo = datetime.now().replace(tzinfo=timezone.utc)
        createFrom = createTo - timedelta(weeks=4)
        logging.info(f"Export data which is created after/from: {createFrom}")
        logging.info(f"and created before/to: {createTo}")
        if MODE == 'all':
            exportAllProfileData(c8y, DATA_TYPE, createFrom, createTo)
        elif MODE == 'specific':
            exportSpecificProfileData(c8y, DATA_TYPE, createFrom, createTo, DEVICE_NAME)

    elif ACTION == "import":
        listOfFiles = checkFileList()
        try:
            listToStringWithNewLine = "\n".join(listOfFiles)
            logging.info("Which file do you want to upload?")
            logging.info(listToStringWithNewLine)
        except:
            logging.info(f"No files to upload")
        # TODO: Implement import function
