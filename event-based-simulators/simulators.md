Back to [README.md](README.md)

## Supported Simulators

### Normal #1
- **Availability**: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation checks if the value of this field is “up”. This event is produced 5-10 times per hour with 90% being “up”.
- **Performance**: the simulator produces an event “Piece_Produced”. The calculation counts these. The event is produced about 25 times per hour. 
- **Quality**: the simulator produces a “Piece_Ok” event. The calculation counts these. The event is produced about 20 times per hour. Those events follow a few seconds after a corresponding “Piece_Produced” event (both events have the same timestamp). Some “Piece_Produced” events are not followed by a “Piece_Ok” event (to simulate a piece with bad quality).

### Normal #2
- **Availability**: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation checks if the value of this field is “up”. This event is produced 5-10 times per hour with 90% being “up”.
- **Performance**: the simulator produces an event “Pieces_Produced”. It contains a field named “count” with values ranging from 0-10. The calculation sums up the values of this field. The event is produced 6 times per hour (every 10 min). 
- **Quality**: the simulator produces a “Piece_Ok” event. The calculation counts these. The event is produced about 20 times per hour. Those events follow a few seconds after a corresponding “Piece_Produced” event (both events have the same timestamp). Some “Piece_Produced” events are not followed by a “Piece_Ok” event (to simulate a piece with bad quality).

### Normal #3
- **Availability**: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation checks if the value of this field is “up”. This event is produced 5-10 times per hour with 90% being “up”.
- **Performance**: the simulator produces an event “Pieces_Produced”. It contains a field named “count” with values ranging from 0-10. The calculation sums up the values of this field. The event is produced 6 times per hour (every 10 min). 
- **Quality**: the simulator produces an event “Piece_Quality”. These have a field “status” that is either “ok” or “nok”. The calculation is a quality status event checking that the value is “ok”. There is 2-3 of these with 90% of the time being in state “ok”.

### Normal with Short Shutdowns
- **Short Shutdowns**: is enabled and set to 2 minutes.
- **Availability**: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation checks if the value of this field is “up”. This event is produced 5-10 times per hour with 90% being “up”. There is a few short shutdowns with the machine being in “down” less than 2 minutes.
- **Performance**: the simulator produces an event “Piece_Produced”. The calculation counts these. The event is produced about 25 times per hour. 
- **Quality**: the simulator produces a “Piece_Ok” event. The calculation counts these. The event is produced about 20 times per hour. Those events follow a few seconds after a corresponding “Piece_Produced” event (both events have the same timestamp). Some “Piece_Produced” events are not followed by a “Piece_Ok” event (to simulate a piece with bad quality).

### Slow Producer
- **Availability**: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation checks if the value of this field is “up”. This event is produced 5-10 times per hour with 90% being “up”.
- **Performance**: the simulator produces an event “Piece_Produced”. The calculation counts these. The event is produced about every 4h.
- **Quality**:  the simulator produces an event “Piece_Ok”. The calculation counts these. The event is produced shortly after the “Piece_Produced” event (both events have the same timestamp). There is always one “Piece_Produced” for a “Piece_Ok” event, which results in a quality of 100%.

### High Frequency Availability
- **Availability**: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation checks if the value of this field is “up”. This event is produced every 10s. Most of the time the status does not change and it is 90% up.
- **Performance**: the simulator produces an event “Piece_Produced”. The calculation counts these. The event is produced about 25 times per hour. 
- **Quality**: the simulator produces a “Piece_Ok” event. The calculation counts these. The event is produced about 20 times per hour. Those events follow a few seconds after a corresponding “Piece_Produced” event (both events have the same timestamp). Some “Piece_Produced” events are not followed by a “Piece_Ok” event (to simulate a piece with bad quality).

### Slow Producer + High Frequency Availability
- **Availability**: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation checks if the value of this field is “up”. This event is produced every 10s. Most of the time the status does not change and it is 90% up.
- **Performance**: the simulator produces an event “Piece_Produced”. The calculation counts these. The event is produced about every 4h.
- **Quality**:  the simulator produces an event “Piece_Ok”. The calculation counts these. The event is produced shortly after the “Piece_Produced” event (both events have the same timestamp). There is always one “Piece_Produced” for a “Piece_Ok” event, which results in a quality of 100%.

### Ideal Producer
- **Availability**: TODO
- **Performance**: TODO
- **Quality**:  TODO

## Profile settings for simulators

Generally, labels like Profile Name, Machine Location or Workpiece Name can be arbitrary values as they dont have any influence on the calculation. Other profile settings are described in the table below. The values for Resolution & Goals are recommendations and can be changed according to the use case.

| Simulator | Workiece | Resolution | Computation | Matching | Goals |
| ----------- | ----------- | ----------- | ----------- | ----------- | ----------- 
| Normal #1 | 0.4 pcs per min | 10 min | PPQ | APA: Event count "Piece_Produced"<br />APT: Value from event: "Availability" = String "up"<br />AQA: Event count "Piece_Ok" | 80, 80, 80, 80 |

- APA: Actual Production Amount
- APT: Actual Production Time
- AQA: Actual Quality Amount