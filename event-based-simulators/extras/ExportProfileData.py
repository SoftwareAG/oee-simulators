import json, logging, os, sys, requests

import ArgumentsAndCredentialsHandler, Environment

from datetime import datetime, timedelta, timezone

logTimeFormat = "%Y%m%d%H%M%S_%f"
C8Y_PROFILE_GROUP = 'c8y_EventBasedSimulatorProfile'
C8Y_OEE_SIMULATOR_DEVICES_GROUP = "c8y_EventBasedSimulator"
c8y = ArgumentsAndCredentialsHandler.c8yPlatformConnection()
DATA_TYPE, DEVICE_ID, CREATE_FROM, CREATE_TO, LOG_LEVEL = ArgumentsAndCredentialsHandler.handleExportArguments()
####################################################
file_log_level = logging.DEBUG
console_log_level = LOG_LEVEL
relativeFilePath = f"logs\export_{datetime.strftime(datetime.now(), logTimeFormat)}.log"
filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
fileLogger, consoleLogger = ArgumentsAndCredentialsHandler.setupLogger(fileLoggerName='ExportProfileData', consoleLoggerName='ConsoleExportProfileData', filePath=filePath, fileLogLevel=file_log_level, consoleLogLevel=console_log_level)
#####################################################
# Check if connection to tenant can be created
try:
    requests.get(f'{c8y.base_url}/tenant/currentTenant', headers=ArgumentsAndCredentialsHandler.C8Y_HEADERS)
    fileLogger.info(f"Connect to tenant {c8y.tenant_id} successfully")
except:
    fileLogger.error(f"Connect to tenant {c8y.tenant_id} failed")
    consoleLogger.error(f"Connect to tenant {c8y.tenant_id} failed")
    sys.exit()
######################################################


