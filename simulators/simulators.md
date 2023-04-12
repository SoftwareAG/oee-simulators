## Event based Simulators

The simulators will create machines sending events and measurements required to configure Cumulocity IoT OEE app to calculate **OEE** from **Availability**, **Performance** and **Quality**.

### Simulated Devices

#### 1. Normal #1
- **Availability**: the simulator produces an `Availability` event which has a field `status` that is either `up` or `down`. This event is produced 5-10 times per hour with 90% being `up`.
- **Performance**: the simulator produces an event `Piece_Produced`. The event is produced about 25 times per hour. 
- **Quality**: the simulator produces a `Piece_Ok` event. The event is produced about 20 times per hour. Those events follow a few seconds after a corresponding `Piece_Produced` event (both events have the same timestamp). Some `Piece_Produced` events are not followed by a `Piece_Ok` event (to simulate a piece with bad quality).

#### 2. Normal #2
- **Availability**: the simulator produces an `Availability` event which has a field `status` that is either `up` or `down`. This event is produced 5-10 times per hour with 90% being `up`.
- **Performance**: the simulator produces an event `Pieces_Produced`. It contains a field named `count` with values ranging from 0-10. The event is produced 6 times per hour (every 10 min). 
- **Quality**: the simulator produces a `Pieces_Ok` event. It contains a field named `count` with values ranging from 0-10. Those events follow a few seconds after a corresponding `Pieces_Produced` event (both events have the same timestamp). The value for `count` might be lower than the value in `Pieces_Produced.count` (to simulate a piece with bad quality).

#### 3. ormal #3
- **Availability**: the simulator produces an `Availability` event which has a field `status` that is either `up` or `down`. This event is produced 5-10 times per hour with 90% being `up`.
- **Performance**: the simulator produces an event `Pieces_Produced`. It contains a field named `count` with values ranging from 0-10. The event is produced 6 times per hour (every 10 min). 
- **Quality**: the simulator produces an event `Piece_Quality`. These have a field `status` that is either `ok` or `nok`. There is 2-3 of these with 90% of the time being in state `ok`.

#### 4. Normal with Short Shutdowns
- **Short Shutdowns**: is enabled and set to 2 minutes.
- **Availability**: the simulator produces an `Availability` event which has a field `status` that is either `up` or `down`. This event is produced 5-10 times per hour with 90% being `up`. There is a few short shutdowns with the machine being in `down` less than 2 minutes.
- **Performance**: the simulator produces an event `Piece_Produced`. The event is produced about 25 times per hour. 
- **Quality**: the simulator produces a `Piece_Ok` event. The event is produced about 20 times per hour. Those events follow a few seconds after a corresponding `Piece_Produced` event (both events have the same timestamp). Some `Piece_Produced` events are not followed by a `Piece_Ok` event (to simulate a piece with bad quality).

#### 5. Slow Producer
- **Availability**: the simulator produces an `Availability` event which has a field `status` that is either `up` or `down`. This event is produced 5-10 times per hour with 90% being `up`.
- **Performance**: the simulator produces an event `Piece_Produced`. The event is produced about every 4h.
- **Quality**:  the simulator produces an event `Piece_Ok`. The event is produced shortly after the `Piece_Produced` event (both events have the same timestamp). There is always one `Piece_Produced` for a `Piece_Ok` event, which results in a quality of 100%.

#### 6. High Frequency Availability
- **Availability**: the simulator produces an `Availability` event which has a field `status` that is either `up` or `down`. This event is produced every 10s. Most of the time the status does not change and it is 90% up.
- **Performance**: the simulator produces an event `Piece_Produced`. The event is produced about 25 times per hour. 
- **Quality**: the simulator produces a `Piece_Ok` event. The event is produced about 20 times per hour. Those events follow a few seconds after a corresponding `Piece_Produced` event (both events have the same timestamp). Some `Piece_Produced` events are not followed by a `Piece_Ok` event (to simulate a piece with bad quality).

#### 7. Slow Producer + High Frequency Availability (SP + HFA)
- **Availability**: the simulator produces an `Availability` event which has a field `status` that is either `up` or `down`. This event is produced every 10s. Most of the time the status does not change and it is 90% up.
- **Performance**: the simulator produces an event `Piece_Produced`. The event is produced about every 4h.
- **Quality**:  the simulator produces an event `Piece_Ok`. The event is produced shortly after the `Piece_Produced` event (both events have the same timestamp). There is always one `Piece_Produced` for a `Piece_Ok` event, which results in a quality of 100%.

#### 8. Ideal Producer
- **Availability**: the simulator produces an `Availability` event which has a field `status` that is always `up`, which results in an availability of 100%.
- **Performance**: the simulator produces an event `Piece_Produced`. The event is produced 60 times per hour, which results in a performance of 100%. 
- **Quality**:  the simulator produces an event `Piece_Ok`. The event is produced shortly after the `Piece_Produced` event (both events have the same timestamp). There is always one `Piece_Produced` for a `Piece_Ok` event, which results in a quality of 100%.

#### 9. Ideal Producer Q80
- **Availability**: the simulator produces an `Availability` event which has a field `status` that is always `up`, which results in an availability of 100%.
- **Performance**: the simulator produces an event `Piece_Produced`. The event is produced 60 times per hour, which results in a performance of 100%. 
- **Quality**:  the simulator produces an event `Piece_Ok`. The event might be produced with probability 80% shortly after the `Piece_Produced` event (both events have the same timestamp), which results in a quality of 80%.

