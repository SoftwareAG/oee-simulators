### Required
C8Y_BASE = 'http://localhost:8080'
C8Y_TENANT = ''
C8Y_USER = ''
C8Y_PASSWORD = ''

### Optional
# Input None if not set
DATA_TYPE = 'all'  # 'alarms': export alarms data, 'measurements': export measurements data, 'all' export both
DEVICE_ID = None   # Input device ID(s) (i.e. DEVICE_ID = 123456, 234567) or set to None

# Set one of these two sections and None to all of the others
############################
# Extract data with periods#
############################
TIME_UNIT = 'hours'  # weeks, days, hours, minutes, seconds
PERIOD_TO_EXPORT = 4
####################################
# Extract data with exact milestone#
####################################
CREATE_FROM = None
CREATE_TO = None
