import argparse
import Credentials

from c8y_api import CumulocityApi


def argumentsParser():
    parser = argparse.ArgumentParser(description='Script to export profiles data')
    parser.add_argument('--baseurl', '-b', type=str, help='Base URL of the tenant', required=True)
    parser.add_argument('--id-tenant', '-i', type=str, help='Tenant ID', required=True)
    parser.add_argument('--username', '-u', type=str, help='Tenant\'s username', required=True)
    parser.add_argument('--password', '-p', type=str, help='Tenant\'s password', required=True)

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
        c8y = CumulocityApi(base_url=C8Y_BASE,  # the url of your Cumulocity tenant here
                            tenant_id=C8Y_TENANT,  # the tenant ID of your Cumulocity tenant here
                            username=C8Y_USER,  # your Cumulocity IoT username
                            password=C8Y_PASSWORD)  # your Cumulocity IoT password
    except:
        C8Y_BASE = Credentials.C8Y_BASE
        C8Y_TENANT = Credentials.C8Y_TENANT
        C8Y_USER = Credentials.C8Y_USER
        C8Y_PASSWORD = Credentials.C8Y_PASSWORD

        c8y = CumulocityApi(base_url=C8Y_BASE,  # the url of your Cumulocity tenant here
                            tenant_id=C8Y_TENANT,  # the tenant ID of your Cumulocity tenant here
                            username=C8Y_USER,  # your Cumulocity IoT username
                            password=C8Y_PASSWORD)  # your Cumulocity IoT password

    return c8y
