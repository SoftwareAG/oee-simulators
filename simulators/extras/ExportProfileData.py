import json, logging, os, sys, requests
import ArgumentsAndCredentialsHandler, Environment

from datetime import datetime, timedelta, timezone

# Global variables and constants
logTimeFormat = "%Y%m%d%H%M%S_%f"
C8Y_PROFILE_GROUP = 'c8y_EventBasedSimulatorProfile'
C8Y_OEE_SIMULATOR_DEVICES_GROUP = "c8y_EventBasedSimulator"
DATA_TYPE, DEVICE_ID_LIST, CREATE_FROM, CREATE_TO, LOG_LEVEL, c8y, PASSWORD = ArgumentsAndCredentialsHandler.HandleExportArguments()
C8Y_HEADERS, MEASUREMENTS_HEADERS = ArgumentsAndCredentialsHandler.SetupHeadersForAPIRequest(tenant_id=c8y.tenant_id, username= c8y.username, password=PASSWORD)
####################################################
# Setup Log
file_log_level = logging.DEBUG
console_log_level = LOG_LEVEL
consoleLogger = ArgumentsAndCredentialsHandler.SetupLogger(console_logger_name='ConsoleExportProfileData', console_log_level=console_log_level)
#####################################################

session = requests.Session()

# Check if connection to tenant can be created
tenantConnectionResponse = ArgumentsAndCredentialsHandler.CheckTenantConnection(baseUrl=c8y.base_url, C8Y_HEADERS=C8Y_HEADERS, session=session)
if tenantConnectionResponse:
    consoleLogger.info(f"Connect to tenant {c8y.tenant_id} successfully")
else:
    if tenantConnectionResponse is None:
        consoleLogger.error(f"Wrong base url setup. Check again the URL: {c8y.base_url}")
    else:
        consoleLogger.error(tenantConnectionResponse.json())
    consoleLogger.error(f"Connect to tenant {c8y.tenant_id} failed")
    sys.exit(1)
######################################################


