import argparse, logging, base64, os
import sys

import Environment

from c8y_api import CumulocityApi

logFileFormatter = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
####################################################
# Setup for additional API request message
user_and_pass_bytes = base64.b64encode(
    (Environment.C8Y_TENANT + "/" + Environment.C8Y_USER + ':' + Environment.C8Y_PASSWORD).encode('ascii'))  # bytes
user_and_pass = user_and_pass_bytes.decode('ascii')  # decode to str

C8Y_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Basic ' + user_and_pass
}

MEASUREMENTS_HEADERS = {
    'Content-Type': 'application/vnd.com.nsn.cumulocity.measurementcollection+json',
    'Accept': 'application/json',
    'Authorization': 'Basic ' + user_and_pass
}
####################################################


def setupLogger(fileLoggerName, consoleLoggerName, filePath, fileLogLevel, consoleLogLevel):
    # Check logs folder availability
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # set up logging to file
    logFilehandler = logging.FileHandler(filePath)
    logFilehandler.setFormatter(logFileFormatter)
    fileLogger = logging.getLogger(fileLoggerName)
    fileLogger.setLevel(fileLogLevel)
    fileLogger.addHandler(logFilehandler)

    # set up logging to console
    logConsoleHandler = logging.StreamHandler(sys.stdout)
    logConsoleHandler.setFormatter(logFileFormatter)
    consoleLogger = logging.getLogger(consoleLoggerName)
    consoleLogger.setLevel(consoleLogLevel)
    consoleLogger.addHandler(logConsoleHandler)

    return fileLogger, consoleLogger


def handleExportArguments():
    parser = argparse.ArgumentParser(description='Script to export or import profiles data')
    parser.add_argument('--device-id', '-i', type=str, help='Input device id')
    parser.add_argument('--create-from', '-from', type=str, help='Input "create from" milestone')
    parser.add_argument('--create-to', '-to', type=str, help='Input "create to" milestone')
    parser.add_argument('--data-type', '-d', choices=['measurements', 'alarms', 'all'], help='Export "alarms" or "measurements"')
    parser.add_argument('--log', '-l', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Log-level')
    parser.add_argument('--username', '-u', type=str, help='C8Y Username')
    parser.add_argument('--password', '-p', type=str, help='C8Y Password')
    parser.add_argument('--baseurl', '-b', type=str, help='C8Y Baseurl')
    parser.add_argument('--tenant', '-t', type=str, help='C8Y TenantID')
    args = parser.parse_args()

    DATA_TYPE = args.data_type
    if not DATA_TYPE:
        DATA_TYPE = Environment.DATA_TYPE

    DEVICE_ID = args.device_id
    if not DEVICE_ID:
        DEVICE_ID = Environment.DEVICE_ID
        if DEVICE_ID:
            DEVICE_ID = str(DEVICE_ID)

    LOG_LEVEL = args.log
    if not LOG_LEVEL:
        LOG_LEVEL = logging.INFO

    CREATE_FROM = args.create_from
    if not CREATE_FROM:
        CREATE_FROM = Environment.CREATE_FROM

    CREATE_TO = args.create_to
    if not CREATE_TO:
        CREATE_TO = Environment.CREATE_TO

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

    return DATA_TYPE, DEVICE_ID, CREATE_FROM, CREATE_TO, LOG_LEVEL, USERNAME, PASSWORD, BASEURL, TENANT


def handleImportArguments():
    parser = argparse.ArgumentParser(description='Script to import profiles data')
    parser.add_argument('--ifile', '-i', type=str, help='Input file')
    parser.add_argument('--log', '-l', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Log-level')
    parser.add_argument('--username', '-u', type=str, help='C8Y Username')
    parser.add_argument('--password', '-p', type=str, help='C8Y Password')
    parser.add_argument('--baseurl', '-b', type=str, help='C8Y Baseurl')
    parser.add_argument('--tenant', '-t', type=str, help='C8Y TenantID')

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


def removeSlashFromBaseUrl(baseUrl):
    if baseUrl[-1] == '/':
        newBaseurl = baseUrl[:-1]
    else:
        newBaseurl = baseUrl
    return newBaseurl


def c8yPlatformConnection():
    C8Y_BASE = removeSlashFromBaseUrl(Environment.C8Y_BASE)
    C8Y_TENANT = Environment.C8Y_TENANT
    C8Y_USER = Environment.C8Y_USER
    C8Y_PASSWORD = Environment.C8Y_PASSWORD

    c8y = CumulocityApi(base_url=C8Y_BASE,  # the url of your Cumulocity tenant here
                        tenant_id=C8Y_TENANT,  # the tenant ID of your Cumulocity tenant here
                        username=C8Y_USER,  # your Cumulocity IoT username
                        password=C8Y_PASSWORD)  # your Cumulocity IoT password
    return c8y
