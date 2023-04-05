import argparse, logging

log = logging.getLogger("C8y Credentials")
def get_credentials():
    # Gets credentials from command line input
    parser = argparse.ArgumentParser(description='Cumulocity API credentials setup')
    parser.add_argument('--tenant-id', '-t', type=str, help='Tenant ID')
    parser.add_argument('--password', '-p', type=str, help='C8Y Password')
    parser.add_argument('--baseurl', '-b', type=str, help='C8Y Baseurl')
    parser.add_argument('--username', '-u', type=str, help='C8Y Username')
    parser.add_argument('--test', '-test', action='store_true', help='Flag to enable test mode')
    args = parser.parse_args()

    return args.baseurl, args.tenant_id, args.username, args.password, args.test

def check_credentials_availability(C8Y_BASEURL, C8Y_TENANT, C8Y_USER, C8Y_PASSWORD):
    # Get credentials from argument inputs
    base_url, tenant, user, password, test_flag = get_credentials()
    if base_url:
        C8Y_BASEURL = base_url
        if not C8Y_BASEURL:
            log.info("C8Y_BASEURL is not set")
            C8Y_BASEURL = "http://localhost:8080"  # Add placeholder so code can reaches the connection error message
    if tenant:
        C8Y_TENANT = tenant
        if not C8Y_TENANT:
            log.info("C8Y_TENANT is not set")
            C8Y_TENANT = "t100"  # Add placeholder so code can reaches the connection error message
    if user:
        C8Y_USER = user
        if not C8Y_USER:
            log.info("C8Y_USER is not set")
            C8Y_USER = "test"  # Add placeholder so code can reaches the connection error message
    if password:
        C8Y_PASSWORD = password
        if not C8Y_PASSWORD:
            log.info("C8Y_PASSWORD is not set")
            C8Y_PASSWORD = "test"  # Add placeholder so code can reaches the connection error message

    return C8Y_BASEURL, C8Y_TENANT, C8Y_USER, C8Y_PASSWORD, test_flag