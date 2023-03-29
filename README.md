# oee-simulators

Collection of simulators available for Cumulocity IoT OEE app. All simulators are available as Docker images and need to be deployed to the tenant where OEE app is running. Once deployed, the simulators automatically create preconfigured devices and start sending data. 

[Generic Simulators](simulators) are the simulators we do use for development and should be used for testing and demoing of Cumulocity IoT OEE app. The simulators have been designed and configured to simulate commonly seen machine types. A detailed description of [supported machine types](simulators/simulators.md) and [how to configure calculation profiles](simulators/simulators.md#oee-profile-settings-for-simulators) in OEE app can be found in the [simulators](simulators) project.

Simulators are needed to calculate OEE based on configuration profiles that can be setup in OEE app.

Prebuilt docker images can be downloaded from the [Releases](https://github.softwareag.com/IOTA/oee-simulators/releases) in this repository.

# unit test 
Collection of test for the [Generic Simulators](simulators)

To run specific test script:
```
python test/[script-name].py  [-h] [--tenant TENANT] [--password PASSWORD] [--baseurl BASEURL] [--user USER]
```
<pre>
Cumulocity platform credentials setup

optional arguments:<br>
  long syntax          |    short syntax    |   Functions
------------------------------------------------------------------------------------------
  --help,              |    -h              |   show help message and exit
  --tenant TENANT,     |    -t TENANT       |    Tenant ID
  --password PASSWORD, |    -p PASSWORD     |    C8Y Password
  --baseurl BASEURL,   |    -b BASEURL      |    C8Y Baseurl
  --user USER,         |    -u USER         |    C8Y Username

The <strong><ins>arguments</strong></ins> for the script are <strong><ins>optional</strong></ins>, but if you choose to input any of them, it is important to note that <strong><ins>all four arguments: Tenant ID, C8Y Password, C8Y Baseurl, and C8Y Username must be filled</ins></strong>. 
Failure to provide any of these fields may cause the script to malfunction or produce unexpected results. 
</pre>
------------------------------

These tools are provided as-is and without warranty or support. They do not constitute part of the Software AG product suite. Users are free to use, fork and modify them, subject to the license agreement. While Software AG welcomes contributions, we cannot guarantee to include every contribution in the master project.
