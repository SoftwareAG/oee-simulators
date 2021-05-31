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
C8Y_SIMULATOR_EXTERNAL_ID = 'myDmgSimulator'

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
        'name': 'Docker DMG Mori Simulator Device',
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

eventMetadata = {}

with open('dmg_metadata.csv', 'rU') as csvfile:
    readCSV = csv.reader(csvfile, delimiter='\t')
    # skip header line
    next(readCSV, None)
    for row in readCSV:
        metadata = {
            'type': row[1],
            'category': row[2],
            'status': row[3],
            'sourceType': row[4],
            'textId': row[5]
        }
        eventMetadata[str(row[0])] = metadata

logging.info(eventMetadata)

eventDataBase = []

with open('dmg_machineData.csv', 'rU') as csvfile:
    readCSV = csv.reader(csvfile, delimiter='\t')
    # skip header line
    next(readCSV, None)
    for row in readCSV:
        # there is some messed up data in the csv -> skip it
        if len(row) < 15:
            continue
        entryType = str(row[3])
        event = {
            'type': eventMetadata[entryType]['type'],
            'text': eventMetadata[entryType]['type'],
            'dmg_TypeInfo': {
                'category': eventMetadata[entryType]['category'],
                'status': eventMetadata[entryType]['status'],
                'sourceType': eventMetadata[entryType]['sourceType'],
                'textId': eventMetadata[entryType]['textId']
            },
            'dmg_Properties': {
                'source': row[4],
                'parameter': row[5],
                'extendedParameter': row[6],
                'userComment': row[7],
                'signalResult': row[8],
                'signalStream': row[9],
                'parameter2': row[10],
                'parameter3': row[11],
                'parameter4': row[12],
                'parameter5': row[13],
                'errorCategoryId': row[14]
            }
        }
        eventDataBase.append(event)

index = 0

while True:
    baseEvent = {
        'source': {
            'id': deviceId
        },
        'time': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    }
    baseEvent.update(eventDataBase[index])
    sendEvent(baseEvent)
    index = index + 1 % len(eventDataBase)
    time.sleep(10)
