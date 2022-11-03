# importing the requests library
import argparse
from datetime import datetime, timezone
from c8y_api import CumulocityApi


def argumentsParser():
    parser = argparse.ArgumentParser(description='Script to export all profiles data')
    parser.add_argument('--baseurl', '-b', type=str, help='Base URL of the tenant', required=True)
    parser.add_argument('--id', '-i', type=str, help='Tenant ID', required=True)
    parser.add_argument('--username', '-u', type=str, help='Tenant\'s username', required=True)
    parser.add_argument('--password', '-p', type=str, help='Tenant\'s password', required=True)
    parser.add_argument('--all', '-a', action='store_true', help='print all profiles option')
    parser.add_argument('--mode', '-m', choices=['measurements', 'alarms']
                        , help='Choose mode to extract data.\n "measurement" to '
                               'extract measurement,\n "alarm" to '
                               'extract alarm'
                        , required=True)

    # Check if arguments are input right
    try:
        args = parser.parse_args()
        return args
    except SystemExit:
        parser.print_help()
        raise


def c8yPlatformConnection(C8Y_BASE, C8Y_TENANT, C8Y_USER, C8Y_PASSWORD):
    c8y = CumulocityApi(base_url=C8Y_BASE,  # the url of your Cumulocity tenant here
                        tenant_id=C8Y_TENANT,  # the tenant ID of your Cumulocity tenant here
                        username=C8Y_USER,  # your Cumulocity IoT username
                        password=C8Y_PASSWORD)  # your Cumulocity IoT password
    return c8y



