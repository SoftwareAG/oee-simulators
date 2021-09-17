# Event based simulators

This project offers two main features: 
- the oee-imulators microservice which creates some devices and periodically sends events for them
- the Profile Generator which allows creation of OEE Profiles from the command line

## Microservice oee-imulators

Creates simulators in Cumulocity based on the definitions in [simulators.json](main/simulators.json). Those simulators can be used for profiles in the OEE App. The currently supported simulators and the corresponding profiles are described [here](simulators.md).

Detailed feature list:
- automatically creates simulators based on JSON definition.
- uses externalId to identify Simulator. It avoids duplicating of similators by re-deploying/updating microservice.
- configurable externalId and label
- simulator can be disabled, in sense that no events will be sent
- the amount of events per hour can be configured either as a random number in a range
    ```
    "minHits": 5,
    "maxHits": 10
    ```
  or like a constant number: 
    ```
    "hits": 20
    ```
- the availibility of mashine is expressed as probability value with range from 0.0 to 1.0
- the timestamp of the following *Piece_ok" event is the same as corresponding *Piece_Produced" event.
- the expected quality of production is configurable. E.g. here 
    ```"type": "Piece_Produced",
              "hits": 25,
              "followedBy": {
                  "type": "Piece_Ok",
                  "hits": 20
              } 
    ```
  the expected quality would be 80%( *followedBy.hits/hits * 100%* )
- Simulates shutdowns(no events are sent if machine is DOWN)
- The all simulation logic is just one Python file and can be easily extended/improved if needed.
- [Python Script](profile_generator.md) for creating profiles for the simulators (every simulator needs a temlate with predefined name: <sim_id>_profile.template)

## [Profile Generator](profile_generator.md)

## Get project

 `git clone git@github.softwareag.com:IOTA/oee-simulators.git`

## Python

Install python 3.8.3+ on your system.

Probably you'll need install some packages using *pip* commmand.

## Build docker image

```bash
  git clone git@github.softwareag.com:IOTA/oee-simulators.git
  cd oee-simulators/event_based_simulators
  docker build -t oee-simulators .
  docker save -o image.tar oee-simulators
```
    
## Deployment

To deploy this project, zip image.tar and cumulocity.json to oee-simulators.zip and deploy it to the Cumulocity as Microservice.


## Development

The entry point is [event_based_simulators.py](main/event_based_simulators.py). The script reads simulator's defintions from [simulators.json](main/simulators.json) and create a new device for every entry. The *id* property in json is used as *extenral_id* in Cumulocity to avoid creating multiple devices by redeploying/updating script.

To mock REST API calls set the evnironment varibale *MOCK_C8Y_REQUESTS* to `true`

## Visual Studio Code

- Open *event-based-simulators* folder in the VSC.
- Install python plugin: ms-python.python
- adjust environemnt varibales in *.xcode/launch.json*. 
- open python file you want to run/debug
- click at the big run icon on the left toolbar
- select run profile you want to use.
- click green run icon in the top area to run the currently opened python script.
  



  