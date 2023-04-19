# Description OEE-Simulators

OEE-simulators offers these main features in [main](main): 
- the **oee-simulators microservice** which creates devices and sends data into Cumulocity.
- the **profile generator** to create/delete OEE calculation profiles from the command line.

There are extra features in [extras](extras):
- the **export profile data** to export Measurements or/and Alarms from OEE profiles into json data files.
- the **import data** to upload Measurements or/and Alarms from data json file to OEE profiles.

## Simulator Microservice
Detailed feature list:
- configuration in JSON, no need to write code.
- automatically creates devices and sends data.
- identifies devices using a configurable `externalId`.
- devices can be disabled to not send any events and measurements.
- Written in python which can be modified easily for further development.
- Simulators work based on status and shift that it is assigned.

### Simulator definition
Creating simulators in Cumulocity based on the definitions in [simulators.json](main/simulator.json). Those simulators can be used for profiles in the OEE App. The currently supported simulators and the corresponding profiles are described [here](simulators.md).


Example for a simulator definition:
```
  [
    {
        "type": "Simulator",
        "id": "sim_001",
        "label": "Normal #1",
        "enabled": true,
        "events": [
            {
                "type": "Availability",
                "minimumPerHour": 5,
                "maximumPerHour": 10,
                "status": ["up", "down"],
                "probabilities": [0.9, 0.1],
                "durations": [0, 0],
                "forceStatusDown": true
            }
        ],
        "measurements": [
            {
                "type": "PumpPressure",
                "fragment": "Pressure",
                "series": "P",
                "unit": "hPa",
                "valueDistribution": "uniform",
                "minimumValue": 1000.0,
                "maximumValue": 1500.0,
                "minimumPerHour": 4.0,
                "maximumPerHour": 4.0
            }
        ]
    }
  ]
```

- the number of **events** and **measurements** **per hour** can be configured as a random number in a range
    ```
    "minimumPerHour": 5,
    "maximumPerHour": 10
    ```
  or using a constant number: 
    ```
    "frequency": 20
    ```
  
- the availability of machine is expressed as probability value `probabilities` with range from 0.0 to 1.0. The `probabilities` is an array which has correspondence with the `status` array.
  ```
    "status": ["up", "down"],
    "probabilities": [0.9, 0.1]
  ```
  In this case, the up status has 90% to happen and the down status has the remain 10%.

- the timestamp of the following `Piece_ok` event is the same as corresponding `Piece_Produced` event
  - the expected quality of production is configurable.  
  ```
    "events": [
      "type": "Piece_Produced",
      "frequency": 25,
      "followedBy": {
          "type": "Piece_Ok",
          "frequency": 20
      }
    ]
  ```
    the expected quality would be 80% (*followedBy.frequency/frequency * 100%*)
- For the `Pieces_Produced`, the simulator produces multiple pieces at a time so the minimum (`piecesMinimumPerProduction`) and maximum pieces per production (`piecesMaximumPerProduction`) must be set
  ```
    "type": "Pieces_Produced",
    "frequency": 6,
    "piecesMinimumPerProduction": 1,
    "piecesMaximumPerProduction": 10,
    "followedBy": {
        "type": "Pieces_Ok",
        "piecesMinimumPerProduction": 0,
        "piecesMaximumPerProduction": 10,
        "frequency": 6
    }
  ```
  - the kind of measurement that should be sent, can be defined by
      ```
      "measurements": [
          "type": "PumpPressure",
          "fragment": "Pressure",
          "series": "P"
      ]
      ```
    where "type" is optional and its default value is the value from the "fragment" property.
  
  - In measurements, `valueDistribution` is defined to let the simulator know which distribution formula to use to generate measurements. There are three choices that can be defined here: `uniform`, `uniformint`, `normal`.

- Simulates shutdowns (no events or measurements are sent if simulator is DOWN or out of shift)

