import ArgumentsAndCredentialsHandler
import Credentials


def exportAllProfileData(c8y):
    # Loop through the list of device in Device management
    for device in c8y.device_inventory.select(type="c8y_EventBasedSimulator"):
        print(f"Found device '{device.name}', id: #{device.id}, "
                f"owned by {device.owner}, number of children: {len(device.child_devices)}")
        # Check each child device of the main device with device.id
        for childDevice in device.child_devices:
            print(f"Child devices #{childDevice.id}")
            # listing alarms of child device
            print(f"Begin LISTING ALARMS of device {childDevice.name}, id #{childDevice.id}")
            for alarm in c8y.alarms.select(source=childDevice.id):
                print(f"Found alarm #{alarm.id}, severity: {alarm.severity}\n")
                print(f"{alarm.text}\n")
                print(f"fragments: {list(alarm.keys())}\n")
            # listing measurements of child device
            for measurement in c8y.measurements.select(source=childDevice.id):
                print(f"Found measurement id #{measurement.id}\n, type: {measurement.type}\n")
                for measurementKey in measurement.fragments:
                    print(f"{measurementKey}: {measurement.fragments.get(measurementKey)}")


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
        
    print(f"{C8Y_PASSWORD}, {C8Y_USER}, {C8Y_BASE}, {C8Y_TENANT}")
    c8y = ArgumentsAndCredentialsHandler.c8yPlatformConnection(C8Y_BASE, C8Y_TENANT, C8Y_USER, C8Y_PASSWORD)
    exportAllProfileData(c8y)
