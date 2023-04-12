import argparse, logging

log = logging.getLogger("C8y Credentials")

# Gets arguments command line input
parser = argparse.ArgumentParser()

# Credentials argument group
credentials = parser.add_argument_group('Credentials')
credentials.add_argument('--tenant-id', '-t', type=str, help='Tenant ID')
credentials.add_argument('--password', '-p', type=str, help='C8Y Password')
credentials.add_argument('--baseurl', '-b', type=str, help='C8Y Baseurl')
credentials.add_argument('--username', '-u', type=str, help='C8Y Username')
credentials.add_argument('--test', '-test', action='store_true', help='Flag to enable test mode')

# profile_generator arguments
profile_generator_mode = parser.add_argument_group('Profile_generator')
profile_generator_mode.add_argument("--create-profiles", "-c",  action="store_true", dest="create_profiles",help="create profiles")
profile_generator_mode.add_argument("--remove-simulator-profiles-via-oee", "-r", action="store_true", dest="remove_simulator_profiles_via_oee", help="remove all simulator profiles using the OEE API provided by oee-bundle")
profile_generator_mode.add_argument("--delete-simulator-profiles", "-d", action="store_true", dest="delete_simulator_profiles", help="delete all simulator profiles using the C8Y inventory API (useful if oee-bundle is not working/available")
profile_generator_mode.add_argument("--create-categories", "-cat", action="store_true", dest="create_categories", help="create or update calculation categories")
profile_generator_mode.add_argument("--delete-categories", "-dcat", action="store_true", dest="delete_categories", help="delete all calculation categories")

args = parser.parse_args()
print(args)
def get_credentials():
    return args.baseurl, args.tenant_id, args.username, args.password, args.test

def get_profile_generator_mode():
    if args.create_profiles:
        return 'createProfiles'
    elif args.remove_simulator_profiles_via_oee:
        return 'removeSimulatorProfilesViaOee'
    elif args.delete_simulator_profiles:
        return 'deleteSimulatorProfiles'
    elif args.create_categories:
        return 'createCalculationCategories'
    elif args.delete_categories:
        return 'deleteCalculationCategories'

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