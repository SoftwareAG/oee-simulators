import sys
import json, os, logging, requests, base64
from datetime import datetime, timedelta, time
from random import randint, uniform, choices, gauss
from statistics import mean

from c8y_api import CumulocityApi

import ArgumentsAndCredentialsHandler, Environment

C8Y_PROFILE_GROUP = 'c8y_EventBasedSimulatorProfile'
C8Y_OEE_SIMULATOR_DEVICES_GROUP = "c8y_EventBasedSimulator"
c8y = CumulocityApi(base_url=Environment.C8Y_BASE,  # the url of your Cumulocity tenant here
                    tenant_id=Environment.C8Y_TENANT,  # the tenant ID of your Cumulocity tenant here
                    username=Environment.C8Y_USER,  # your Cumulocity IoT username
                    password=Environment.C8Y_PASSWORD)  # your Cumulocity IoT password
C8Y_HEADERS, MEASUREMENTS_HEADERS = ArgumentsAndCredentialsHandler.SetupHeadersForAPIRequest(
    tenant_id=c8y.tenant_id, username=c8y.username, password=Environment.C8Y_PASSWORD)


def current_timestamp(format="%Y-%m-%dT%H:%M:%S.%f"):
    return datetime.utcnow().strftime(format)[:-3] + 'Z'


logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.DEBUG)
log = logging.getLogger("Measurements-generator")
log.info(f"started at {current_timestamp()}")
#####################################################
'''
# Check if connection to tenant can be created
tenantConnectionResponse = ArgumentsAndCredentialsHandler.CheckTenantConnection(baseUrl=Environment.C8Y_BASE,
                                                                                C8Y_HEADERS=C8Y_HEADERS)
if tenantConnectionResponse:
    log.info(f"Connect to tenant {Environment.C8Y_TENANT} successfully")
else:
    if tenantConnectionResponse is None:
        log.error(f"Wrong base url setup. Check again the URL: {Environment.C8Y_BASE}")
    else:
        log.error(tenantConnectionResponse.json())
    log.error(f"Connect to tenant {Environment.C8Y_TENANT} failed")
    sys.exit()
'''
######################################################
# Start and end date are mandatory and need to be in ISO8601 format (e.g. 2020-10-26T10:00:00.000).
sim_time = datetime.utcnow()
sim_end_time = sim_time + timedelta(hours=1)

LIST_OF_MEASUREMENTS = ['Availability', 'AvailabilityLossTime', 'PerformanceLossTime', 'ActualProductionTime',
                        'QualityLossAmount', 'IdealQualityTime', 'IdealCycleAmount', 'AvailabilityLossAmount',
                        'IdealMachineRuntime', 'IdealProductionAmount', 'OEE', 'ActualQualityAmount',
                        'ActualProductionAmount', 'IdealAmount', 'PerformanceLossAmount', 'Quality', 'IdealCycleTime',
                        'QualityLossTime', 'Performance', 'PotentialProductionTime']


