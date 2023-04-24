import logging, urllib, json, requests, os, sys
import ArgumentsAndCredentialsHandler

from urllib3.exceptions import InsecureRequestWarning
from os.path import isfile, join
from datetime import datetime

# Data File Folder
EXPORT_DATA_FOLDER = 'export_data'
# Global variables and constants
timeFormat = "%Y-%m-%dT%H:%M:%S.%fZ"
logTimeFormat = "%Y%m%d%H%M%S_%f"
file_log_level = logging.DEBUG
C8Y_PROFILE_GROUP = 'c8y_EventBasedSimulatorProfile'
json_filename_list_to_import, console_log_level, c8y, password, verifySslCertificate = ArgumentsAndCredentialsHandler.HandleImportArguments()
C8Y_HEADERS, MEASUREMENTS_HEADERS = ArgumentsAndCredentialsHandler.SetupHeadersForAPIRequest(tenant_id=c8y.tenant_id, username= c8y.username, password=password)
####################################################
# Setup Log
consoleLogger = ArgumentsAndCredentialsHandler.SetupLogger(console_logger_name='ConsoleImportProfileData', console_log_level=console_log_level)
#####################################################

session = requests.Session()
session.verify = verifySslCertificate

# Check if connection to tenant can be created
tenantConnectionResponse = ArgumentsAndCredentialsHandler.CheckTenantConnection(baseUrl=c8y.base_url, C8Y_HEADERS=C8Y_HEADERS, session=session)
if tenantConnectionResponse:
    consoleLogger.info(f"Connected successfully to tenant \"{c8y.tenant_id}\" with user {c8y.username} on {c8y.base_url}")
else:
    if tenantConnectionResponse is None:
        consoleLogger.error(f"Wrong base url setup. Check again the URL: {c8y.base_url}")
    else:
        consoleLogger.error(tenantConnectionResponse.json())
    consoleLogger.error(f"Connection to tenant \"{c8y.tenant_id}\" failed with user {c8y.username} on {c8y.base_url}")
    sys.exit(1)
######################################################


def GetDeviceIdByExternalId(external_id):
    consoleLogger.info(f'Searching for device with ext ID {external_id}')
    encoded_external_id = EncodeUrl(external_id)
    response = session.get(f'{c8y.base_url}/identity/externalIds/{C8Y_PROFILE_GROUP}/{encoded_external_id}', headers=C8Y_HEADERS)
    if response.ok:
        device_id = response.json()['managedObject']['id']
        consoleLogger.info(f'Device({device_id}) has been found by its external id "{C8Y_PROFILE_GROUP}/{external_id}".')
        return device_id
    consoleLogger.warning(response.json())
    return None


def CreateAlarm(alarm):
    response = session.post(f'{c8y.base_url}/alarm/alarms', headers=C8Y_HEADERS, data=json.dumps(alarm))
    if response.ok:
        return response.json()
    consoleLogger.warning(response.json())
    return None


def CreateMeasurements(measurements):
    response = session.post(f'{c8y.base_url}/measurement/measurements', headers=MEASUREMENTS_HEADERS, data=json.dumps(measurements))
    if response.ok:
        return response.json()
    consoleLogger.warning(response.json())
    return None


def GetTimeDifference(object, key):
    creation_Time = datetime.strptime(object[key], timeFormat)
    now = datetime.utcnow()
    return (now - creation_Time)


def DeleteUnwantedAlarmFields(alarm):
    del alarm['lastUpdated']
    del alarm['count']
    del alarm['creationTime']
    del alarm['history']
    return alarm


def ImportAlarms(alarms, id):
    consoleLogger.info(f'Importing [{len(alarms)}] alarms for {id}')
    timeShift = GetTimeDifference(alarms[0], 'creationTime')
    for alarm in alarms:
        alarm['source']['id'] = id
        alarm = DeleteUnwantedAlarmFields(alarm)
        alarm['time'] = (datetime.strptime(alarm['time'], timeFormat) + timeShift).strftime(timeFormat)
        CreateAlarm(alarm)
    consoleLogger.info("Alarms import finished")


def ImportMeasurements(measurements, id):
    consoleLogger.info(f'Importing [{len(measurements)}] measurements for {id}')
    timeShift = GetTimeDifference(measurements[len(measurements) - 1], 'time')
    for i in range(len(measurements)):
        measurements[i]['time'] = (datetime.strptime(measurements[i]['time'], timeFormat) + timeShift).strftime(timeFormat)
        measurements[i]['source']['id'] = id
    measurements_object = {
        "measurements": measurements
    }
    CreateMeasurements(measurements=measurements_object)
    consoleLogger.info("Measurements import finished")


def LoadFile(filePath):
    try:
        with open(filePath) as f_obj:
            return json.load(f_obj)
    except Exception as e:
        consoleLogger.error(e, type(e))
        return {}


def ExtractExternalIdFromFilePath(filepath):
    filename = os.path.basename(filepath)
    return filename.split('.')[0]


def EncodeUrl(url):
    encodedUrl = urllib.parse.quote(url.encode('utf8'))
    return encodedUrl


def CheckFileList(filepath):
    list_of_files = []
    if not os.path.exists(filepath):
        consoleLogger.debug(f"No data folder with name {filepath} found")
    else:
        #listOfFiles = [file for file in os.listdir(filePath) if isfile(join(filePath, file))]
        for file in os.listdir(filepath):
            if isfile(join(filepath, file)):
                list_of_files.append(file)
        return list_of_files


def ReplaceFileNameWithFilePathInList(list_of_files):
    list_of_file_paths = []
    for data_file_name in list_of_files:
        data_file_path = EXPORT_DATA_FOLDER + "/" + data_file_name
        list_of_file_paths.append(data_file_path)
    return list_of_file_paths


def AddJsonExtensionToFileNameList(list_of_filenames):
    list_of_file_names_with_extension = []
    for filename in list_of_filenames:
        filename = f'{filename}.json'
        list_of_file_names_with_extension.append(filename)
    return list_of_file_names_with_extension


if __name__ == '__main__':
    if json_filename_list_to_import:
        listOfFileNamesWithExtension = AddJsonExtensionToFileNameList(list_of_filenames=json_filename_list_to_import)
        listOfFilePaths = ReplaceFileNameWithFilePathInList(list_of_files=listOfFileNamesWithExtension)
    else:
        listOfFiles = CheckFileList(filepath=EXPORT_DATA_FOLDER)
        listOfFilePaths = ReplaceFileNameWithFilePathInList(list_of_files=listOfFiles)

    for filePath in listOfFilePaths:
        file_data = LoadFile(filePath)
        external_id = ExtractExternalIdFromFilePath(filePath)
        consoleLogger.debug(f'external id: {external_id}')
        alarms = file_data.get("alarms", [])
        measurements = file_data.get("measurements", [])
        id = GetDeviceIdByExternalId(external_id=external_id)

        if (id is not None):
            requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
            if len(alarms) > 0:
                ImportAlarms(alarms=alarms, id=id)
            else:
                consoleLogger.info("No Alarms to import")
            if len(measurements) > 0:
                ImportMeasurements(measurements=measurements, id=id)
            else:
                consoleLogger.info("No Measurements to import")
