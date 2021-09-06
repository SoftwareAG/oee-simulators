
# OEE Simulators

Create predefined simulators for testing OEE-App in the Cumulocity. 

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
  

# [Profile Generator](profile_generator.md)



  