- the main entry point is [simulator.py](main/simulator.py)
  - the script reads the configuration from [simulator.json](main/simulator.json) and creates a new device for every entry
  - the `id` property is used as `external_id` for the ManagedObjects to avoid creating multiple devices when redeploying/updating the microservice
  
    - Simulators act according to given Shiftplans
      - Simulators are linked to shiftplans via locationId.
      - The `locationId` presented in [shiftplans.json](main/shiftplans.json) are used to parse for all shiftplans used in the script but only a specific shiftplan is applied to a simulator if it has the `locationId` of a shift defined.
        ```
        {
          "type": "Simulator",
          "id": "sim_012",
          "label": "Normal #12 with short shifts",
          "locationId": "ShortShiftsLocation",
          "enabled": true
        }
        ```
        In this example, the ShortShiftsLocation shift is applied to the simulator sim_012.
      - If a Simulator is not in Production time according to the given Shiftplan, it will not produce any events and measurements.
      - At startup [shiftplans.json](main/shiftplans.json) is parsed once and the shifts are created accordingly (if they do not exist).
      - Everytime an event/measurement is about to be sent, the script checks if the status of the locationId equals PRODUCTION; and only if the status is correct, the event/measurement is sent.
      - Since the status of shiftplans is checked in realtime, if there are any changes to the shiftplans, they are taken into account.


### Shiftplan definition
```
  [
    {
      "locationId": "OneShiftLocation",
      "recurringTimeslots": [
        { "id": "OneShiftLocation-DayShift", "seriesPostfix": "DayShift", "slotType": "PRODUCTION", "slotStart": "2022-07-13T08:00:00Z", "slotEnd": "2022-07-13T16:00:00Z", "description": "Day Shift", "active": true, "slotRecurrence": { "weekdays": [1, 2, 3, 4, 5] } },
        { "id": "OneShiftLocation-Break", "slotType": "BREAK", "slotStart": "2022-07-13T12:00:00Z", "slotEnd": "2022-07-13T12:30:00Z", "description": "Day Shift Break", "active": true, "slotRecurrence": { "weekdays": [1, 2, 3, 4, 5] } }
      ]
    },
    {...}
  ]
```
This is an example of a shiftplan which contains a shift name `OneShiftLocation` in `locationId` field.
The `recurringTimeslots` field is an array which define components of the shift. In this case, this shift has two parts: 
  - `OneShiftLocation-DayShift` is the shift for `PRODUCTION`, in which the applied simulators will generate events and measurements. The length of the shift is defined by the abstraction between `slotEnd` and `slotStart` and the `active` field is set to true means that this component of the shift is activated. The field `slotRecurrence` defined which day of the week can the applied simulators work. `""weekdays": [1, 2, 3, 4, 5]` means the applied simulators will work from Monday to Friday.
  - `OneShiftLocation-Break` is the shift for `BREAK`, in which the applied simulators will not generate events and measurements. The other setup is the same as above.

**Only `recurringTimeslots` is supported**, `timeslots` is not support.

### Build the docker image

To build the docker image for this microservice, execute:
```
git clone git@github.softwareag.com:IOTA/oee-simulators.git
cd oee-simulators/simulators
docker build -t oee-simulators .
docker save -o image.tar oee-simulators
```
In [cumulocity.json](cumulocity.json), change "version" from "@project.version@" to version number you want in format xx.xx.xx (example: "version": "12.20.11"). If you want to use the same version for multiple uploads, "latest" can be used in the last position (example: "version": "12.20.latest").
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

To deploy this project, upload the zip file to the Cumulocity as Microservice. The zip file can be created locally as described above or downloaded from the [releases](https://github.com/SoftwareAG/oee-simulators/releases) section.

## Profile generator

The Profile Generator is a [Python script](main/profile_generator.py) that creates OEE calculation profiles for each simulator available in the tenant. Every simulator needs a template with appropriate name (<external_id>_profile.template) in your local [main](main/profile_templates) folder. The simulators must have been created beforehand by deploying the [oee-simulators](#simulator-microservice) microservice.

### Environment

Install python 3.8.3+ on your system. Probably you'll need install some packages using *pip* commmand, e.g.
```
pip install requests
```

To run the scripts the following environment variables need to be set in [cumulocityAPI.py](main/cumulocityAPI.py):

```
C8Y_BASEURL=https://test.development.c8y.io 
C8Y_TENANT=t123
C8Y_USER=yourusername
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
  



  
