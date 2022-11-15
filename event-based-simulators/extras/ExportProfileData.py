import json, logging, os, sys, requests

import ArgumentsAndCredentialsHandler, Environment

from datetime import datetime, timedelta, timezone

# Global variables and constants
logTimeFormat = "%Y%m%d%H%M%S_%f"
C8Y_PROFILE_GROUP = 'c8y_EventBasedSimulatorProfile'
C8Y_OEE_SIMULATOR_DEVICES_GROUP = "c8y_EventBasedSimulator"
DATA_TYPE, DEVICE_ID, CREATE_FROM, CREATE_TO, LOG_LEVEL, c8y = ArgumentsAndCredentialsHandler.handleExportArguments()
####################################################
# Setup Log
file_log_level = logging.DEBUG
console_log_level = LOG_LEVEL
relativeFilePath = f"logs\export_{datetime.strftime(datetime.now(), logTimeFormat)}.log"
filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
fileLogger, consoleLogger = ArgumentsAndCredentialsHandler.setupLogger(fileLoggerName='ExportProfileData', consoleLoggerName='ConsoleExportProfileData', filePath=filePath, fileLogLevel=file_log_level, consoleLogLevel=console_log_level)
def logDebug(content):
  fileLogger.debug(content)
  consoleLogger.debug(content)
def logInfo(content):
  fileLogger.info(content)
  consoleLogger.info(content)
def logError(content):
  fileLogger.error(content)
  consoleLogger.error(content)
#####################################################
# Check if connection to tenant can be created
if ArgumentsAndCredentialsHandler.checkTenantConnection(c8y.base_url):
    logInfo(f"Connect to tenant {c8y.tenant_id} successfully")
else:
    logError(f"Connect to tenant {c8y.tenant_id} failed")
    sys.exit()
######################################################


def exportAllProfileDataFromChildDevices(createFrom, createTo):
    deviceCount = 0
    deviceManagedObject = c8y.device_inventory.select(type=C8Y_OEE_SIMULATOR_DEVICES_GROUP)
    for device in deviceManagedObject:
        deviceCount += 1
        logDebug(f"Found device '{device.name}', id: #{device.id}, owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        logDebug(f"List of {device.name}'s child devices: ")
        for childDevice in device.child_devices:
            ExportSpecificProfileDataWithDeviceId(createFrom=createFrom,createTo=createTo, deviceId=childDevice.id)

    if deviceCount == 0:
        logInfo(f"No device in tenant {c8y.tenant_id} found")


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
    logDebug(f"Search for {DATA_TYPE} data from device {deviceName}, id #{deviceId}")
    for device in c8y.device_inventory.select(name=deviceName):
        deviceCount += 1
        fileLogger.debug(f"Child device {device.name}, id #{device.id}")
        if DATA_TYPE == "alarms":
            exportAlarms(device, createFrom, createTo, filePath)
            appendDataToJsonFile([], filePath, 'measurements')
            fileLogger.debug(f"{DATA_TYPE.capitalize()} data is added to data file at {filePath}")
        elif DATA_TYPE == "measurements":
            # listing measurements of child device
            exportMeasurements(device, createFrom, createTo, filePath)
            appendDataToJsonFile([], filePath, 'alarms')
            fileLogger.debug(f"{DATA_TYPE.capitalize()} data is added to data file at {filePath}")
        else:
            exportAlarms(device, createFrom, createTo, filePath)
            exportMeasurements(device, createFrom, createTo, filePath)
            fileLogger.debug(f"Alarms and Measurements data is added to data file at {filePath}")

    if deviceCount == 0:
        fileLogger.info(f"No device with id {deviceId} found")
    return


def findDeviceNameById(deviceId, baseUrl):
    response = requests.get(f'{baseUrl}/inventory/managedObjects/{deviceId}',
                            headers=ArgumentsAndCredentialsHandler.C8Y_HEADERS)
    if not response.ok:
        logError(f"Connection to url '{baseUrl}/inventory/managedObjects/{deviceId}' failed. Check your parameters in environment file again")
        sys.exit()
    else:
        try:
            deviceName = response.json()['name']
        except:
            logError(f"Device #{deviceId} does not have name")
            sys.exit()

    return deviceName


def exportAlarms(device, createFrom, createTo, filePath):
    jsonAlarmsList = listAlarms(device, createFrom, createTo)
    appendDataToJsonFile(jsonAlarmsList, filePath, 'alarms')


def listAlarms(device, createFrom, createTo):
    jsonAlarmsList = []
    # Create a count variable as a json/dict key to save json data
    count = 0
    for alarm in c8y.alarms.select(source=device.id, created_after=createFrom, created_before=createTo):
        fileLogger.debug(f"Found alarm id #{alarm.id}, severity: {alarm.severity}, time: {alarm.time}, creation time: {alarm.creation_time}, update time : {alarm.updated_time}\n")
        count += 1
        jsonAlarmsList.append(alarm.to_json())
    return jsonAlarmsList


def exportMeasurements(device, createFrom, createTo, filePath):
    jsonMeasurementsList = listMeasurements(device, createFrom, createTo)
    appendDataToJsonFile(jsonMeasurementsList, filePath, 'measurements')


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
        logError(f"Connection to url '{baseUrl}/identity/globalIds/{deviceId}/externalIds' failed. Check your parameters in environment file again")
        sys.exit()
    else:
        return externalIdResponse


def checkDeviceExternalIdById(deviceId, baseUrl):
    externalIdResponse = getExternalIdReponse(deviceId, baseUrl)

    try:
        deviceExternalId = externalIdResponse.json()['externalIds'][0]['externalId']
        deviceExternalIdType = externalIdResponse.json()['externalIds'][0]['type']
        logInfo(f"Found external id: {deviceExternalId} with type: {deviceExternalIdType} for the device with id {deviceId}")
    except:
        logInfo(f"Could not find external id for the device with id {deviceId}")
        return None, None

    return deviceExternalId, deviceExternalIdType


def isExternalIdTypeEventBasedSimulatorProfile(deviceExternalIdType):
    if deviceExternalIdType == C8Y_PROFILE_GROUP:
        return True
    else:
        logInfo(f"The type {deviceExternalIdType} of external ID must be {C8Y_PROFILE_GROUP}")
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
        logDebug(f'CREATE_FROM and/or CREATE_TO were not set. Using default setup to export {Environment.PERIOD_TO_EXPORT}{Environment.TIME_UNIT} ago from now')

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