#### 10. Ideal Producer A80
- **Availability**: the simulator produces an `Availability` event which has a field `status` that is 80% of time is `up`, which results in an availability of 80%.
- **Performance**: the simulator produces an event `Piecec_Produced`. The event is produced 60 times per hour and it contains a field named `count` with value 5. The summary amount of events per hour is 300. 
- **Quality**: the simulator produces a `Pieces_Ok` event. It contains a field named `count` with value 5. Those events follow a few seconds after a corresponding `Pieces_Produced` event (both events have the same timestamp). The summary amount of quality pieces is also 300 per hour, which results in a quality of 100%.

#### 11. Ideal Producer with Categories
- **Availability**: the simulator produces an `Availability` event which has a field `status` that is 90% of time is `up`, 7% `Planned maintenance`, 3% `Manual stop`, which results in an availability of 90%.
- **Performance**: the simulator produces an event `Pieces_Produced`. The event is produced 60 times per hour and it contains fields named `piecesMinimumPerProduction` and `piecesMaximumPerProduction` with value 5. The summary amount of events per hour is 60 which results in the amount of production pieces is 300 per hours. 
- **Quality**: the simulator produces a `Pieces_Ok` event. It contains fields named `piecesMinimumPerProduction` and `piecesMaximumPerProduction` with value 5. Those events follow a few seconds after a corresponding `Pieces_Produced` event (both events have the same timestamp). The summary amount of quality pieces is also 300 per hour, which results in a quality of 100%.  

### OEE profile settings for simulators

Labels not mentioned explicitly in the following table, such as for example `Profile Name`, `Machine Location` or `Workpiece Name`, can be arbitrary values as they don't have any influence on the calculation. 

For all calculation profiles we recommend at least 2 `Resolution` intervals: 
- *30 minutes*
- *1 hour* 
  
Additionally 10 minutes default interval will be available for all profiles, even if not explicitly configured. 

The computation method is `PPQ` for all profiles. Matching settings for each profile are described in the table below. All values for `Resolution` and `Goals` are recommendations and could be changed according to the use case.

| Simulator                      | Workpiece         | Matching                                                                                                                                                                                    | Goals (OEE, Availability, Performance, Quality)          | Other                       |
| ------------------------------ | ----------------- |---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------|-----------------------------|
| Normal #1                      | 25 pcs per hour   | APA: Event count `Piece_Produced`<br />APT: Value from event: `Availability` = String `up`<br />AQA: Event count `Piece_Ok`                                                                 | 80, 80, 80, 80                                           |                             |
| Normal #2                      | 1 pcs per min     | APA: Value from event `Pieces_Produced` count<br />APT: Value from event: `Availability` = String `up`<br />AQA: Value from event `Pieces_Ok` count                                         | 80, 80, 80, 80                                           |                             |
| Normal #3                      | 60 pcs per hour   | APA: Value from event `Pieces_Produced` count<br />APT: Value from event: `Availability` = String `up`<br />AQA: Value from event `Piece_Quality` = `ok`                                    | 20, 90, 50, 90                                           |                             |
| Normal with Short Shutdowns    | 25 pcs per hour   | APA: Event count `Piece_Produced`<br />APT: Value from event: `Availability` = String `up`<br />AQA: Event count `Piece_Ok`                                                                 | 60, 90, 90, 90                                           | Short stoppages: 3 min      |
| Slow Producer                  | 0.25 pcs per hour | APA: Event count `Piece_Produced`<br />APT: Value from event: `Availability` = String `up`<br />AQA: Event count `Piece_Ok`                                                                 | 90, 90, 100, 100                                         | Resolution: 4 hours, 1 days |
| High Frequency Availability    | 25 pcs per hour   | APA: Event count `Piece_Produced`<br />APT: Value from event: `Availability` = String `up`<br />AQA: Event count `Piece_Ok`                                                                 |  60, 90, 90, 80                                          |                             |
| SP + HFA                       | 0.25 pcs per hour | APA: Event count `Piece_Produced`<br />APT: Value from event: `Availability` = String `up`<br />AQA: Event count `Piece_Ok`                                                                 | 90, 90, 100, 100                                         | Resolution: 4 hours, 1 days |
| Ideal Producer                 | 60 pcs per hour   | APA: Event count `Piece_Produced`<br />APT: Value from event: `Availability` = String `up`<br />AQA: Event count `Piece_Ok`                                                                 | 100, 100, 100, 100                                       |                             |
| Ideal Producer Q80             | 60 pcs per hour   | APA: Event count `Piece_Produced`<br />APT: Value from event: `Availability` = String `up`<br />AQA: Event count `Piece_Ok`                                                                 | 80, 100, 100, 80                                         |                             |
| Ideal Producer A80             | 300 pcs per hour  | APA: Value from event `Pieces_Produced` count<br />APT: Value from event: `Availability` = String `up`<br />AQA: Value from event `Pieces_Ok` count                                         | 80, 80, 100, 100                                         |                             |
| Ideal Producer with Categories | 300 pcs per hour  | APA: Value from event `Pieces_Produced` count<br />APT: Value from event: `Availability` = String `up`, `Planned maintenance`, `Manual stop`<br />AQA: Value from event `Pieces_Ok` count   | 90, 90, 100, 100                                         |                             |

- APA: Actual Production Amount
- APT: Actual Production Time (enable *define machine status event*)
- AQA: Actual Quality Amount
