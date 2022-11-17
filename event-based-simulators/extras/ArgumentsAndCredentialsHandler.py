import argparse, logging, base64, os, sys, requests

import Environment

from c8y_api import CumulocityApi

logFormat = '[%(asctime)s] [%(levelname)s] - %(message)s'
logFileFormatter = logging.Formatter(logFormat)
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
    parser.add_argument('--device-ids', '-i', type=str, help='Input device id / List of device ids', nargs='+')
    parser.add_argument('--create-from', '-from', type=str, help='Input "create from" milestone')
    parser.add_argument('--create-to', '-to', type=str, help='Input "create to" milestone')
    parser.add_argument('--data-type', '-d', choices=['measurements', 'alarms', 'all'], help='Export "alarms" or "measurements"')
    parser.add_argument('--log', '-l', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Log-level')
    parser.add_argument('--username', '-u', type=str, help='C8Y Username')
    parser.add_argument('--password', '-p', type=str, help='C8Y Password')
    parser.add_argument('--baseurl', '-b', type=str, help='C8Y Baseurl')
    parser.add_argument('--tenant-id', '-t', type=str, help='C8Y TenantID')
    args = parser.parse_args()

    DATA_TYPE = args.data_type
    if not DATA_TYPE:
        DATA_TYPE = Environment.DATA_TYPE

    DEVICE_ID_LIST = args.device_ids
    if not DEVICE_ID_LIST:
        DEVICE_ID_LIST = []
        if Environment.DEVICE_ID:
            for deviceId in Environment.DEVICE_ID:
                DEVICE_ID_LIST.append(deviceId)

    LOG_ARGUMENT = args.log
    LOG_LEVEL = logging.INFO
    if LOG_ARGUMENT == 'DEBUG':
        LOG_LEVEL = logging.DEBUG
    elif LOG_ARGUMENT == 'WARNING':
        LOG_LEVEL = logging.WARNING
    elif LOG_ARGUMENT == 'ERROR':
        LOG_LEVEL = logging.ERROR
    elif LOG_ARGUMENT == 'CRITICAL':
        LOG_LEVEL = logging.CRITICAL

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
    BASEURL = removeTrailingSlashFromBaseUrl(BASEURL)

    TENANT = args.tenant_id
    if not TENANT:
        TENANT = Environment.C8Y_TENANT

    c8y = CumulocityApi(base_url=BASEURL,  # the url of your Cumulocity tenant here
                        tenant_id=TENANT,  # the tenant ID of your Cumulocity tenant here
                        username=USERNAME,  # your Cumulocity IoT username
                        password=PASSWORD)  # your Cumulocity IoT password

    return DATA_TYPE, DEVICE_ID_LIST, CREATE_FROM, CREATE_TO, LOG_LEVEL, c8y


def handleImportArguments():
    parser = argparse.ArgumentParser(description='Script to import profiles data')
    parser.add_argument('--ifiles', '-i', type=str, help='Input file', nargs='+')
    parser.add_argument('--log', '-l', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Log-level')
    parser.add_argument('--username', '-u', type=str, help='C8Y Username')
    parser.add_argument('--password', '-p', type=str, help='C8Y Password')
    parser.add_argument('--baseurl', '-b', type=str, help='C8Y Baseurl')
    parser.add_argument('--tenant-id', '-t', type=str, help='C8Y TenantID')

    args = parser.parse_args()

    if not os.path.exists("export_data"):
        logging.info("No export_data folder found")
        sys.exit()
    INPUT_FILE_LIST = args.ifiles
    if not INPUT_FILE_LIST:
        INPUT_FILE_LIST = []

    LOG_ARGUMENT = args.log
    LOG_LEVEL = logging.INFO
    if LOG_ARGUMENT == 'DEBUG':
        LOG_LEVEL = logging.DEBUG
    elif LOG_ARGUMENT == 'WARNING':
        LOG_LEVEL = logging.WARNING
    elif LOG_ARGUMENT == 'ERROR':
        LOG_LEVEL = logging.ERROR
    elif LOG_ARGUMENT == 'CRITICAL':
        LOG_LEVEL = logging.CRITICAL

    USERNAME = args.username
    if not USERNAME:
        USERNAME = Environment.C8Y_USER

    PASSWORD = args.password
    if not PASSWORD:
        PASSWORD = Environment.C8Y_PASSWORD

    BASEURL = args.baseurl
    if not BASEURL:
        BASEURL = Environment.C8Y_BASE
    BASEURL = removeTrailingSlashFromBaseUrl(BASEURL)

    TENANT = args.tenant_id
    if not TENANT:
        TENANT = Environment.C8Y_TENANT

    c8y = CumulocityApi(base_url=BASEURL,  # the url of your Cumulocity tenant here
                        tenant_id=TENANT,  # the tenant ID of your Cumulocity tenant here
                        username=USERNAME,  # your Cumulocity IoT username
                        password=PASSWORD)  # your Cumulocity IoT password

    return INPUT_FILE_LIST, LOG_LEVEL, c8y


def removeTrailingSlashFromBaseUrl(baseUrl):
    if baseUrl[-1] == '/':
        return baseUrl[:-1]
    return baseUrl


def checkTenantConnection(baseUrl):
    # Check if connection to tenant can be created
    try:
        requests.get(f'{baseUrl}/tenant/currentTenant', headers=C8Y_HEADERS)
        return True
    except:
        return False
