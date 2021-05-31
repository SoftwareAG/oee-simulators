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
C8Y_BASE = os.environ.get('C8Y_BASEURL')
C8Y_TENANT = os.environ.get('C8Y_TENANT')
C8Y_USER = os.environ.get('C8Y_USER')
C8Y_PASSWORD = os.environ.get('C8Y_PASSWORD')
C8Y_SIMULATOR_EXTERNAL_ID = 'myDuerrSimulator'

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
        'name': 'Docker Duerr Simulator Device',
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

def resolveSeverity(input):
    if 'Warning' in input:
        return 'WARNING'
    elif 'Fault' in input:
        return 'MAJOR'
    elif 'Operate' in input:
        return 'MINOR'
    else:
        return 'WARNING'

availableAlarms = {}

with open('duerr_alarmlog.csv', 'rU') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=';')
    # skip header line
    next(readCSV, None)
    # build adamos alarms from the rows
    for row in readCSV:
        alarmObject = {
            'type': row[8],
            'text': row[4],
            'severity': resolveSeverity(row[5]),
            'status': 'ACTIVE',
            'duerr_Properties': {
                'group': row[3],
                'prio': row[6],
                'ioNode': row[7],
                'location': row[9],
                'username': row[10],
                'computer': row[11]
            }
        }
        availableAlarms[row[8]] = alarmObject

currentActiveAlarms = []

alarmTypes = availableAlarms.keys()


availableMeasurements = []

# extract the measurement names from the file names
for filename in listdir('duerr_measurements'):
    withoutExt = filename[0:-4]
    withoutExt = withoutExt.replace('.', '_')
    lastUnderscore = withoutExt.rfind('_')
    measurementMetaData = {
        'file': filename,
        'fragment': withoutExt[0:lastUnderscore],
        'series': withoutExt[lastUnderscore + 1:]
    }
    availableMeasurements.append(measurementMetaData)

measurementDataBase = {}

SAMPLE_SIZE = 1000

# extract sample amount of data for each measurement
for filename in listdir('duerr_measurements'):
    with open('duerr_measurements/' + filename, 'rU') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=';')
        data = []
        # grab 100 values
        i = 0
        for row in readCSV:
            m = {
                'value': float(row[1]),
                'quality': int(row[2])
            }
            data.append(m)
            i += 1
            if i == SAMPLE_SIZE:
                break
        measurementDataBase[filename] = data

logging.debug(measurementDataBase)

index = 0

while True:
    # measurements
    baseMeasurement = {
        'type': 'duerr_collected_measurements',
        'time': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
        'source': {
            'id': deviceId
        }
    }

    for measurement in availableMeasurements:
        fragment = {
            measurement['fragment']: {
                measurement['series']: {
                    'value': measurementDataBase[measurement['file']][index]['value'],
                    'qualtiy': measurementDataBase[measurement['file']][index]['quality']
                }
            }
        }
        baseMeasurement.update(fragment)

    sendMeasurement(baseMeasurement)
    index = index + 1 % SAMPLE_SIZE

    #alarms
    doAlarms = randint(1, 10)
    if doAlarms == 10:
        chance = randint(1, 20)
        if chance > (20 - len(currentActiveAlarms)):
            # clear existing alarm
            if len(currentActiveAlarms) > 1:
                alarmId = randint(0, len(currentActiveAlarms) - 1)
                clearAlarm(currentActiveAlarms[alarmId])
                currentActiveAlarms.remove(currentActiveAlarms[alarmId])
            elif len(currentActiveAlarms) == 1:
                clearAlarm(currentActiveAlarms[0])
                currentActiveAlarms = []
        else:
            # create an alarm randomly
            alarmType = randint(0, len(alarmTypes) - 1)
            baseAlarm = {
                'source': {
                    'id': deviceId
                },
                'time': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            }
            baseAlarm.update(availableAlarms[alarmTypes[alarmType]])
            alarm = sendAlarm(baseAlarm)
            if alarm['id'] not in currentActiveAlarms:
                currentActiveAlarms.append(alarm['id'])
    time.sleep(1)
