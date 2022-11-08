import argparse
import Environment

from c8y_api import CumulocityApi


def argumentsParser():
    parser = argparse.ArgumentParser(description='Script to export or import profiles data')
    parser.add_argument('--action', '-a', choices=['export', 'import'], help='"Export" or "Import" data', required=True)
    parser.add_argument('--mode', '-m', choices=['all', 'specific']
                        , help='Extract data from "all" device, or from "specific" device',
                        required=True)
    parser.add_argument('--data-type', '-d', choices=['measurements', 'alarms'], help='Export "alarms" or '
                                                                                      '"measurements"', required=True)

    try:
        args = parser.parse_args()
        MODE = args.mode
        ACTION = args.action
        DATA_TYPE = args.data_type
    except:
        MODE = Environment.MODE
        DATA_TYPE = Environment.DATA_TYPE
        ACTION = Environment.ACTION

    return MODE, DATA_TYPE, ACTION

    """""
    # Check if arguments are input right and print help message
    try:
        args = parser.parse_args()
        return args
    except SystemExit:
        parser.print_help()
        raise
    """


def c8yPlatformConnection():
    C8Y_BASE = Environment.C8Y_BASE
    C8Y_TENANT = Environment.C8Y_TENANT
    C8Y_USER = Environment.C8Y_USER
    C8Y_PASSWORD = Environment.C8Y_PASSWORD

    c8y = CumulocityApi(base_url=C8Y_BASE,  # the url of your Cumulocity tenant here
                        tenant_id=C8Y_TENANT,  # the tenant ID of your Cumulocity tenant here
                        username=C8Y_USER,  # your Cumulocity IoT username
                        password=C8Y_PASSWORD)  # your Cumulocity IoT password

    return c8y
