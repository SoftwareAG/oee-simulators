# Required
C8Y_BASE = 'http://localhost:8080'
C8Y_TENANT = 't100'
C8Y_USER = 'test'
C8Y_PASSWORD = 'test'

# Optional
ACTION = 'export'  # 'import': upload json file in export_data to c8y, 'export': export data from c8y to json file
MODE = 'specific'  # 'all': export all measurements or alarms data from c8y, 'specific': export only data from chosen device
DATA_TYPE = 'alarms'  # 'alarms': export alarms data, 'measurements': export measurements data
DEVICE_NAME = 'Normal #1'  # Choose a device name in device management to extract data in 'specific' mode
