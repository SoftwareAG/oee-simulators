import logging

import ArgumentsAndCredentialsHandler
import Environment
import base64
import json
import requests
import os
from datetime import datetime

import sys, getopt

log_format = '[%(asctime)s] [%(levelname)s] - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=log_format)
log = logging.getLogger('ImportData')
c8y = ArgumentsAndCredentialsHandler.c8yPlatformConnection()
format = "%Y-%m-%dT%H:%M:%S.%fZ"

C8Y_SIMULATORS_GROUP = 'c8y_EventBasedSimulator'


user_and_pass_bytes = base64.b64encode(
    (Environment.C8Y_TENANT + "/" + Environment.C8Y_USER + ':' + Environment.C8Y_PASSWORD).encode('ascii'))  # bytes
user_and_pass = user_and_pass_bytes.decode('ascii')  # decode to str

C8Y_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Basic ' + user_and_pass
}

def getDeviceIdByExternalId(external_id):
    log.info(f'Searching for device with ext ID {external_id}')
    response = requests.get(f'{Environment.C8Y_BASE}/identity/externalIds/{C8Y_SIMULATORS_GROUP}/{external_id}', headers=C8Y_HEADERS)
    if response.ok:
        device_id = response.json()['managedObject']['id']
        log.info(f'Device({device_id}) has been found by its external id "{C8Y_SIMULATORS_GROUP}/{external_id}".')
        return device_id
    log.warning(f'No device has been found for the external id "{C8Y_SIMULATORS_GROUP}/{external_id}".')
    return None

def postAlarm(alarm):
    response = requests.post(f'{Environment.C8Y_BASE}/alarm/alarms', headers=C8Y_HEADERS, data=json.dumps(alarm))
    if response.ok:
        return response.json()
    log.warn(response)
    return None

def getTimeDifference(alarms):
    creation_Time = datetime.strptime(alarms[0]['creationTime'], format)
    now = datetime.utcnow()
    return (now - creation_Time)

def replaceID(alarms, id):
    for alarm in alarms:
        alarm['source']['id'] = id
    return alarms

def deleteUnwantedFields(alarm):
    del alarm['lastUpdated']
    del alarm['count']
    del alarm['creationTime']
    del alarm['history']
    return alarm

def importAlarms(alarms, external_id):
    id = getDeviceIdByExternalId(external_id)
    timeShift = getTimeDifference(alarms)
    alarms = replaceID(alarms, id)
    for alarm in alarms:
        alarm = deleteUnwantedFields(alarm)
        alarm['time'] = (datetime.strptime(alarm['time'], format) + timeShift).strftime(format)
        log.debug(f'Posting Alarm for device {id}: {alarm}')
        postAlarm(alarm)

    #get device by external id
    #add alarms for this device
    #replace ids with device id
    log.info('Importing all alarms')

def load(filename):
    try:
        with open(filename) as f_obj:
            return json.load(f_obj)
    except Exception as e:
        print(e, type(e))
        return {}

def extract_ext_id_from_filepath(filepath):
    filename = os.path.basename(filepath)
    return filename[:len(filename)-5]
    
def main(argv):
    filepath = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile="])
    except getopt.GetoptError:
        log.error('No file input presented. Use -i filepath')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            log.info('test.py -i <inputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            filepath = arg

    
    log.info(f'Your file: {filepath}')
    file_data = load(filepath)
    external_id = extract_ext_id_from_filepath(filepath)
    log.info(f'external id: {extract_ext_id_from_filepath(filepath)}')
    alarms = file_data.get("alarms", [])
    importAlarms(alarms= file_data, external_id=external_id)

    #add import for measurements
    
if __name__ == "__main__":
   main(sys.argv[1:])