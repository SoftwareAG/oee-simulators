import argparse

def get_credentials():
    # Gets credentials from command line input
    parser = argparse.ArgumentParser(description='Cumulocity API credentials setup')
    parser.add_argument('--tenant-id', '-t', type=str, help='Tenant ID')
    parser.add_argument('--password', '-p', type=str, help='C8Y Password')
    parser.add_argument('--baseurl', '-b', type=str, help='C8Y Baseurl')
    parser.add_argument('--username', '-u', type=str, help='C8Y Username')
    args = parser.parse_args()

    username = args.username
    password = args.password
    baseurl = args.baseurl
    tenant_id = args.tenant_id

    return baseurl, tenant_id, username, password