def exportAllProfileDataFromChildDevices(createFrom, createTo):
    deviceCount = 0
    deviceManagedObject = c8y.device_inventory.select(type=C8Y_OEE_SIMULATOR_DEVICES_GROUP)
    for device in deviceManagedObject:
        deviceCount += 1
        fileLogger.debug(f"Found device '{device.name}', id: #{device.id}, "
                    f"owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        consoleLogger.debug(f"Found device '{device.name}', id: #{device.id} ")
        fileLogger.debug(f"List of {device.name}'s child devices: ")
        consoleLogger.debug(f"List of {device.name}'s child devices: ")
        for childDevice in device.child_devices:
            ExportSpecificProfileDataWithDeviceId(createFrom=createFrom,createTo=createTo, deviceId=childDevice.id)

    if deviceCount == 0:
        fileLogger.info(f"No device in tenant {c8y.tenant_id} found")
        consoleLogger.info(f"No device in tenant {c8y.tenant_id} found")


def ExportSpecificProfileDataWithDeviceId(createFrom, createTo, deviceId):
    deviceName = findDeviceNameById(deviceId, c8y.base_url)
    deviceCount = 0
    deviceExternalId, deviceExternalIdType = checkDeviceExternalIdById(deviceId, c8y.base_url)
    if not deviceExternalId:
        return
    if isExternalIdTypeEventBasedSimulatorProfile(deviceExternalIdType):
        filePath = createFilePath(Id=deviceExternalId)
    else:
        return
    fileLogger.debug(f"Search for {DATA_TYPE} data from device {deviceName}, id #{deviceId} ")
    consoleLogger.debug(f"Search for {DATA_TYPE} data from device {deviceName}, id #{deviceId} ")
    for device in c8y.device_inventory.select(name=deviceName):
        deviceCount += 1
        fileLogger.debug(f"Child device {device.name}, id #{device.id}")
        if DATA_TYPE == "alarms":
            jsonAlarmsList = listAlarms(device, createFrom, createTo)
            appendDataToJsonFile(jsonAlarmsList, filePath, DATA_TYPE)
            appendDataToJsonFile([], filePath, 'measurements')
            fileLogger.debug(f"{DATA_TYPE.capitalize()} data is added to data file at {filePath}")
        elif DATA_TYPE == "measurements":
            # listing measurements of child device
            jsonMeasurementsList = listMeasurements(device, createFrom, createTo)
            appendDataToJsonFile(jsonMeasurementsList, filePath, DATA_TYPE)
            appendDataToJsonFile([], filePath, 'alarms')
            fileLogger.debug(f"{DATA_TYPE.capitalize()} data is added to data file at {filePath}")
        else:
            jsonAlarmsList = listAlarms(device, createFrom, createTo)
            appendDataToJsonFile(jsonAlarmsList, filePath, 'alarms')
            jsonMeasurementsList = listMeasurements(device, createFrom, createTo)
            appendDataToJsonFile(jsonMeasurementsList, filePath, 'measurements')
            fileLogger.debug(f"Alarms and Measurements data is added to data file at {filePath}")

    if deviceCount == 0:
        fileLogger.info(f"No device with id {deviceId} found")
    return


def findDeviceNameById(deviceId, baseUrl):
    response = requests.get(f'{baseUrl}/inventory/managedObjects/{deviceId}',
                            headers=ArgumentsAndCredentialsHandler.C8Y_HEADERS)
    if not response.ok:
        fileLogger.error(f"Connection to url '{baseUrl}/inventory/managedObjects/{deviceId}' failed. Check your parameters in environment file again")
        consoleLogger.error(f"Connection to url '{baseUrl}/inventory/managedObjects/{deviceId}' failed. Check your parameters in environment file again")
        sys.exit()
    else:
        try:
            deviceName = response.json()['name']
        except:
            fileLogger.error(f"Device #{deviceId} does not have name")
            consoleLogger.error(f"Device #{deviceId} does not have name")
            sys.exit()

    return deviceName


def listAlarms(device, createFrom, createTo):
    jsonAlarmsList = []
    # Create a count variable as a json/dict key to save json data
    count = 0
    for alarm in c8y.alarms.select(source=device.id, created_after=createFrom, created_before=createTo):
        fileLogger.debug(f"Found alarm id #{alarm.id}, severity: {alarm.severity}, time: {alarm.time}, creation time: {alarm.creation_time}, update time : {alarm.updated_time}\n")
        count += 1
        jsonAlarmsList.append(alarm.to_json())
    return jsonAlarmsList


def listMeasurements(device, createFrom, createTo):
    jsonMeasurementsList = []
    # Create a count variable as a json/dict key to save json data
    count = 0
    for measurement in c8y.measurements.select(source=device.id, after=createFrom, before=createTo):
        fileLogger.debug(f"Found measurement id #{measurement.id}\n")
        count += 1
        jsonMeasurementsList.append(measurement.to_json())
    return jsonMeasurementsList


def appendDataToJsonFile(jsonDataList, filePath, data_type, json_data={}):
    # Create new json file or add data to an existing json file
    with open(filePath, 'w') as f:
        json_data[f"{data_type}"] = jsonDataList
        json.dump(json_data, f, indent=2)


def getExternalIdReponse(deviceId, baseUrl):
    externalIdResponse = requests.get(f'{baseUrl}/identity/globalIds/{deviceId}/externalIds',
                                      headers=ArgumentsAndCredentialsHandler.C8Y_HEADERS)
    if not externalIdResponse.ok:
        fileLogger.error(f"Connection to url '{baseUrl}/identity/globalIds/{deviceId}/externalIds' failed. Check your parameters in environment file again")
        consoleLogger.error(f"Connection to url '{baseUrl}/identity/globalIds/{deviceId}/externalIds' failed. Check your parameters in environment file again")
        sys.exit()
    else:
        return externalIdResponse


def checkDeviceExternalIdById(deviceId, baseUrl):
    externalIdResponse = getExternalIdReponse(deviceId, baseUrl)

    try:
        deviceExternalId = externalIdResponse.json()['externalIds'][0]['externalId']
        deviceExternalIdType = externalIdResponse.json()['externalIds'][0]['type']
        fileLogger.info(f"Found external id: {deviceExternalId} with type: {deviceExternalIdType} for the device with id {deviceId}")
        consoleLogger.info(f"Found external id: {deviceExternalId} with type: {deviceExternalIdType} for the device with id {deviceId}")
    except:
        fileLogger.info(f"Could not find external id for the device with id {deviceId}")
        consoleLogger.info(f"Could not find external id for the device with id {deviceId}")
        return None, None

    return deviceExternalId, deviceExternalIdType


def isExternalIdTypeEventBasedSimulatorProfile(deviceExternalIdType):
    if deviceExternalIdType == C8Y_PROFILE_GROUP:
        return True
    else:
        fileLogger.info(f"The type {deviceExternalIdType} of external ID must be {C8Y_PROFILE_GROUP}")
        consoleLogger.info(f"The type {deviceExternalIdType} of external ID must be {C8Y_PROFILE_GROUP}")
        return False


def createFilePath(Id):
    # Check if folder containing data files exists and make one if not
    if not os.path.exists('export_data'):
        os.makedirs('export_data')
    relativeFilePath = f'export_data\{Id}.json'
    filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
    fileLogger.debug(f"Created successfully file path: {filePath}")
    return filePath


def SetTimePeriodToExportData():
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
    createFrom, createTo = SetTimePeriodToExportData()
    fileLogger.info(f"Export data which is created after/from: {createFrom}")
    fileLogger.info(f"and created before/to: {createTo}")

    if not DEVICE_ID:
        exportAllProfileDataFromChildDevices(createFrom=createFrom, createTo=createTo)
    else:
        ExportSpecificProfileDataWithDeviceId(createFrom=createFrom, createTo=createTo, deviceId=DEVICE_ID)
