import argparse, logging, base64, os, sys, requests

import Environment

from c8y_api import CumulocityApi

log_format = '[%(asctime)s] [%(levelname)s] - %(message)s'
log_file_formatter = logging.Formatter(log_format)
####################################################
def SetupHeadersForAPIRequest(tenant_id, username, password):
    # Setup for additional API request message
    user_and_pass_bytes = base64.b64encode(
        (tenant_id + "/" + username + ':' + password).encode('ascii'))  # bytes
    user_and_pass = user_and_pass_bytes.decode('ascii')  # decode to str

    c8y_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + user_and_pass
    }

    measurements_headers = {
        'Content-Type': 'application/vnd.com.nsn.cumulocity.measurementcollection+json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + user_and_pass
    }
    return c8y_headers, measurements_headers


def SetupLogger(file_logger_name, console_logger_name, filepath, file_log_level, console_log_level):
    # Check logs folder availability
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # set up logging to file
    log_filehandler = logging.FileHandler(filepath)
    log_filehandler.setFormatter(log_file_formatter)
    file_logger = logging.getLogger(file_logger_name)
    file_logger.setLevel(file_log_level)
    file_logger.addHandler(log_filehandler)

    # set up logging to console
    log_console_handler = logging.StreamHandler(sys.stdout)
    log_console_handler.setFormatter(log_file_formatter)
    console_logger = logging.getLogger(console_logger_name)
    console_logger.setLevel(console_log_level)
    console_logger.addHandler(log_console_handler)

    return file_logger, console_logger


def HandleExportArguments():
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

    data_type = args.data_type
    if not data_type:
        data_type = Environment.DATA_TYPE

    device_ids_list = args.device_ids
    if not device_ids_list:
        device_ids_list = []
        abc = Environment.DEVICE_ID
        if Environment.DEVICE_ID:
            logging.info(type(Environment.DEVICE_ID))
            if type(Environment.DEVICE_ID) == tuple:
                for device_id in Environment.DEVICE_ID:
                    device_ids_list.append(device_id)
            else:
                device_ids_list.append(Environment.DEVICE_ID)

    log_argument = args.log
    log_level = logging.INFO
    if log_argument == 'DEBUG':
        log_level = logging.DEBUG
    elif log_argument == 'WARNING':
        log_level = logging.WARNING
    elif log_argument == 'ERROR':
        log_level = logging.ERROR
    elif log_argument == 'CRITICAL':
        log_level = logging.CRITICAL

    create_from = args.create_from
    if not create_from:
        create_from = Environment.CREATE_FROM

    create_to = args.create_to
    if not create_to:
        create_to = Environment.CREATE_TO

    username = args.username
    if not username:
        username = Environment.C8Y_USER

    password = args.password
    if not password:
        password = Environment.C8Y_PASSWORD

    baseurl = args.baseurl
    if not baseurl:
        baseurl = Environment.C8Y_BASE
    baseurl = RemoveTrailingSlashFromBaseUrl(baseurl)

    tenant = args.tenant_id
    if not tenant:
        tenant = Environment.C8Y_TENANT

    c8y = CumulocityApi(base_url=baseurl,  # the url of your Cumulocity tenant here
                        tenant_id=tenant,  # the tenant ID of your Cumulocity tenant here
                        username=username,  # your Cumulocity IoT username
                        password=password)  # your Cumulocity IoT password

    return data_type, device_ids_list, create_from, create_to, log_level, c8y, password


def HandleImportArguments():
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
    BASEURL = RemoveTrailingSlashFromBaseUrl(BASEURL)

    TENANT = args.tenant_id
    if not TENANT:
        TENANT = Environment.C8Y_TENANT

    c8y = CumulocityApi(base_url=BASEURL,  # the url of your Cumulocity tenant here
                        tenant_id=TENANT,  # the tenant ID of your Cumulocity tenant here
                        username=USERNAME,  # your Cumulocity IoT username
                        password=PASSWORD)  # your Cumulocity IoT password

    return INPUT_FILE_LIST, LOG_LEVEL, c8y, PASSWORD


def RemoveTrailingSlashFromBaseUrl(baseUrl):
    if baseUrl[-1] == '/':
        return baseUrl[:-1]
    return baseUrl


def CheckTenantConnection(baseUrl, C8Y_HEADERS):
    # Check if connection to tenant can be created
    try:
        response = requests.get(f'{baseUrl}/tenant/currentTenant', headers=C8Y_HEADERS)
        return response
    except:
        return None