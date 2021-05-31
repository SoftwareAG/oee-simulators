# -*- coding: utf-8 -*-

import requests, base64, json, logging, os, time, sys, csv
from random import randint
from datetime import datetime
from os import listdir

logging.basicConfig(level=logging.INFO)

logging.info(os.environ)

'''
Start configuration
'''
C8Y_BASE = 'http://hackathon.adamos-dev.com' #os.environ.get('C8Y_BASEURL')
C8Y_TENANT = os.environ.get('C8Y_TENANT')
C8Y_USER = os.environ.get('C8Y_USER')
C8Y_PASSWORD = os.environ.get('C8Y_PASSWORD')
C8Y_SIMULATOR_EXTERNAL_ID = 'myAsmSimulator'

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

# Check if device already created
response = requests.get(C8Y_BASE + '/identity/externalIds/c8y_SimulatorSerial/' + C8Y_SIMULATOR_EXTERNAL_ID, headers=C8Y_HEADERS)

if (response.status_code == 200):
    deviceId = response.json()['managedObject']['id']
else:
    # Create device
    device = {
        'name': 'Docker ASM Simulator Device',
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

availableEvents = {}

with open('asmEventMetadata.csv', 'rU') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=';')
    # skip header line
    next(readCSV, None)
    for row in readCSV:
        availableEvents[str(row[0])] = row[1]

eventDataBase = []

# extract events from csv
with open('asmEventLog.csv', 'rU') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=';')
    # skip header line
    next(readCSV, None)
    for row in readCSV:
        resolvedType = availableEvents[str(row[5])]
        event = {
            'type': resolvedType,
            'text': resolvedType,
            'asm_Properties': {
                'iBoardNumber': row[2],
                'ucConveyor': row[3],
                'ucProcessingArea': row[4],
                'ucProcessingMode': row[7],
                'iIdSequence': row[8],
                'iBoardCompositeId': row[9],
                'ucSubConveyor': row[10]
            }
        }
        eventDataBase.append(event)

logging.debug(eventDataBase)

index = len(eventDataBase) - 1

while True:
    baseEvent = {
        'source': {
            'id': deviceId
        },
        'time': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    }
    baseEvent.update(eventDataBase[index])
    sendEvent(baseEvent)
    index = index - 1 % len(eventDataBase)
    time.sleep(1)
