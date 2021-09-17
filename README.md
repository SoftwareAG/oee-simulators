# oee-simulators

Collection of simulators available for Cumulocity IoT OEE app. All simulators are available as Docker images and need to be deployed to the tenant where OEE app is running. Once deployed, the simulators automatically create preconfigured devices and start sending data. 

Simulators are needed to calculate OEE based on configuration profiles that can be setup in OEE app.

Prebuilt docker images can be downloaded from the [Releases](https://github.softwareag.com/IOTA/oee-simulators/releases) in this repository.

## ADAMOS Simulators

[simulator-dockers](simulator-dockers/) and [zeiss-simulator](zeiss-simulator/) have been implemented as part of the initial ADAMOS OEE project based on customer data. We do keep those for reference, but will be only maintaining [Generic event based Simulators](#generic-event-based-simulators).

## Generic event based Simulators

[Generic event based Simulators](event-based-simulators) are the simulators we do use for development and should be used for testing and demoing of Cumulocity IoT OEE app. The simulators have been designed and configured to simulate commonly seen machine types. A detailed description and how to configure calculation profiles in OEE app can be found in the [documentation](event-based-simulators).