def ListAllChildDevices():
    deviceInTenantCount = 0
    deviceManagedObject = c8y.device_inventory.select(type=C8Y_OEE_SIMULATOR_DEVICES_GROUP)
    listOfChildDevicesExternalIds = []
    for device in deviceManagedObject:
        deviceInTenantCount += 1
        log.info(
            f"Found device '{device.name}', id: #{device.id}, owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        for childDevice in device.child_devices:
            deviceExternalId, deviceExternalIdType = CheckDeviceExternalIdById(childDevice.id, c8y.base_url)
            if not deviceExternalId:
                return
            if IsExternalIdTypeEventBasedSimulatorProfile(deviceExternalIdType):
                filePath = CreateFilePath(Id=deviceExternalId)
            else:
                return
            listOfChildDevicesExternalIds.append(deviceExternalId)
            ExportMeasurements(filePath=filePath)
    if deviceInTenantCount == 0:
        log.info(f"No device in tenant {c8y.tenant_id} found")


def GetExternalIdReponse(deviceId, baseUrl):
    externalIdResponse = requests.get(f'{baseUrl}/identity/globalIds/{deviceId}/externalIds',
                                      headers=C8Y_HEADERS)
    if not externalIdResponse.ok:
        log.error(externalIdResponse.json())
        sys.exit()
    else:
        return externalIdResponse


def CheckDeviceExternalIdById(deviceId, baseUrl):
    externalIdResponse = GetExternalIdReponse(deviceId, baseUrl)

    try:
        deviceExternalId = externalIdResponse.json()['externalIds'][0]['externalId']
        deviceExternalIdType = externalIdResponse.json()['externalIds'][0]['type']
        log.info(
            f"Found external id: {deviceExternalId} with type: {deviceExternalIdType} for the device with id {deviceId}")
    except:
        log.info(f"Could not find external id for the device with id {deviceId}")
        return None, None

    return deviceExternalId, deviceExternalIdType


def IsExternalIdTypeEventBasedSimulatorProfile(deviceExternalIdType):
    if deviceExternalIdType == C8Y_PROFILE_GROUP:
        return True
    else:
        log.info(f"The type {deviceExternalIdType} of external ID must match with type {C8Y_PROFILE_GROUP}")
        return False


def CreateFilePath(Id):
    # Check if folder containing data files exists and make one if not
    if not os.path.exists('generated_data'):
        os.makedirs('generated_data')
    relativeFilePath = f'generated_data\{Id}.json'
    filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
    log.debug(f"Created successfully file path: {filePath}")
    return filePath


def ExportMeasurements(filePath):
    jsonMeasurementsList = JsonMeasurementList(device_id=123456, distribution='normal')
    AppendDataToJsonFile(jsonMeasurementsList, filePath, 'measurements')


def JsonMeasurementList(device_id, distribution):
    time_pointer = sim_time
    time_count = 0
    jsonMeasurementList = []
    storageMeasurementDict = CreateStorageMeasurementDict()
    storageMeasurementDict_1800s = CreateStorageMeasurementDict()
    while time_pointer <= sim_end_time:
        time_count += 1
        measurementsTemplateDict = CreateExtraInfoDict(time_pointer, device_id)
        # 600s
        for measurementKey in LIST_OF_MEASUREMENTS:
            newMeasurement = CreateMeasurement(distribution)
            measurementsDict = CreateIndividualMeasurementDict(measurement_key=measurementKey,
                                                               measurement_series='600s',
                                                               new_measurement=newMeasurement)

            measurementsTemplateDict.update(measurementsDict)
            storageMeasurementDict[f"{measurementKey}"].append(newMeasurement)
        jsonMeasurementList.append(measurementsTemplateDict)

        # 1800s
        if time_count == 3 or time_count == 6:
            measurementsTemplateDict = CreateExtraInfoDict(time_pointer, device_id)
            for measurementKey in LIST_OF_MEASUREMENTS:
                newMeasurement = CalculateMeanValue(storage_measurement_dict=storageMeasurementDict,
                                                    measurement_key=measurementKey)
                measurementsDict = CreateIndividualMeasurementDict(measurement_key=measurementKey,
                                                                   measurement_series='1800s',
                                                                   new_measurement=newMeasurement)

                measurementsTemplateDict.update(measurementsDict)
                storageMeasurementDict_1800s[f"{measurementKey}"].append(newMeasurement)
            jsonMeasurementList.append(measurementsTemplateDict)

        # 3600s
        if time_count == 6:
            measurementsTemplateDict = CreateExtraInfoDict(time_pointer, device_id)
            for measurementKey in LIST_OF_MEASUREMENTS:
                newMeasurement = CalculateMeanValue(storage_measurement_dict=storageMeasurementDict_1800s,
                                                    measurement_key=measurementKey)
                measurementsDict = CreateIndividualMeasurementDict(measurement_key=measurementKey,
                                                                   measurement_series='3600s',
                                                                   new_measurement=newMeasurement)

                measurementsTemplateDict.update(measurementsDict)
            jsonMeasurementList.append(measurementsTemplateDict)
            storageMeasurementDict = CreateStorageMeasurementDict()
            storageMeasurementDict_1800s = CreateStorageMeasurementDict()
            time_count = 0

        time_pointer += timedelta(seconds=600)

    return jsonMeasurementList


def CreateExtraInfoDict(time_pointer, device_id):
    extraInfoDict = {
        "type": "OEEMeasurements",
        "time": f"{time_pointer}",
        "source": {
            "id": f"{device_id}"
        }
    }
    return extraInfoDict


def CreateIndividualMeasurementDict(measurement_key, measurement_series, new_measurement):
    measurement_dict = {
        f"{measurement_key}":
            {
                f"{measurement_series}":
                    {
                        "unit": "",
                        "value": f"{new_measurement}"
                    }
            }
    }
    return measurement_dict


def CreateStorageMeasurementDict():
    storage_measurement_dict = {}
    for measurement_key in LIST_OF_MEASUREMENTS:
        new_key = {
            f"{measurement_key}": []
        }
        storage_measurement_dict.update(new_key)
    return storage_measurement_dict


def CreateMeasurement(distribution):
    MeasurementValue = 0.0
    if distribution == "uniform":
        min_value = 0
        max_value = 100
        MeasurementValue = round(uniform(min_value, max_value), 2)
    elif distribution == "uniformint":
        min_value = 0
        max_value = 200
        MeasurementValue = randint(min_value, max_value)
    elif distribution == "normal":
        mu = 20
        sigma = 0.5
        MeasurementValue = round(gauss(mu, sigma), 2)
    return MeasurementValue


def AppendDataToJsonFile(jsonDataList, filePath, data_type='measurements', json_data={}):
    # Create new json file or add data to an existing json file
    with open(filePath, 'w') as f:
        json_data[f"{data_type}"] = jsonDataList
        json.dump(json_data, f, indent=2)


def CalculateMeanValue(storage_measurement_dict, measurement_key):
    meanValue = mean(storage_measurement_dict[f"{measurement_key}"])
    return meanValue


if __name__ == '__main__':
    filePath = CreateFilePath(Id=123456)
    ExportMeasurements(filePath=filePath)
    log.info("FINISH")
    # ListAllChildDevices()
