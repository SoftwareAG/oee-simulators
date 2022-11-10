import argparse
import Environment

from c8y_api import CumulocityApi


def argumentsParser():
    parser = argparse.ArgumentParser(description='Script to export or import profiles data')
    parser.add_argument('--device-id', '-i', type=str, help='Input device id')
    parser.add_argument('--action', '-a', choices=['export', 'import'], help='"Export" or "Import" data')
    parser.add_argument('--data-type', '-d', choices=['measurements', 'alarms', 'all'], help='Export "alarms" or '
                                                                                             '"measurements"')

    args = parser.parse_args()
    ACTION = args.action
    if not ACTION:
        ACTION = Environment.ACTION
    DATA_TYPE = args.data_type
    if not DATA_TYPE:
        DATA_TYPE = Environment.DATA_TYPE
    DEVICE_ID = args.device_id
    if not DEVICE_ID:
        DEVICE_ID = str(Environment.DEVICE_ID)

    return DATA_TYPE, ACTION, DEVICE_ID


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
