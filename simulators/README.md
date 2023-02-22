# Description OEE-Simulators

OEE-simulators offers these main features in [main](simulators/main): 
- the **oee-simulators microservice** which creates devices and sends data into Cumulocity.
- the **profile generator** to create/delete OEE calculation profiles from the command line.

There are extra features in [extras](simulators/extras):
- the **export profile data** to export Measurements or/and Alarms from OEE profiles into json data files.
- the **import data** to upload Measurements or/and Alarms from data json file to OEE profiles.

## Simulator Microservice

Creates simulators in Cumulocity based on the definitions in [simulators.json](main/simulator.json). Those simulators can be used for profiles in the OEE App. The currently supported simulators and the corresponding profiles are described [here](simulators.md).

Detailed feature list:
- configuration in JSON, no need to write code
- automatically creates devices and sends data
- identifies devices using a configurable `externalId`
- devices can be disabled to not send any events and measurements
- the number of events and measurements per hour can be configured as a random number in a range
    ```
    "minimumPerHour": 5,
    "maximumPerHour": 10
    ```
  or using a constant number: 
    ```
    "frequency": 20
    ```
- the availibility of machine is expressed as probability value with range from 0.0 to 1.0
- the timestamp of the following `Piece_ok` event is the same as corresponding `Piece_Produced` event
- the expected quality of production is configurable.  
    ```
    "type": "Piece_Produced",
    "frequency": 25,
    "followedBy": {
        "type": "Piece_Ok",
        "frequency": 20
    } 
    ```
  the expected quality would be 80% (*followedBy.frequency/frequency * 100%*)
- the kind of measurement that should be sent, can be defined by
    ```
    "type": "PumpPressure",
    "fragment": "Pressure",
    "series": "P",
    ```
  where "type" is optional and its default value is the value from the "fragment" property
- Simulates shutdowns (no events or measurements are sent if machine is DOWN)
- Written in Python and is easy to extend
- the main entry point is [simulator.py](main/simulator.py)
  - the script reads the configuration from [simulator.json](main/simulator.json) and creates a new device for every entry
  - the `id` property is used as `external_id` for the ManagedObjects to avoid creating multiple devices when redeploying/updating the microservice
- Simulators act according to given Shiftplans
  - Simulators are linked to shiftplans via locationId
  - Shiftplans are polled once a day
  - If a Simulator is not in Production time according to the given Shiftplan, it will not produce any  events
  - At startup [shiftplans.json](main/shiftplans.json) is parsed and used to update the given timeslots whitin the shiftplan
  - The `locationId's` presented in [shiftplans.json](main/shiftplans.json) are used to parse for all shiftplans used in the script and are the only shiftplans are considered for the polling

### Build the docker image

To build the docker image for this microservice, execute:
```
git clone git@github.softwareag.com:IOTA/oee-simulators.git
cd oee-simulators/simulators
docker build -t oee-simulators .
docker save -o image.tar oee-simulators
```
In [cumulocity.json](oee-simulators/simulators/cumulocity.json), change "version" from "@project.version@" to version number you want in format xx.xx.xx (example: "version": "12.20.11"). If you want to use the same version for multiple uploads, "latest" can be used in the last position (example: "version": "12.20.latest").
Then compress both the [cumulocity.json] and the newly created [image.tar] files into a ZIP file or execute the command below to create [oee-simulators.zip] file:
```
zip oee-simulators.zip image.tar cumulocity.json 
```
This zip file can then be uploaded as a Microservice to Cumulocity IoT.

### Creating profiles automatically

The creation of profiles can be configured using the Tenant Options on the given Cumulocity tenant. See the [Cumulocity REST API](https://cumulocity.com/api/10.14.0/#tag/Options) documentation for details. The Tenant Options must use the category: "simulators"

Some Options can be configured:
- CREATE_PROFILES - holds a string with 'CREATE' or 'CREATE_IF_NOT_EXISTS' to indicate if the profiles should be overwritten or only created if they not already exist. Default: 'CREATE_IF_NOT_EXISTS'
- CREATE_PROFILES_ARGUMENTS - can be used to set a string that is passed down as arguments to the profile creation script [Execution from command line / CLI arguments](#execution-from-command-line). 
- CREATE_ASSET_HIERARCHY - holds a boolean with 'true' or 'false' to indicate whether the Simulator should create the asset hierarchy for OEE. If set to true it will create one SITE with one LINE that holds all devices and their profiles. Default: 'false'
- LOG_LEVEL - sets the used logging-level of the simulator. Choose between INFO and DEBUG. DEBUG does give a more detailed output of the Simulator's configuration and decisions. Default: 'INFO'
- DELETE_PROFILES - Holds a boolean either 'True' or 'False' to indicate whether OEE_Profiles created by the simulator should be deleted beforehand.

Note: A profile will be created and activated only if no other profiles are already defined for the particular device.

### Deployment

To deploy this project, upload the zip file to the Cumulocity as Microservice. The zip file can be created locally as described above or downloaded from the [releases](releases) section.

## Profile generator

The Profile Generator is a [Python script](main/profile_generator.py) that creates OEE calculation profiles for each simulator available in the tenant. Every simulator needs a template with appropriate name (<external_id>_profile.template) in your local [main](main/profile_templates) folder. The simulators must have been created beforehand by deploying the [oee-simulators](#simulator-microservice) microservice.

### Environment

Install python 3.8.3+ on your system. Probably you'll need install some packages using *pip* commmand, e.g.
```
pip install requests
```

To run the scripts the following environment variables need to be set:

```
C8Y_BASEURL=https://perftest.2.performance.c8y.io 
C8Y_TENANT=t3233
C8Y_USER=viktor.tymoshenko@softwareag.com
C8Y_PASSWORD=yourpassword
```

Additionally the following optional/debug variables can be set:
```
MOCK_C8Y_REQUESTS=false
PROFILES_PER_DEVICE=1
```

- if MOCK_C8Y_REQUESTS is set to true, no requests to the C8Y tenant are executed, but you can see what would have been executed in the log
- if PROFILES_PER_DEVICE is increased, more than one profile is created for each simulator; this might be useful when doing performance/scalability tests

### Execution

There are two ways to execute the profile generation. You can run it from the development environment [Visual Studio Code](#visual-studio-code) or from the command line.

#### Execution from command line
To execute the scripts from command line, open a command prompt and the *oee-simulators\simulators* folder.

To create profiles, execute:
```
python .\main\profile_generator.py -c
``` 

To remove profiles using the OEE API, execute:
```
python .\main\profile_generator.py -r
``` 

To remove profiles using the standard Cumulocity IoT API (e.g. if OEE is not installed on the tenant), execute:
```
python .\main\profile_generator.py -d
``` 

#### Execution in Visual Studio Code

- Open *simulators* folder in the VSC
- Install python plugin: ms-python.python
- adjust environemnt varibales in [.vscode/.env](.vscode/.env)
- click at the big run/debug icon in the left toolbar
- select the configuration that you want to use from the dropdown: `create profiles`, `remove simulator profiles via OEE API`, `delete simulator profiles`
- click the small green run/debug icon left of the dropdown in the top area to execute the configuration
  



  
