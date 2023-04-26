import logging

from cumulocityAPI import CumulocityAPI
from oeeAPI import OeeAPI 


log = logging.getLogger("task")

cumulocityAPI = CumulocityAPI()
oeeAPI = OeeAPI()

one_day = 86400

class Shiftplan:

    def __init__(self, shiftplan_model, replace_existing_timeslots) -> None:
        self.locationId = shiftplan_model["locationId"] or ""
        self.recurringTimeSlots = shiftplan_model["recurringTimeslots"] or []
        if replace_existing_timeslots.lower() == "true":
            self.delete_OEE_shiftplan_timeslots()
        self.add_shiftplan_to_OEE()

    def add_shiftplan_to_OEE(self):
        oeeAPI.add_timeslots_for_shiftplan(self)
        log.info(f'Added shiftplan to OEE for location: {self.locationId}')

    def delete_OEE_shiftplan_timeslots(self):
        oeeAPI.delete_timeslots_for_shiftplan(self)
        log.info(f'Deleted shiftplan in OEE for location: {self.locationId}')