import json
import os
from datetime import datetime

import ArgumentsAndCredentialsHandler


def exportAllProfileData(c8y, DATA_TYPE, createFrom, createTo, filePath):
    # Loop through the list of device in Device management
    for device in c8y.device_inventory.select(type="c8y_EventBasedSimulator"):
        print(f"Found device '{device.name}', id: #{device.id}, "
              f"owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        print(f"List of {device.name}'s child devices: ")
        for childDevice in device.child_devices:
            print(f"Child device {childDevice.name}, id #{childDevice.id}")
            if DATA_TYPE == "alarms":
                listAlarms(c8y, childDevice, createFrom, createTo, filePath)
            elif DATA_TYPE == "measurements":
                # listing measurements of child device
                listMeasurements(c8y, childDevice, createFrom, createTo, filePath)


def exportSpecificProfileData(c8y, DATA_TYPE, createFrom, createTo, filePath):
    print(f"Enter device name to search for {DATA_TYPE} data: ")
    deviceName = input()
    deviceCount = 0
    for device in c8y.device_inventory.select(type="c8y_EventBasedSimulator", name=deviceName):
        print(f"Found device '{device.name}', id: #{device.id}, "
              f"owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        deviceCount += 1
        print(f"List of {device.name}'s child devices: ")
        for childDevice in device.child_devices:
            print(f"Child device {childDevice.name}, id #{childDevice.id}")
            if DATA_TYPE == "alarms":
                listAlarms(c8y, childDevice, createFrom, createTo, filePath)
            elif DATA_TYPE == "measurements":
                # listing measurements of child device
                listMeasurements(c8y, childDevice, createFrom, createTo, filePath)

    if deviceCount == 0:
        print(f"No device with name {deviceName} found")


def listAlarms(c8y, childDevice, createFrom, createTo, filePath):
    count = 0
    for alarm in c8y.alarms.select(source=childDevice.id, created_after=createFrom, created_before=createTo):
        print(
            f"Found alarm id #{alarm.id}, severity: {alarm.severity}, time: {alarm.time}, creation time: {alarm.creation_time}, update time : {alarm.updated_time}\n")
        print(f"{alarm.text}\n")
        print(f"fragments: {list(alarm.keys())}\n")
        count += 1
        appendDataToJsonFile(alarm.to_json(), filePath, count)

def listMeasurements(c8y, childDevice, createFrom, createTo, filePath):
    # Create a count variable as a json/dict key to save json data
    count = 0
    for measurement in c8y.measurements.select(source=childDevice.id, after=createFrom, before=createTo):
        print(f"Found measurement id #{measurement.id}\n, type: {measurement.type}\n")
        count += 1
        appendDataToJsonFile(measurement.to_json(), filePath, count)

def appendDataToJsonFile(jsonData, filePath, count, json_data={}):
    try:
        # Load content of existing json data file
        with open(filePath, 'r') as f:
            json_data = json.load(f)
            print(json_data)
    except:
        print(f"Create new data json file {filePath}")

    # Create new json file or add data to an existing json file
    with open(filePath, 'w') as f:
        json_data[f"{count}"] = jsonData
        json.dump(json_data, f, indent=2)
        print("New data is added to file")


def createFilePathFromDateTime(DATA_TYPE):
    # Check if folder containing data files exists and make one if not
    if not os.path.exists('export_data'):
        os.makedirs('export_data')
    # dd/mm/YY H:M:S
    dateTimeString = datetime.now().strftime(f"{DATA_TYPE}_%d_%m_%Y_%H_%M_%S")
    relativeFilePath = f'export_data\{dateTimeString}.json'
    filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
    return filePath


# Main function to run the script
if __name__ == '__main__':
    c8y, MODE, DATA_TYPE = ArgumentsAndCredentialsHandler.c8yPlatformConnection()

    print("Export data which is created after/from: \n(example input: 2022-10-28T15:52:19.605Z)")
    createFrom = input()
    print("and created before/to: \n(example input: 2022-10-28T16:02:02.310Z)")
    createTo = input()
    filePath = createFilePathFromDateTime(DATA_TYPE)
    if MODE == 'all':
        exportAllProfileData(c8y, DATA_TYPE, createFrom, createTo, filePath)
    elif MODE == 'specific':
        exportSpecificProfileData(c8y, DATA_TYPE, createFrom, createTo, filePath)
