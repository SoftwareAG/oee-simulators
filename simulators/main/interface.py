import logging
from datetime import datetime

log = logging.getLogger("interface")

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class MachineType:
    def tick(self):
        raise NotImplementedError


def calculate_interval_in_seconds(definition):
    min_frequency_per_hour = definition.get("minimumPerHour", definition.get("frequency"))
    max_frequency_per_hour = definition.get("maximumPerHour", definition.get("frequency"))
    min_interval_in_seconds = int(3600 / max_frequency_per_hour)
    max_interval_in_seconds = int(3600 / min_frequency_per_hour)

    return min_interval_in_seconds, max_interval_in_seconds


def datetime_to_string(date_time, time_string_format="%Y-%m-%dT%H:%M:%S.%f"):
    return date_time.strftime(time_string_format)[:-3] + 'Z'


def current_timestamp():
    return datetime_to_string(datetime.utcnow())
