import logging, urllib, json, requests, os, sys
from os.path import isfile, join

import ArgumentsAndCredentialsHandler

from datetime import datetime

# Global variables and constants
timeFormat = "%Y-%m-%dT%H:%M:%S.%fZ"
logTimeFormat = "%Y%m%d%H%M%S_%f"
file_log_level = logging.DEBUG
C8Y_PROFILE_GROUP = 'c8y_EventBasedSimulatorProfile'
json_filename_list_to_import, console_log_level, c8y = ArgumentsAndCredentialsHandler.handleImportArguments()
C8Y_HEADERS, MEASUREMENTS_HEADERS = ArgumentsAndCredentialsHandler.setupHeadersForAPIRequest(tenant_id=c8y.tenant_id, username= c8y.username, password=c8y.password)
####################################################
# Setup Log
relativeFilePath = f"logs\import_{datetime.strftime(datetime.now(), logTimeFormat)}.log"
logFilePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
fileLogger, consoleLogger = ArgumentsAndCredentialsHandler.setupLogger(fileLoggerName='ImportProfileData', consoleLoggerName='ConsoleImportProfileData', filePath=logFilePath, fileLogLevel=file_log_level, consoleLogLevel=console_log_level)
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
if ArgumentsAndCredentialsHandler.checkTenantConnection(baseUrl=c8y.base_url, C8Y_HEADERS=C8Y_HEADERS):
    logInfo(f"Connect to tenant {c8y.tenant_id} successfully")
else:
    logError(f"Connect to tenant {c8y.tenant_id} failed")
    sys.exit()
######################################################


def getDeviceIdByExternalId(external_id):
    logInfo(f'Searching for device with ext ID {external_id}')
    encoded_external_id = encodeUrl(external_id)
    response = requests.get(
        f'{c8y.base_url}/identity/externalIds/{C8Y_PROFILE_GROUP}/{encoded_external_id}', headers=C8Y_HEADERS)
    if response.ok:
        device_id = response.json()['managedObject']['id']
        logInfo(f'Device({device_id}) has been found by its external id "{C8Y_PROFILE_GROUP}/{external_id}".')
        return device_id
    fileLogger.warning(
        f'No device has been found for the external id "{C8Y_PROFILE_GROUP}/{external_id}".')
    return None


def createAlarm(alarm):
    response = requests.post(
        f'{c8y.base_url}/alarm/alarms', headers=C8Y_HEADERS, data=json.dumps(alarm))
    if response.ok:
        return response.json()
    fileLogger.warning(response)
    return None


def createMeasurements(measurements):
    response = requests.post(f'{c8y.base_url}/measurement/measurements',
                             headers=MEASUREMENTS_HEADERS, data=json.dumps(measurements))
    if response.ok:
        return response.json()
    fileLogger.warning(response)
    return None


def getTimeDifference(object, key):
    creation_Time = datetime.strptime(object[key], timeFormat)
    now = datetime.utcnow()
    return (now - creation_Time)


def deleteUnwantedFields(alarm):
    del alarm['lastUpdated']
    del alarm['count']
    del alarm['creationTime']
    del alarm['history']
    return alarm


def importAlarms(alarms, id):
    fileLogger.debug('Importing all alarms')
    fileLogger.debug(f'Alarms:{alarms}')
    timeShift = getTimeDifference(alarms[0], 'creationTime')
    for alarm in alarms:
        alarm['source']['id'] = id
        alarm = deleteUnwantedFields(alarm)
        alarm['time'] = (datetime.strptime(
            alarm['time'], timeFormat) + timeShift).strftime(timeFormat)
        fileLogger.debug(f'Posting Alarm for device {id}: {alarm}')
        createAlarm(alarm)
    logInfo("Alarms import finished")


def importMeasurements(measurements, id):
    fileLogger.debug('Importing all measurements')
    fileLogger.debug(f'Measurements: {measurements}')
    timeShift = getTimeDifference(measurements[len(measurements) - 1], 'time')
    for i in range(len(measurements)):
        measurements[i]['time'] = (datetime.strptime(
            measurements[i]['time'], timeFormat) + timeShift).strftime(timeFormat)
        measurements[i]['source']['id'] = id
    measurements_object = {
        "measurements": measurements
    }
    createMeasurements(measurements=measurements_object)
    logInfo("Measurements import finished")


def loadFile(filePath):
    try:
        with open(filePath) as f_obj:
            return json.load(f_obj)
    except Exception as e:
        fileLogger.error(e, type(e))
        return {}


def extract_ext_id_from_filepath(filepath):
    filename = os.path.basename(filepath)
    return filename.split('.')[0]


def encodeUrl(url):
    encodedUrl = urllib.parse.quote(url.encode('utf8'))
    return encodedUrl


def checkFileList(filepath):
    list_of_files = []
    if not os.path.exists(filepath):
        consoleLogger.debug(f"No data folder with name {filepath} found")
    else:
        #listOfFiles = [file for file in os.listdir(filePath) if isfile(join(filePath, file))]
        for file in os.listdir(filepath):
            if isfile(join(filepath, file)):
                list_of_files.append(file)
        return list_of_files


def replaceFileNameWithFilePathInList(list_of_files):
    list_of_file_paths = []
    for data_file_name in list_of_files:
        data_file_path = 'export_data' + "\ ".strip() + data_file_name
        list_of_file_paths.append(data_file_path)
    return list_of_file_paths


def addJsonExtensionToFileNameList(list_of_filenames):
    list_of_file_names_with_extension = []
    for filename in list_of_filenames:
        filename = f'{filename}.json'
        list_of_file_names_with_extension.append(filename)
    return list_of_file_names_with_extension


if __name__ == '__main__':
    if json_filename_list_to_import:
        listOfFileNamesWithExtension = addJsonExtensionToFileNameList(list_of_filenames=json_filename_list_to_import)
        listOfFilePaths = replaceFileNameWithFilePathInList(list_of_files=listOfFileNamesWithExtension)
    else:
        listOfFiles = checkFileList(filepath='export_data')
        listOfFilePaths = replaceFileNameWithFilePathInList(list_of_files=listOfFiles)

    for filePath in listOfFilePaths:
        file_data = loadFile(filePath)
        external_id = extract_ext_id_from_filepath(filePath)
        fileLogger.debug(f'external id: {external_id}')
        alarms = file_data.get("alarms", [])
        measurements = file_data.get("measurements", [])
        id = getDeviceIdByExternalId(external_id=external_id)

        if len(alarms) > 0:
            importAlarms(alarms=alarms, id=id)
        else:
            fileLogger.info("No Alarms to import")
        if len(measurements) > 0:
            importMeasurements(measurements=measurements, id=id)
        else:
            logInfo("No Measurements to import")
