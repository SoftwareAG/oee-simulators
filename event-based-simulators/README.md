# Generic event based Simulators

This project offers two main features: 
- the **oee-simulators microservice** which creates devices and sends data into Cumulocity
- the **profile generator** to create OEE calculation profiles from the command line

## Simulator Microservice

Creates simulators in Cumulocity based on the definitions in [simulators.json](main/simulators.json). Those simulators can be used for profiles in the OEE App. The currently supported simulators and the corresponding profiles are described [here](simulators.md).

Detailed feature list:
- configuration in JSON, no need to write code
- automatically creates devices and sends data
- identifies devices using a configurable `externalId`
- devices can be disabled to not send any events
- the number of events per hour can be configured as a random number in a range
    ```
    "minHits": 5,
    "maxHits": 10
    ```
  or using a constant number: 
    ```
    "hits": 20
    ```
- the availibility of machine is expressed as probability value with range from 0.0 to 1.0
- the timestamp of the following `Piece_ok` event is the same as corresponding `Piece_Produced` event
- the expected quality of production is configurable.  
    ```
    "type": "Piece_Produced",
    "hits": 25,
    "followedBy": {
        "type": "Piece_Ok",
        "hits": 20
    } 
    ```
  the expected quality would be 80% (*followedBy.hits/hits * 100%*)
- Simulates shutdowns (no events are sent if machine is DOWN)
- Written in Python and is easy to extend
- the main entry point is [event_based_simulators.py](main/event_based_simulators.py)
  - the script reads the configuration from [simulators.json](main/simulators.json) and creates a new device for every entry
  - the `id` property is used as `external_id` for the ManagedObjects to avoid creating multiple devices when redeploying/updating the microservice

### Build the docker image

To build the docker image for this microservice, execute:
```
git clone git@github.softwareag.com:IOTA/oee-simulators.git
cd oee-simulators/event_based_simulators
docker build -t oee-simulators .
docker save -o image.tar oee-simulators
zip oee-simulators.zip image.tar cumulocity.json 
```

### Creating profiles automatically

The creation of profiles can be configured using the tenant options on the given c8y tenant. 
Tenant options should fall under the category-name: "event-based-simulators"

Two Options can be configured:
- CREATE_PROFILES - holds a boolean with 'true' or 'false' to indicate if the profiles should be created. Default: 'false'
- CREATE_PROFILES_ARGUMENTS - can be used to set a string that is passed down as arguments to the profile creation script [Execution from command line / CLI arguments](#execution-from-command-line). 

Note: A profile will be created and activated only if no other profiles are already defined for the particular device.

### Deployment

To deploy this project, upload the zip file to the Cumulocity as Microservice. The zip file can be created locally as described above or downloaded from the [releases](releases) section.

## Profile generator

The Profile Generator is a [Python script](main/profile_generator.py) that creates OEE calculation profiles for each simulator available in the tenant. Every simulator needs a template with appropriate name (<external_id>_profile.template) in your local [main](main/) folder. The simulators must have been created beforehand by deploying the [oee-simulators](#simulator-microservice) microservice.

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
To execute the scripts from command line, open a command prompt and the *oee-simulators\event-based-simulators* folder.

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

- Open *event-based-simulators* folder in the VSC
- Install python plugin: ms-python.python
- adjust environemnt varibales in [.vscode/.env](.vscode/.env)
- click at the big run/debug icon in the left toolbar
- select the configuration that you want to use from the dropdown: `create profiles`, `remove simulator profiles via OEE API`, `delete simulator profiles`
- click the small green run/debug icon left of the dropdown in the top area to execute the configuration
  



  