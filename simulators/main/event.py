import json, logging
from datetime import datetime
from random import randint, uniform, choices
from cumulocityAPI import CumulocityAPI
from task import Task
import interface

cumulocityAPI = CumulocityAPI()
log = logging.getLogger("events generation")


class Event(interface.MachineType):
    def __init__(self, model, shiftplans) -> None:
        self.model = model
        self.definitions = self.model.get('events', [])
        self.shiftplans = shiftplans
        self.machine_up = False
        self.shutdown = False
        self.production_time_s = 0.0
        self.last_production_time_update = datetime.timestamp(datetime.utcnow())
        self.out_of_production_time_logged = False
        if self.model.get('enabled'):
            self.production_speed_s = self.get_production_speed_s()

    def callback(self, definition, min_interval_in_seconds, max_interval_in_seconds):
        event_callback = lambda task: {Event.event_mapping[definition["type"]](self, definition, task)}
        if definition:
            log.debug(f'Machine {self.model.get("label")}, id {self.model.get("id")}: create periodic task for {definition["type"]}, interval in range ({min_interval_in_seconds}, {max_interval_in_seconds}) seconds')
        else:
            log.debug(f'No definition of event in machine {self.model.get("label")}, id {self.model.get("id")}')
        return event_callback

    def get_production_speed_s(self) -> float:
        """Returns pieces/s"""
        for event_definition in self.definitions:
            event_type = event_definition.get("type") or ""
            if event_type == "Piece_Produced":
                frequency = event_definition.get("frequency")
                return frequency / 3600.0
            if event_type == "Pieces_Produced":
                frequency = event_definition.get("frequency")
                countMaximumPerHour = event_definition.get("countMaximumPerHour")
                return frequency * countMaximumPerHour / 3600.0

        return 0.0

    def produce_pieces(self):
        production_time = datetime.timestamp(datetime.utcnow()) - self.last_production_time_update
        self.last_production_time_update = datetime.timestamp(datetime.utcnow())
        if self.machine_up and not self.shutdown:
            self.production_time_s = self.production_time_s + production_time
            log.debug(f'{self.device_id} production time: {self.production_time_s}s')

    def pick_one_piece(self, pieces_per_seconds: float):
        piece_production_time = 1.0 / pieces_per_seconds
        if self.production_time_s > piece_production_time:
            self.production_time_s = self.production_time_s - piece_production_time
            log.debug(f'{self.device_id} one piece produced, remained time: {self.production_time_s}s')
            return True
        log.debug(f'{self.device_id} piece not yet produced, production time: {self.production_time_s}s')
        return False

    def pick_pieces(self, pieces_per_seconds: float):
        pieces_produced = int(pieces_per_seconds * self.production_time_s)
        self.production_time_s = self.production_time_s - pieces_produced / pieces_per_seconds
        log.debug(f'{self.device_id} pieces produced: {pieces_produced}, remained time: {self.production_time_s}s')
        return pieces_produced

    def type_fragment(self, event_definition, text=None):
        return {
            'type': event_definition["type"],
            'text': text or event_definition["type"]
        }

    def log_ignore(self, event_definition):
        log.info(f'Device: {self.device_id} [{self.model["label"]}] is down -> ignore event {event_definition["type"]}')

    def log_not_in_shift(self):
        log.info(f'Device: {self.device_id} [{self.model["label"]}] is not in PRODUCTION shift -> ignore event')

    def on_availability_event(self, event_definition, task):

        self.produce_pieces()

        event = self.type_fragment(event_definition)

        statusses = event_definition.get("status") or ["up"]
        probabilities = event_definition.get("probabilities") or [0.5]
        durations = event_definition.get("durations") or [0]
        status, duration = get_random_status(statusses, durations, probabilities)
        self.machine_up = (status == "up")
        event.update({'status': status})

        event.update(self.get_production_info())
        self.send_event(event)

        # Send Piece_Produced as soon as possible(to get OEE calculation quicker for Slow Producers)
        # Might make sense to configure the behavior per simulator in json.
        if self.is_whole_piece_available():
            self.force_production_event()

        return duration

    def force_production_event(self):
        for event_definition in self.model["events"]:
            event_type = event_definition.get("type")
            if event_type == "Piece_Produced":
                task = self.create_one_time_task(event_definition)
                self.tasks.append(task)

    def get_production_info(self):
        return {
            'production_time_s': self.production_time_s,
            'production_speed_h': self.production_speed_s * 3600.0,
            'pieces_produced': self.production_speed_s * self.production_time_s
        }

    def on_piece_produced_event(self, event_definition, task):
        if not self.machine_up: return self.log_ignore(event_definition)

        self.produce_pieces()

        pieces_per_hour = event_definition.get("frequency") or 1

        if self.pick_one_piece(pieces_per_hour / 3600.0):
            event = self.type_fragment(event_definition)
            event.update(self.get_production_info())
            timestamp = self.send_event(event)
            self.send_following_event(event_definition, timestamp)

        if self.is_whole_piece_available():
            # send piece_produced again.
            next_task = self.create_one_time_task(event_definition)
            self.tasks.append(next_task)

    def is_whole_piece_available(self):
        return int(self.production_time_s * self.production_speed_s) >= 1

    def on_pieces_produced_event(self, event_definition, task):
        if not self.machine_up: return self.log_ignore(event_definition)

        self.produce_pieces()

        countMaximumPerHour = event_definition.get("countMaximumPerHour") or 10

        frequency = event_definition.get("frequency") or 1

        event = self.type_fragment(event_definition)
        pieces_produced = self.pick_pieces(frequency * countMaximumPerHour / 3600.0)
        event.update({"count": pieces_produced})
        event.update(self.get_production_info())

        timestamp = self.send_event(event)
        if timestamp and pieces_produced > 0:
            extra_params = {"pieces_produced": pieces_produced}
            self.send_following_event(event_definition, timestamp, extra_params)

    def on_piece_ok_event(self, event_definition, task):
        event = self.type_fragment(event_definition)

        piece_produced_timestamp = None
        if hasattr(task, 'extra'):
            piece_produced_timestamp = task.extra["timestamp"]

        self.send_event(event, piece_produced_timestamp)

    def on_pieces_ok_event(self, event_definition, task):
        event = self.type_fragment(event_definition)

        countMinimumPerHour = event_definition.get("countMinimumPerHour") or 0
        countMaximumPerHour = event_definition.get("countMaximumPerHour") or 10

        piece_produced_timestamp = None
        if hasattr(task, 'extra'):
            piece_produced_timestamp = task.extra["timestamp"]
            countMaximumPerHour = task.extra.get("pieces_produced") or countMaximumPerHour

        event.update({"count": randint(min(countMinimumPerHour, countMaximumPerHour), countMaximumPerHour)})

        self.send_event(event, piece_produced_timestamp)

    def on_piece_quality_event(self, event_definition, task):
        if not self.machine_up: return self.log_ignore(event_definition)

        event = self.type_fragment(event_definition)

        status_ok_probability = event_definition.get("statusOkProbability") or 0.5
        if try_event(status_ok_probability):
            event.update({"status": "ok"})
        else:
            event.update({"status": "nok"})

        self.send_event(event)

    def on_shutdown_event(self, event_definition, task):
        self.produce_pieces()
        self.shutdown = True

        min_duration = event_definition.get("minDuration") or 0
        max_duration = event_definition.get("maxDuration") or 5
        duration = int(uniform(min_duration, max_duration) * 60)
        log.info(f'shutdown {self.device_id} for the next {duration} seconds.')
        task = self.create_one_time_task({}, duration, Event.on_machine_up_event)
        self.tasks.append(task)

    def on_machine_up_event(self, event_definition, task):
        self.produce_pieces()
        self.shutdown = False
        log.info(f'Device({self.device_id}) is up now.')

    def send_following_event(self, event_definition, timestamp=None, extra_params={}):
        if "followedBy" in event_definition:
            followed_by_definition = event_definition["followedBy"]
            followed_by_frequency = followed_by_definition["frequency"]
            this_frequency = event_definition["frequency"]

            # should followedBy event be sent?
            if try_event(followed_by_frequency / this_frequency):
                followed_by_task = self.create_one_time_task(followed_by_definition)
                followed_by_task.extra["timestamp"] = timestamp
                followed_by_task.extra.update(extra_params)
                self.tasks.append(followed_by_task)
                log.debug(f'{self.device_id} task({id(followed_by_task)}) added: {json.dumps(followed_by_definition)}, tasks: {len(self.tasks)}')
            else:
                log.debug(f'{self.device_id} followedBy task missed. probability = {1 - followed_by_frequency / this_frequency} , def: {json.dumps(followed_by_definition)}')

    def create_one_time_task(self, event_definition, start_in_seconds=2, event_callback=None):
        callback = event_callback or Event.event_mapping[event_definition["type"]]
        task = Task(start_in_seconds, lambda task: {self.execute_callback_and_remove_task(callback, event_definition, task)})
        return task

    def execute_callback_and_remove_task(self, callback, event_definition, task):
        callback(self, event_definition, task)
        if task in self.tasks:
            self.tasks.remove(task)
            log.debug(f'{self.device_id} task({id(task)}) removed: {json.dumps(event_definition)}, tasks: {len(self.tasks)}')

    def send_event(self, event_fragment, timestamp=None):
        newTimestamp = timestamp or interface.current_timestamp()
        base_event = {
            'source': {
                'id': self.device_id
            },
            'time': newTimestamp
        }
        base_event.update(event_fragment)

        if self.shutdown:
            log.info(f'{self.model["id"]} is down -> ignore event: {json.dumps(base_event)}')
            return None
        else:
            response = cumulocityAPI.send_event(base_event)
            if response:
                log.info(f"Created new {event_fragment.get('type')} event for device {self.model.get('label')}, id {self.model.get('id')}")
            return newTimestamp

    def is_in_productionTime(self):
        # if there are no shiftplans for a device, it should not be affected by production-time
        has_no_shiftplan = True
        for shiftplan in self.shiftplans:
            if shiftplan.locationId == self.locationId:
                has_no_shiftplan = False
                for timeslot in shiftplan.recurringTimeSlots:
                    if timeslot.slotType == "PRODUCTION":
                        now = datetime.utcnow()
                        start = datetime.strptime(timeslot.slotStart, interface.DATE_FORMAT)
                        end = datetime.strptime(timeslot.slotEnd, interface.DATE_FORMAT)
                        if start < now < end:
                            return True
        return has_no_shiftplan

    event_mapping = {'Availability': on_availability_event,
                     'Piece_Produced': on_piece_produced_event,
                     'Pieces_Produced': on_pieces_produced_event,
                     'Piece_Ok': on_piece_ok_event,
                     'Pieces_Ok': on_pieces_ok_event,
                     'Piece_Quality': on_piece_quality_event,
                     'Shutdown': on_shutdown_event}

    def should_tick(self):
        if not Event.is_in_productionTime(self):
            if not self.out_of_production_time_logged:
                Event.log_not_in_shift(self)
            self.out_of_production_time_logged = True
            return False
        else:
            self.out_of_production_time_logged = False
            return True


def try_event(probability: float):
    """ Returns True if event occurs.
    """
    return uniform(0.0, 1.0) <= probability


def get_random_status(statusses, durations, probabilites):
    '''returns a random status and duration of the given lists of status, durations and probabilites.
    '''
    if len(statusses) != len(probabilites) or len(durations) != len(probabilites):
        log.info("Length of statusses, duration and probabilites does not match. Set status to up")
        return "up", 0
    choice = choices([i for i in range(len(probabilites))], probabilites)[0]
    return statusses[choice], durations[choice]