def ExportAllProfileDataFromChildDevices(createFrom, createTo):
    deviceInTenantCount = 0
    deviceManagedObject = c8y.device_inventory.select(type=C8Y_OEE_SIMULATOR_DEVICES_GROUP)
    for device in deviceManagedObject:
        deviceInTenantCount += 1
        consoleLogger.debug(f"Found device '{device.name}', id: #{device.id}, owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        if len(device.child_devices) > 0:
            consoleLogger.debug(f"List of {device.name}'s child devices: ")
            for childDevice in device.child_devices:
                ExportSpecificProfileDataWithDeviceId(createFrom=createFrom,createTo=createTo, deviceId=childDevice.id)

    if deviceInTenantCount == 0:
        consoleLogger.info(f"No device in tenant {c8y.tenant_id} found")


def ExportSpecificProfileDataWithDeviceId(createFrom, createTo, deviceId):
    deviceName = FindDeviceNameById(deviceId, c8y.base_url)
    deviceExternalId, deviceExternalIdType = CheckDeviceExternalIdById(deviceId, c8y.base_url)
    if not deviceExternalId:
        return
    if IsExternalIdTypeEventBasedSimulatorProfile(deviceExternalIdType):
        filePath = CreateFilePath(Id=deviceExternalId)
    else:
        return
    consoleLogger.info(f"Search for {DATA_TYPE} data from device {deviceName}, id #{deviceId}")

    consoleLogger.info(f"Child device {deviceName}, id #{deviceId}")
    if DATA_TYPE == "alarms":
        ExportAlarms(deviceId, createFrom, createTo, filePath)
        AppendDataToJsonFile([], filePath, 'measurements')
        consoleLogger.debug(f"{DATA_TYPE.capitalize()} data is added to data file at {filePath}")
    elif DATA_TYPE == "measurements":
        # listing measurements of child device
        ExportMeasurements(deviceId, createFrom, createTo, filePath)
        AppendDataToJsonFile([], filePath, 'alarms')
        consoleLogger.debug(f"{DATA_TYPE.capitalize()} data is added to data file at {filePath}")
    else:
        ExportAlarms(deviceId, createFrom, createTo, filePath)
        ExportMeasurements(deviceId, createFrom, createTo, filePath)
        consoleLogger.debug(f"Alarms and Measurements data is added to data file at {filePath}")

    return


def FindDeviceNameById(deviceId, baseUrl):
    response = session.get(f'{baseUrl}/inventory/managedObjects/{deviceId}',
                            headers=C8Y_HEADERS)
    if not response.ok:
        consoleLogger.error(response.json())
        sys.exit(1)
    else:
        try:
            deviceName = response.json()['name']
        except:
            consoleLogger.error(f"Device #{deviceId} does not have name")
            sys.exit(1)

    return deviceName


def ExportAlarms(deviceId, createFrom, createTo, filePath):
    jsonAlarmsList = ListAlarms(deviceId, createFrom, createTo)
    AppendDataToJsonFile(jsonAlarmsList, filePath, 'alarms')


def ListAlarms(deviceId, createFrom, createTo):
    jsonAlarmsList = []
    for alarm in c8y.alarms.select(source=deviceId, created_after=createFrom, created_before=createTo):
        consoleLogger.debug(f"Found alarm id #{alarm.id}, severity: {alarm.severity}, time: {alarm.time}, creation time: {alarm.creation_time}, update time : {alarm.updated_time}\n")
        jsonAlarmsList.append(alarm.to_json())
    return jsonAlarmsList


def ExportMeasurements(deviceId, createFrom, createTo, filePath):
    jsonMeasurementsList = ListMeasurements(deviceId, createFrom, createTo)
    AppendDataToJsonFile(jsonMeasurementsList, filePath, 'measurements')


def ListMeasurements(deviceId, createFrom, createTo):
    jsonMeasurementsList = []
    for measurement in c8y.measurements.select(source=deviceId, after=createFrom, before=createTo):
        consoleLogger.debug(f"Found measurement id #{measurement.id}\n")
        jsonMeasurementsList.append(measurement.to_json())
    return jsonMeasurementsList


def AppendDataToJsonFile(jsonDataList, filePath, data_type, json_data={}):
    # Create new json file or add data to an existing json file
    with open(filePath, 'w') as f:
        json_data[f"{data_type}"] = jsonDataList
        json.dump(json_data, f, indent=2)


def GetExternalIdReponse(deviceId, baseUrl):
    externalIdResponse = session.get(f'{baseUrl}/identity/globalIds/{deviceId}/externalIds',
                                      headers=C8Y_HEADERS)
    if not externalIdResponse.ok:
        consoleLogger.error(externalIdResponse.json())
        sys.exit(1)
    else:
        return externalIdResponse


def CheckDeviceExternalIdById(deviceId, baseUrl):
    externalIdResponse = GetExternalIdReponse(deviceId, baseUrl)

    try:
        deviceExternalId = externalIdResponse.json()['externalIds'][0]['externalId']
        deviceExternalIdType = externalIdResponse.json()['externalIds'][0]['type']
        consoleLogger.info(f"Found external id: {deviceExternalId} with type: {deviceExternalIdType} for the device with id {deviceId}")
    except:
        consoleLogger.info(f"Could not find external id for the device with id {deviceId}")
        return None, None

    return deviceExternalId, deviceExternalIdType


def IsExternalIdTypeEventBasedSimulatorProfile(deviceExternalIdType):
    if deviceExternalIdType == C8Y_PROFILE_GROUP:
        return True
    else:
        consoleLogger.info(f"The type {deviceExternalIdType} of external ID must match with type {C8Y_PROFILE_GROUP}")
        return False


def CreateFilePath(Id):
    # Check if folder containing data files exists and make one if not
    if not os.path.exists('export_data'):
        os.makedirs('export_data')
    relativeFilePath = f'export_data\{Id}.json'
    filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
    consoleLogger.debug(f"Created successfully file path: {filePath}")
    return filePath


def SetTimePeriodToExportData():
    if not CREATE_FROM or CREATE_TO:
        consoleLogger.debug(f'CREATE_FROM and/or CREATE_TO were not set. Using default setup to export {Environment.PERIOD_TO_EXPORT} {Environment.TIME_UNIT} ago from now')

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
    consoleLogger.info(f"Export data which is created after/from: {createFrom}")
    consoleLogger.info(f"and created before/to: {createTo}")

    if not DEVICE_ID_LIST:
        ExportAllProfileDataFromChildDevices(createFrom=createFrom, createTo=createTo)
    else:
        for deviceId in DEVICE_ID_LIST:
            ExportSpecificProfileDataWithDeviceId(createFrom=createFrom, createTo=createTo, deviceId=deviceId)
