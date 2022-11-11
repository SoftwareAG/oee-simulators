import argparse

import Environment
import logging

from c8y_api import CumulocityApi


def handleExportArguments():
    parser = argparse.ArgumentParser(
        description='Script to export or import profiles data')
    parser.add_argument('--device-id', '-i', type=str, help='Input device id')
    parser.add_argument('--create-from', '-f', type=str, help='Input "create from" milestone')
    parser.add_argument('--create-to', '-t', type=str, help='Input "create to" milestone')
    parser.add_argument('--data-type', '-d', choices=['measurements', 'alarms', 'all'], help='Export "alarms" or '
                                                                                             '"measurements"')

    args = parser.parse_args()
    DATA_TYPE = args.data_type
    if not DATA_TYPE:
        DATA_TYPE = Environment.DATA_TYPE
    DEVICE_ID = args.device_id
    if not DEVICE_ID:
        DEVICE_ID = Environment.DEVICE_ID
        if DEVICE_ID:
            DEVICE_ID = str(DEVICE_ID)

    CREATE_FROM = args.create_from
    if not CREATE_FROM:
        CREATE_FROM = Environment.CREATE_FROM
    CREATE_TO = args.create_to
    if not CREATE_TO:
        CREATE_TO = Environment.CREATE_TO

    return DATA_TYPE, DEVICE_ID, CREATE_FROM, CREATE_TO


def handleImportArguments():
    parser = argparse.ArgumentParser(
        description='Script to import profiles data')
    parser.add_argument('--ifile', '-i', type=str, help='Input file')
    parser.add_argument(
        '--log', '-l', choices=['INFO', 'DEBUG'], help='Log-level')
    parser.add_argument(
        '--username', '-u', type=str, help='C8Y Username')
    parser.add_argument(
        '--password', '-p', type=str, help='C8Y Password')
    parser.add_argument(
        '--baseurl', '-b', type=str, help='C8Y Baseurl')
    parser.add_argument(
        '--tenant', '-t', type=str, help='C8Y TenantID')

    args = parser.parse_args()
    INPUT_FILE = args.ifile
    LOG_ARGUMENT = args.log
    LOG_LEVEL = logging.INFO
    if LOG_ARGUMENT == 'DEBUG':
        LOG_LEVEL = logging.DEBUG

    USERNAME = args.username
    if not USERNAME:
        USERNAME = Environment.C8Y_USER

    PASSWORD = args.password
    if not PASSWORD:
        PASSWORD = Environment.C8Y_PASSWORD
    
    BASEURL = args.baseurl
    if not BASEURL:
        BASEURL = Environment.C8Y_BASE
    
    TENANT = args.tenant
    if not TENANT:
        TENANT = Environment.C8Y_TENANT

    return INPUT_FILE, LOG_LEVEL, USERNAME, PASSWORD, BASEURL, TENANT


def c8yPlatformConnection():
    if Environment.C8Y_BASE[-1] == '/':
        C8Y_BASE = Environment.C8Y_BASE[:-1]
    else:
        C8Y_BASE = Environment.C8Y_BASE
    C8Y_TENANT = Environment.C8Y_TENANT
    C8Y_USER = Environment.C8Y_USER
    C8Y_PASSWORD = Environment.C8Y_PASSWORD

    c8y = CumulocityApi(base_url=C8Y_BASE,  # the url of your Cumulocity tenant here
                        tenant_id=C8Y_TENANT,  # the tenant ID of your Cumulocity tenant here
                        username=C8Y_USER,  # your Cumulocity IoT username
                        password=C8Y_PASSWORD)  # your Cumulocity IoT password
    return c8y
