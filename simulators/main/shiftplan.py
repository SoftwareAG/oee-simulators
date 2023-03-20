import logging

from cumulocityAPI import CumulocityAPI
from oeeAPI import OeeAPI 


log = logging.getLogger("task")

cumulocityAPI = CumulocityAPI()
oeeAPI = OeeAPI()

one_day = 86400

class Shiftplan:
    polling_interval = one_day

    def __init__(self, shiftplan_model) -> None:
        self.locationId = ""
        self.recurringTimeSlots = []
        self.set_timeslots_for_shiftplan(shiftplan_model)
        self.add_shiftplan_to_OEE()

    def set_timeslots_for_shiftplan(self, shiftplan):
        self.locationId = shiftplan["locationId"]
        self.recurringTimeSlots = shiftplan["recurringTimeslots"]

    def add_shiftplan_to_OEE(self):
        oeeAPI.add_timeslots_for_shiftplan(self)
        log.info(f'Added shiftplan to OEE for location: {self.locationId}')
