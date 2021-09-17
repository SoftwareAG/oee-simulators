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
- [Python Script](profile_generator.md) to create OEE calculation profiles for the simulators (every simulator needs a temlate with predefined name: <sim_id>_profile.template)

## Profile generator

To use the profile generator, the *oee-simulators microservice* needs to be deployed and devices have to be available in the tenant.

### Environment variabels

To run the scripts the following environment variables need to be set:

```
C8Y_BASEURL=https://perftest.2.performance.c8y.io 
C8Y_TENANT=t3233
C8Y_USER=viktor.tymoshenko@softwareag.com
C8Y_PASSWORD=yourpassword
MOCK_C8Y_REQUESTS=false
PROFILES_PER_DEVICE=1
```

### Generate profiles

Change `PROFILES_PER_DEVICE` variable to generate a given number of profiles. There will be a profile created per device. As there are 7+ simulators, the result amount of profiles will be 'PROFILES_PER_DEVICE * 7'.

To generate profiles run
```
event_based_simulators/main/profile_generator.py
``` 

To delete profiles run
```event_based_simulators/main/profile_deleter.py```

See comments at the end of the script file for more details.

## Build the project

### Python

Install python 3.8.3+ on your system. Probably you'll need install some packages using *pip* commmand.

### Build docker image

```
git clone git@github.softwareag.com:IOTA/oee-simulators.git
cd oee-simulators/event_based_simulators
docker build -t oee-simulators .
docker save -o image.tar oee-simulators
```
    
### Deployment

To deploy this project, zip image.tar and cumulocity.json to oee-simulators.zip and deploy it to the Cumulocity as Microservice.


## Development

The entry point is [event_based_simulators.py](main/event_based_simulators.py). The script reads simulator's defintions from [simulators.json](main/simulators.json) and creates a new device for every entry. The `id` property in json is used as `extenral_id` in Cumulocity to avoid creating multiple devices by redeploying/updating script.

To mock REST API calls set the evnironment varibale `MOCK_C8Y_REQUESTS` to `true`

## Visual Studio Code

- Open *event-based-simulators* folder in the VSC.
- Install python plugin: ms-python.python
- adjust environemnt varibales in *.xcode/launch.json*. 
- open python file you want to run/debug
- click at the big run icon on the left toolbar
- select run profile you want to use.
- click green run icon in the top area to run the currently opened python script.
  



  