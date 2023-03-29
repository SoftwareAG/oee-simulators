# OEE-simulators

Collection of simulators available for Cumulocity IoT OEE app. All simulators are available as Docker images and need to be deployed to the tenant where OEE app is running. Once deployed, the simulators automatically create preconfigured devices and start sending data. 

[Generic Simulators](simulators) are the simulators we do use for development and should be used for testing and demoing of Cumulocity IoT OEE app. The simulators have been designed and configured to simulate commonly seen machine types. A detailed description of [supported machine types](simulators/simulators.md) and [how to configure calculation profiles](simulators/simulators.md#oee-profile-settings-for-simulators) in OEE app can be found in the [simulators](simulators) project.

Simulators are needed to calculate OEE based on configuration profiles that can be setup in OEE app.

Prebuilt docker images can be downloaded from the [Releases](https://github.softwareag.com/IOTA/oee-simulators/releases) in this repository.

# Tests 
Collection of test for the [Generic Simulators](simulators)

To run specific test script:
```
python test/[script-name].py  [-h] [--tenant-id TENANT_ID] [--password PASSWORD] [--baseurl BASEURL] [--username USER]
```
<pre>
Cumulocity platform credentials setup

optional arguments:<br>
  long syntax                |    short syntax       |   Functions
------------------------------------------------------------------------------------------
  --help,                    |    -h                 |   show help message and exit
  --tenant-id TENANT_ID,     |    -t TENANT_ID       |   Tenant ID
  --password PASSWORD,       |    -p PASSWORD        |   C8Y Password
  --baseurl BASEURL,         |    -b BASEURL         |   C8Y Baseurl
  --username USER,           |    -u USER            |   C8Y Username

It is important to note that <strong><ins>all four arguments: Tenant ID, C8Y Password, C8Y Baseurl, and C8Y Username must be filled</ins></strong>. 
Failure to provide any of these fields may cause the script to malfunction or produce unexpected results.
</pre>

If you don't want to input arguments, you can set environment variables need to be set in [cumulocityAPI.py](simulators/main/cumulocityAPI.py) in order to run [simulators_test.py](test/simulators_test.py). <br>
For example:
```
C8Y_BASEURL=https://test.development.c8y.io 
C8Y_TENANT=t123
C8Y_USER=yourusername
C8Y_PASSWORD=yourpassword
```

If you run the [export_import_test.py](test/export_import_test.py), besides environment variables in [cumulocityAPI.py](main/cumulocityAPI.py), you must set environment variables also in [Environment.py](simulators/extras/Environment.py).
Because they use both [extra](simulators/extras) and [main](simulators/main) parts of simulators which are independent to each other.
<br>

------------------------------

These tools are provided as-is and without warranty or support. They do not constitute part of the Software AG product suite. Users are free to use, fork and modify them, subject to the license agreement. While Software AG welcomes contributions, we cannot guarantee to include every contribution in the master project.
