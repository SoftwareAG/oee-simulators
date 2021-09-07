Back to [README.md](README.md)

**Normal #1 (Intervals: 1min, 10min)**
Availability: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation is a machine status event checking that the value is “up”. This event should be produced 5-10 times per hour with 90% being “up”.
Performance: the simulator produces an event “Piece_Produced”. The calculation counts these. The event should be produced about 25 times per hour. 
Quality:  the simulator produces an event “Piece_Ok”. The calculation counts these. The event should be produced about 20 times per hour. The should follow a few seconds after a corresponding “Piece_Produced” event. Some “Piece_Produced” events are not followed by a “Piece_Ok” event.

**Normal #2 (Intervals: 1min, 10min)**
Availability: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation is a machine status event  checking that the value is “up”. This event should be produced 5-10 times per hour with 90% being “up”.
Performance: the simulator produces an event “Pieces_Produced”. They contain a field named “count” with values ranging from 0-10. The calculation adds the counts from the fields. The event should be produced 6 times per hour (every 10 min). 
Quality: the simulator produces an event “Piece_Ok”. The calculation counts these. The event should be produced about 20 times per hour. The should follow a few seconds after a corresponding “Piece_Produced” event. Some “Piece_Produced” events are not followed by a “Piece_Ok” event.

**Normal #3 (Intervals: 1min, 10min)**
Availability: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation is a machine status event checking that the value is “up”. This event should be produced 5-10 times per hour with 90% being “up”.
Performance: the simulator produces an event “Pieces_Produced”. They contain a field named “count” with values ranging from 0-10. The calculation adds the counts from the fields. The event should be produced 6 times per hour (every 10 min). 
Quality: the simulator produces an event “Piece_Quality”. These have a field “status” that is either “ok” or “nok”. The calculation is a quality status event checking that the value is “ok”. There should be 2-3 of these with 90% of the time being in state “ok”.

**Normal with Short Shutdowns (Intervals: 1min, 10min)**
Short Shutdowns: should be enabled and set to 2 minutes.
Availability: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation is a machine status event checking that the value is “up”. This event should be produced 5-10 times per hour with 90% being “up”. There should be a few short shutdowns with the machine being in “down” less than 2 minutes.
Performance: the simulator produces an event “Piece_Produced”. The calculation counts these. The event should be produced about 25 times per hour. 
Quality:  the simulator produces an event “Piece_Ok”. The calculation counts these. The event should be produced about 20 times per hour. The should follow a few seconds after a corresponding “Piece_Produced” event. Some “Piece_Produced” events are not followed by a “Piece_Ok” event.

**Slow Producer (Intervals: 10min, 1h, 4h, 8h)**
Availability: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation is a machine status event checking that the value is “up”. This event should be produced 5-10 times per hour with 90% being “up”.
Performance: the simulator produces an event “Piece_Produced”. The calculation counts these. The event should be produced about every 4h
Quality:  the simulator produces an event “Piece_Ok”. The calculation counts these. The event should be produced shortly after the “Piece_Produced” event. There should always be one, leading to a quality of 100%.

**High Frequency Availability (Intervals: 1min, 10min)**
Availability: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation is a machine status event checking that the value is “up”. This event should be produced every 10s. Most of the time the status should not change and it should be 90% up.
Performance: the simulator produces an event “Piece_Produced”. The calculation counts these. The event should be produced about 25 times per hour. 
Quality:  the simulator produces an event “Piece_Ok”. The calculation counts these. The event should be produced about 20 times per hour. The should follow a few seconds after a corresponding “Piece_Produced” event. Some “Piece_Produced” events are not followed by a “Piece_Ok” event.

**Slow Producer + High Frequency Availability (Intervals: 10min, 1h, 4h, 8h)**
Availability: the simulator produces an “Availability” event which has a field “status” that is either “up” or “down”. The calculation is a machine status event checking that the value is “up”. This event should be produced every 10s. Most of the time the status should not change and it should be 90% up.
Performance: the simulator produces an event “Piece_Produced”. The calculation counts these. The event should be produced about every 4h
Quality:  the simulator produces an event “Piece_Ok”. The calculation counts these. The event should be produced shortly after the “Piece_Produced” event. There should always be one, leading to a quality of 100%.
