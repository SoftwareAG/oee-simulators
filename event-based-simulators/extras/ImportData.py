import logging

import ArgumentsAndCredentialsHandler
import base64
import json
import requests
import os
from datetime import datetime

log_format = '[%(asctime)s] [%(levelname)s] - %(message)s'
format = "%Y-%m-%dT%H:%M:%S.%fZ"
c8y_username, c8y_password, c8y_baseurl, c8y_tenant = '','','',''
C8Y_PROFILE_GROUP = 'c8y_EventBasedSimulatorProfile'

filepath, log_level, c8y_username, c8y_password, c8y_baseurl, c8y_tenant = ArgumentsAndCredentialsHandler.handleImportArguments()
log = logging.getLogger('ImportData')
logging.basicConfig(level=log_level, format=log_format)

user_and_pass_bytes = base64.b64encode(
    (c8y_tenant + "/" + c8y_username + ':' + c8y_password).encode('ascii'))  # bytes
user_and_pass = user_and_pass_bytes.decode('ascii')  # decode to str

C8Y_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Basic ' + user_and_pass
}

MEASUREMENTS_HEADERS = {
    'Content-Type': 'application/vnd.com.nsn.cumulocity.measurementcollection+json',
    'Accept': 'application/json',
    'Authorization': 'Basic ' + user_and_pass
}


def getDeviceIdByExternalId(external_id):
    log.info(f'Searching for device with ext ID {external_id}')
    response = requests.get(
        f'{c8y_baseurl}/identity/externalIds/{C8Y_PROFILE_GROUP}/{external_id}', headers=C8Y_HEADERS)
    if response.ok:
        device_id = response.json()['managedObject']['id']
        log.info(
            f'Device({device_id}) has been found by its external id "{C8Y_PROFILE_GROUP}/{external_id}".')
        return device_id
    log.warning(
        f'No device has been found for the external id "{C8Y_PROFILE_GROUP}/{external_id}".')
    return None


def createAlarm(alarm):
    response = requests.post(
        f'{c8y_baseurl}/alarm/alarms', headers=C8Y_HEADERS, data=json.dumps(alarm))
    if response.ok:
        return response.json()
    log.warning(response)
    return None


def createMeasurements(measurements):
    response = requests.post(f'{c8y_baseurl}/measurement/measurements',
                             headers=MEASUREMENTS_HEADERS, data=json.dumps(measurements))
    if response.ok:
        return response.json()
    log.warning(response)
    return None


def getTimeDifference(object, key):
    creation_Time = datetime.strptime(object[key], format)
    now = datetime.utcnow()
    return (now - creation_Time)


def deleteUnwantedFields(alarm):
    del alarm['lastUpdated']
    del alarm['count']
    del alarm['creationTime']
    del alarm['history']
    return alarm


def importAlarms(alarms, id):
    log.debug('Importing all alarms')
    log.debug(f'Alarms:{alarms}')
    timeShift = getTimeDifference(alarms[0], 'creationTime')
    for alarm in alarms:
        alarm['source']['id'] = id
        alarm = deleteUnwantedFields(alarm)
        alarm['time'] = (datetime.strptime(
            alarm['time'], format) + timeShift).strftime(format)
        log.debug(f'Posting Alarm for device {id}: {alarm}')
        createAlarm(alarm)


def importMeasurements(measurements, id):
    log.debug('Importing all measurements')
    log.debug(f'Measurements: {measurements}')
    timeShift = getTimeDifference(measurements[len(measurements)-1], 'time')
    for i in range(len(measurements)):
        measurements[i]['time'] = (datetime.strptime(
            measurements[i]['time'], format) + timeShift).strftime(format)
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
        log.error(e, type(e))
        return {}


def extract_ext_id_from_filepath(filepath):
    filename = os.path.basename(filepath)
    return filename.split('.')[0]


if __name__ == '__main__':
    file_data = load(filepath)
    external_id = extract_ext_id_from_filepath(filepath)
    log.debug(f'external id: {extract_ext_id_from_filepath(filepath)}')
    alarms = file_data.get("alarms", [])
    measurements = file_data.get("measurements", [])
    id = getDeviceIdByExternalId(external_id=external_id)

    if len(alarms) > 0:
        importAlarms(alarms=alarms, id=id)
    else:
        log.info("No Alarms to import")
    if len(measurements) > 0:
        importMeasurements(measurements=measurements, id=id)
    else:
        log.info("No Measurements to import")
