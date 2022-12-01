import sys, json, os, logging, requests

from datetime import datetime, timedelta
from random import randint, uniform, gauss
from statistics import mean
from c8y_api import CumulocityApi

import ArgumentsAndCredentialsHandler, Environment

C8Y_PROFILE_GROUP = "c8y_EventBasedSimulatorProfile"
C8Y_OEE_SIMULATOR_DEVICES_GROUP = "c8y_EventBasedSimulator"
c8y = CumulocityApi(base_url=Environment.C8Y_BASE,  # the url of your Cumulocity tenant here
                    tenant_id=Environment.C8Y_TENANT,  # the tenant ID of your Cumulocity tenant here
                    username=Environment.C8Y_USER,  # your Cumulocity IoT username
                    password=Environment.C8Y_PASSWORD)  # your Cumulocity IoT password
C8Y_HEADERS, MEASUREMENTS_HEADERS = ArgumentsAndCredentialsHandler.SetupHeadersForAPIRequest(
    tenant_id=c8y.tenant_id, username=c8y.username, password=Environment.C8Y_PASSWORD)


def current_timestamp(format="%Y-%m-%dT%H:%M:%S.%f"):
    return datetime.utcnow().strftime(format)[:-3] + 'Z'


logging.basicConfig(format="%(asctime)s %(name)s:%(message)s", level=logging.DEBUG)
log = logging.getLogger("Measurements-generator")
log.info(f"started at {current_timestamp()}")
#####################################################
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
######################################################
# Start and end date are mandatory and need to be in ISO8601 format (e.g. 2020-10-26T10:00:00.000).
simStartTime = datetime.utcnow()
simEndTime = simStartTime + timedelta(hours=1)

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
                continue
            if IsExternalIdTypeEventBasedSimulatorProfile(deviceExternalIdType):
                filePath = CreateFilePath(Id=deviceExternalId)
            else:
                continue
            listOfChildDevicesExternalIds.append(deviceExternalId)
            ExportMeasurements(filePath=filePath, device_id=childDevice.id)
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


def ExportMeasurements(filePath, device_id):
    jsonMeasurementsList = CreateJsonMeasurementList(deviceId=device_id, distribution='normal')
    AppendDataToJsonFile(jsonMeasurementsList, filePath, 'measurements')


def CreateJsonMeasurementList(deviceId, distribution):
    timePointer = simStartTime
    timeCount = 0
    jsonMeasurementList = []
    storageMeasurementDict = CreateStorageMeasurementDict()
    storageMeasurementDict_1800s = CreateStorageMeasurementDict()
    while timePointer <= simEndTime:
        timeCount += 1
        measurementsTemplateDict = CreateExtraInfoDict(timePointer, deviceId)
        # 600s
        for measurementKey in LIST_OF_MEASUREMENTS:
            newMeasurement = CreateMeasurement(distribution)
            measurementsDict = CreateIndividualMeasurementDict(measurementKey=measurementKey,
                                                               measurementSeries='600s',
                                                               newMeasurement=newMeasurement)

            measurementsTemplateDict.update(measurementsDict)
            storageMeasurementDict[f"{measurementKey}"].append(newMeasurement)
        jsonMeasurementList.append(measurementsTemplateDict)

        # 1800s
        if timeCount == 3 or timeCount == 6:
            measurementsTemplateDict = CreateExtraInfoDict(timePointer, deviceId)
            for measurementKey in LIST_OF_MEASUREMENTS:
                newMeasurement = CalculateMeanValue(storageMeasurementDict=storageMeasurementDict,
                                                    measurementKey=measurementKey)
                measurementsDict = CreateIndividualMeasurementDict(measurementKey=measurementKey,
                                                                   measurementSeries='1800s',
                                                                   newMeasurement=newMeasurement)

                measurementsTemplateDict.update(measurementsDict)
                storageMeasurementDict_1800s[f"{measurementKey}"].append(newMeasurement)
            jsonMeasurementList.append(measurementsTemplateDict)

        # 3600s
        if timeCount == 6:
            measurementsTemplateDict = CreateExtraInfoDict(timePointer, deviceId)
            for measurementKey in LIST_OF_MEASUREMENTS:
                newMeasurement = CalculateMeanValue(storageMeasurementDict=storageMeasurementDict_1800s,
                                                    measurementKey=measurementKey)
                measurementsDict = CreateIndividualMeasurementDict(measurementKey=measurementKey,
                                                                   measurementSeries='3600s',
                                                                   newMeasurement=newMeasurement)

                measurementsTemplateDict.update(measurementsDict)
            jsonMeasurementList.append(measurementsTemplateDict)
            storageMeasurementDict = CreateStorageMeasurementDict()
            storageMeasurementDict_1800s = CreateStorageMeasurementDict()
            timeCount = 0

        timePointer += timedelta(seconds=600)

    return jsonMeasurementList


def CreateExtraInfoDict(timePointer, deviceId):
    extraInfoDict = {
        "type": "OEEMeasurements",
        "time": f"{timePointer}",
        "source": {
            "id": f"{deviceId}"
        }
    }
    return extraInfoDict


def CreateIndividualMeasurementDict(measurementKey, measurementSeries, newMeasurement):
    measurementDict = {
        f"{measurementKey}":
            {
                f"{measurementSeries}":
                    {
                        "unit": "",
                        "value": f"{newMeasurement}"
                    }
            }
    }
    return measurementDict


def CreateStorageMeasurementDict():
    storageMeasurementDict = {}
    for measurementKey in LIST_OF_MEASUREMENTS:
        new_key = {
            f"{measurementKey}": []
        }
        storageMeasurementDict.update(new_key)
    return storageMeasurementDict


def CreateMeasurement(distribution):
    MeasurementValue = 0.0
    if distribution == "uniform":
        minValue = 0
        maxValue = 100
        MeasurementValue = round(uniform(minValue, maxValue), 2)
    elif distribution == "uniformint":
        minValue = 0
        maxValue = 200
        MeasurementValue = randint(minValue, maxValue)
    elif distribution == "normal":
        mu = 20
        sigma = 0.5
        MeasurementValue = round(gauss(mu, sigma), 2)
    return MeasurementValue


def AppendDataToJsonFile(jsonDataList, filePath, dataType='measurements', jsonData={}):
    # Create new json file or add data to an existing json file
    with open(filePath, 'w') as f:
        jsonData[f"{dataType}"] = jsonDataList
        json.dump(jsonData, f, indent=2)


def CalculateMeanValue(storageMeasurementDict, measurementKey):
    meanValue = mean(storageMeasurementDict[f"{measurementKey}"])
    return meanValue


if __name__ == '__main__':
    ListAllChildDevices()
    log.info("FINISH")
    # ListAllChildDevices()
