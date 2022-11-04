import argparse
import Environment

from c8y_api import CumulocityApi


def argumentsParser():
    parser = argparse.ArgumentParser(description='Script to export profiles data')
    parser.add_argument('--baseurl', '-b', type=str, help='Base URL of the tenant', required=True)
    parser.add_argument('--id-tenant', '-i', type=str, help='Tenant ID', required=True)
    parser.add_argument('--username', '-u', type=str, help='Tenant\'s username', required=True)
    parser.add_argument('--password', '-p', type=str, help='Tenant\'s password', required=True)
    parser.add_argument('--data-type', '-d', choices=['measurements', 'alarms']
                        , help='Choose data type between "measurement" or "alarm"')
    parser.add_argument('--mode', '-m', choices=['all', 'specific'],
                        help='Extract "all" devices data or only data from a "specific" device')

    # Check if arguments are input right
    try:
        args = parser.parse_args()
        return args
    except SystemExit:
        parser.print_help()
        raise


def c8yPlatformConnection():
    try:
        args = argumentsParser()
        C8Y_BASE = args.baseurl
        C8Y_TENANT = args.id_tenant
        C8Y_USER = args.username
        C8Y_PASSWORD = args.password
        MODE = args.mode
        DATA_TYPE = args.data_type
    except:
        C8Y_BASE = Environment.C8Y_BASE
        C8Y_TENANT = Environment.C8Y_TENANT
        C8Y_USER = Environment.C8Y_USER
        C8Y_PASSWORD = Environment.C8Y_PASSWORD
        print("Do you want to extract 'all' devices data or only data from a 'specific' device?")
        MODE = chooseOneOfChoices(['all', 'specific'])
        print(f"You chose to extract data from {MODE.upper()} device(s)")
        print("Do you want to extract 'measurements' or 'alarms' data?")
        DATA_TYPE = chooseOneOfChoices(['measurements', 'alarms'])
        print(f"You chose to extract {DATA_TYPE.upper()} data")

    c8y = CumulocityApi(base_url=C8Y_BASE,  # the url of your Cumulocity tenant here
                        tenant_id=C8Y_TENANT,  # the tenant ID of your Cumulocity tenant here
                        username=C8Y_USER,  # your Cumulocity IoT username
                        password=C8Y_PASSWORD)  # your Cumulocity IoT password

    return c8y, MODE, DATA_TYPE


def chooseOneOfChoices(listOfChoices):
    while True:
        listToStringWithCommas = "', '".join(listOfChoices)
        print(f"Type one of these words '{listToStringWithCommas}'")
        inputString = input()
        if inputString in listOfChoices:
            break
        else:
            print(f"the choice {inputString} is not accepted, only input {listToStringWithCommas}")
    return inputString
