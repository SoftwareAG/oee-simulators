import ArgumentsAndCredentialsHandler
import Credentials


def exportSpecificProfileData(c8y, deviceName):
    deviceCount = 0
    deviceIntentorySelect = c8y.device_inventory.select(type="c8y_EventBasedSimulator", name=deviceName)

    for device in deviceIntentorySelect:
        print(f"Found device '{device.name}', id: #{device.id}, "
              f"owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        deviceCount += 1
        for childDevice in device.child_devices:
            print(f"Child device {childDevice.name}, id #{childDevice.id}, owned by device {device.name}")

    if deviceCount == 0:
        print(f"No device with name {deviceName} found")


# Main function to run the script
if __name__ == '__main__':
    try:
        args = ArgumentsAndCredentialsHandler.argumentsParser()
        C8Y_BASE = args.baseurl
        C8Y_TENANT = args.id
        C8Y_USER = args.username
        C8Y_PASSWORD = args.password
        MODE = args.mode
    except:
        C8Y_BASE = Credentials.C8Y_BASE
        C8Y_TENANT = Credentials.C8Y_TENANT
        C8Y_USER = Credentials.C8Y_USER
        C8Y_PASSWORD = Credentials.C8Y_PASSWORD
        
    print('Enter device name to search: ')
    deviceName = input()
    print(f"{C8Y_PASSWORD}, {C8Y_USER}, {C8Y_BASE}, {C8Y_TENANT}, {deviceName}")
    c8y = ArgumentsAndCredentialsHandler.c8yPlatformConnection(C8Y_BASE, C8Y_TENANT, C8Y_USER, C8Y_PASSWORD)
    exportSpecificProfileData(c8y, deviceName)
