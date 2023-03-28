import argparse

def get_credentials():
    # Gets credentials from command line input
    parser = argparse.ArgumentParser(description='Cumulocity API credentials setup')
    parser.add_argument('--tenant', '-t', type=str, help='Tenant ID')
    parser.add_argument('--password', '-p', type=str, help='C8Y Password')
    parser.add_argument('--baseurl', '-b', type=str, help='C8Y Baseurl')
    parser.add_argument('--user', '-u', type=str, help='C8Y Username')
    args = parser.parse_args()

    user = args.user
    password = args.password
    base_url = args.baseurl
    tenant = args.tenant

    return base_url, tenant, user, password