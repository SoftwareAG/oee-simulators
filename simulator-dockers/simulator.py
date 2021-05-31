# -*- coding: utf-8 -*-

import requests, base64, json, logging, os, time, sys
from random import randint
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

logging.info(os.environ)

'''
Start configuration
'''
C8Y_BASE = os.environ.get('C8Y_BASEURL')
C8Y_TENANT = os.environ.get('C8Y_TENANT')
C8Y_USER = os.environ.get('C8Y_USER')
C8Y_PASSWORD = os.environ.get('C8Y_PASSWORD')
C8Y_SIMULATOR_EXTERNAL_ID = 'myRandomSimulator'

'''
End configuration
'''

logging.info(C8Y_BASE)
logging.info(C8Y_TENANT)
logging.info(C8Y_USER)
logging.info(C8Y_PASSWORD)

C8Y_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Basic ' + base64.b64encode(C8Y_TENANT + '/' + C8Y_USER + ':' + C8Y_PASSWORD)
}

def sendMeasurement(measurement):
    response = requests.post(C8Y_BASE + '/measurement/measurements', headers=C8Y_HEADERS, data=json.dumps(measurement))
    return response.json()

def sendAlarm(alarm):
    response = requests.post(C8Y_BASE + '/alarm/alarms', headers=C8Y_HEADERS, data=json.dumps(alarm))
    return response.json()

def clearAlarm(alarmId):
    alarm = {
        'status': 'CLEARED'
    }
    response = requests.put(C8Y_BASE + '/alarm/alarms/' + str(alarmId), headers=C8Y_HEADERS, data=json.dumps(alarm))
    return response.json()


def sendEvent(event):
    response = requests.post(C8Y_BASE + '/event/events', headers=C8Y_HEADERS, data=json.dumps(event))
    return response.json()

def getMeasurement(source):
    return {
        'c8y_Temperature': {
            'T': {
                'value': randint(20, 29),
                'unit': '°C'
            }
        },
        'type': 'c8y_Temperature',
        'source': {
            'id': source
        },
        'time': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    }

# Check if device already created
response = requests.get(C8Y_BASE + '/identity/externalIds/c8y_SimulatorSerial/' + C8Y_SIMULATOR_EXTERNAL_ID, headers=C8Y_HEADERS)

if (response.status_code == 200):
    deviceId = response.json()['managedObject']['id']
else:
    # Create device
    device = {
        'name': 'Docker Simulator Device',
        'c8y_IsDevice': {}
    }
    response = requests.post(C8Y_BASE + '/inventory/managedObjects', headers=C8Y_HEADERS, data=json.dumps(device))
    deviceId = response.json()['id']
    externalId = {
        'type': 'c8y_SimulatorSerial',
        'externalId': C8Y_SIMULATOR_EXTERNAL_ID
    }
    response = requests.post(C8Y_BASE + '/identity/globalIds/' + deviceId + '/externalIds', headers=C8Y_HEADERS, data=json.dumps(externalId))

logging.info('Device ID: ' + deviceId)


while True:
    sendMeasurement(getMeasurement(deviceId))
    time.sleep(30)
