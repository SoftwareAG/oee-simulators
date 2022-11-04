import ArgumentsAndCredentialsHandler


def exportAllProfileData(c8y, DATA_TYPE, createFrom, createTo):
    # Loop through the list of device in Device management
    for device in c8y.device_inventory.select(type="c8y_EventBasedSimulator"):
        print(f"Found device '{device.name}', id: #{device.id}, "
              f"owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        print(f"List of {device.name}'s child devices: ")
        for childDevice in device.child_devices:
            print(f"Child device {childDevice.name}, id #{childDevice.id}")
            if DATA_TYPE == "alarms":
                listAlarms(c8y, childDevice, createFrom, createTo)
            elif DATA_TYPE == "measurements":
                # listing measurements of child device
                listMeasurements(c8y, childDevice, createFrom, createTo)


def exportSpecificProfileData(c8y, DATA_TYPE, createFrom, createTo):
    print(f"Enter device name to search for {DATA_TYPE} data: ")
    deviceName = input()
    deviceCount = 0
    for device in c8y.device_inventory.select(type="c8y_EventBasedSimulator", name=deviceName):
        print(f"Found device '{device.name}', id: #{device.id}, "
              f"owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        deviceCount += 1
        print(f"List of {device.name}'s child devices: ")
        for childDevice in device.child_devices:
            print(f"Child device {childDevice.name}, id #{childDevice.id}")
            if DATA_TYPE == "alarms":
                listAlarms(c8y, childDevice, createFrom, createTo)
            elif DATA_TYPE == "measurements":
                # listing measurements of child device
                listMeasurements(c8y, childDevice, createFrom, createTo)

    if deviceCount == 0:
        print(f"No device with name {deviceName} found")


def listAlarms(c8y, childDevice, createFrom, createTo):
    for alarm in c8y.alarms.select(source=childDevice.id, created_after=createFrom, created_before=createTo):
        print(f"Found alarm id #{alarm.id}, severity: {alarm.severity}, time: {alarm.time}, creation time: {alarm.creation_time}, update time : {alarm.updated_time}\n")
        print(f"{alarm.text}\n")
        print(f"fragments: {list(alarm.keys())}\n")


def listMeasurements(c8y, childDevice, createFrom, createTo):
    for measurement in c8y.measurements.select(source=childDevice.id, created_after=createFrom, created_before=createTo):
        print(f"Found measurement id #{measurement.id}\n, type: {measurement.type}\n")
        for measurementKey in measurement.fragments:
            print(f"{measurementKey}: {measurement.fragments.get(measurementKey)}")


# Main function to run the script
if __name__ == '__main__':
    c8y, MODE, DATA_TYPE = ArgumentsAndCredentialsHandler.c8yPlatformConnection()

    print("Export data which is created after/from: \n(example input: 2022-10-28T15:52:19.605Z)")
    createFrom = input()
    print("and created before/to: \n(example input: 2022-10-28T16:02:02.310Z)")
    createTo = input()

    if MODE == "all":
        exportAllProfileData(c8y, DATA_TYPE, createFrom, createTo)
    elif MODE == "specific":
        exportSpecificProfileData(c8y, DATA_TYPE, createFrom, createTo)
