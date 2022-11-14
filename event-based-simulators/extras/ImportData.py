import logging, urllib, json, requests, os, sys

import ArgumentsAndCredentialsHandler

from datetime import datetime

timeFormat = "%Y-%m-%dT%H:%M:%S.%fZ"
logTimeFormat = "%Y%m%d%H%M%S_%f"
file_log_level = logging.DEBUG
C8Y_PROFILE_GROUP = 'c8y_EventBasedSimulatorProfile'
filepath, console_log_level, c8y = ArgumentsAndCredentialsHandler.handleImportArguments()
####################################################
relativeFilePath = f"logs\import_{datetime.strftime(datetime.now(), logTimeFormat)}.log"
filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
fileLogger, consoleLogger = ArgumentsAndCredentialsHandler.setupLogger(fileLoggerName='ImportProfileData', consoleLoggerName='ConsoleImportProfileData', filePath=filePath, fileLogLevel=file_log_level, consoleLogLevel=console_log_level)
#####################################################
# Check if connection to tenant can be created
if ArgumentsAndCredentialsHandler.checkTenantConnection(c8y.base_url):
    fileLogger.info(f"Connect to tenant {c8y.tenant_id} successfully")
    consoleLogger.info(f"Connect to tenant {c8y.tenant_id} successfully")
else:
    fileLogger.error(f"Connect to tenant {c8y.tenant_id} failed")
    consoleLogger.error(f"Connect to tenant {c8y.tenant_id} failed")
    sys.exit()
######################################################

def getDeviceIdByExternalId(external_id):
    fileLogger.info(f'Searching for device with ext ID {external_id}')
    consoleLogger.info(f'Searching for device with ext ID {external_id}')
    encoded_external_id = encodeUrl(external_id)
    response = requests.get(
        f'{c8y.base_url}/identity/externalIds/{C8Y_PROFILE_GROUP}/{encoded_external_id}', headers=ArgumentsAndCredentialsHandler.C8Y_HEADERS)
    if response.ok:
        device_id = response.json()['managedObject']['id']
        fileLogger.info(f'Device({device_id}) has been found by its external id "{C8Y_PROFILE_GROUP}/{external_id}".')
        consoleLogger.info(f'Device({device_id}) has been found by its external id "{C8Y_PROFILE_GROUP}/{external_id}".')
        return device_id
    fileLogger.warning(
        f'No device has been found for the external id "{C8Y_PROFILE_GROUP}/{external_id}".')
    return None


def createAlarm(alarm):
    response = requests.post(
        f'{c8y.base_url}/alarm/alarms', headers=ArgumentsAndCredentialsHandler.C8Y_HEADERS, data=json.dumps(alarm))
    if response.ok:
        return response.json()
    fileLogger.warning(response)
    return None


def createMeasurements(measurements):
    response = requests.post(f'{c8y.base_url}/measurement/measurements',
                             headers=ArgumentsAndCredentialsHandler.MEASUREMENTS_HEADERS, data=json.dumps(measurements))
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


def load(filename):
    try:
        with open(filename) as f_obj:
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


if __name__ == '__main__':
    file_data = load(filepath)
    external_id = extract_ext_id_from_filepath(filepath)
    fileLogger.debug(f'external id: {extract_ext_id_from_filepath(filepath)}')
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
        fileLogger.info("No Measurements to import")
