
# Profile Generator

Ensure you created simulators in the target tenant. See [README.md](README.md) for more details.

## Environemnt varibales

To run one of the scripts from command line you need set up following environement variables:

        C8Y_BASEURL=https://perftest.2.performance.c8y.io 
        C8Y_TENANT=t3233
        C8Y_USER=viktor.tymoshenko@softwareag.com
        C8Y_PASSWORD=yourpassword
        MOCK_C8Y_REQUESTS=false

## Generate profiles

Change PROFILES_PER_DEVIE variable to generate a wanted amount of profiles.

Since there are 7 simulators, The result amount of profiles will be 'PROFILES_PER_DEVIE * 7'

Use *event_based_simulators/main/profile_generator.py* to start profile generation.


## Delete profiles
Use *event_based_simulators/main/profile_deleter.py* to start profile generation

See comments at the end of the script file for more details

## Visual Studio Code

- Open *event-based-simulators* folder in the VSC.
- Install python plugin: ms-python.python
- copy [launch.json](misc/.vscode/launch.json) to *event-based-simulators/.vscode/* folder. The file contains few configuration to run python script with differnt environment varibales. 
- open profile_generator.py file
- click at the big run icon on the left toolbar(see [screenshot](images/vsc_run_python.png))
- select run profile you want to use. Every profile is configured for different tenant.
- click green run icon in the top area to run the currently opened python script.

