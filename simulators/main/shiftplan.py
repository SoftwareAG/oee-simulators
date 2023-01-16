from datetime import datetime, timedelta
from task import PeriodicTask

from cumulocityAPI import CumulocityAPI
from oeeAPI import OeeAPI 
import logging
import interface

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
        self.add_Shiftplan_to_OEE()
        self.task = self.__create_task()

    def set_timeslots_for_shiftplan(self, shiftplan):
        self.locationId = shiftplan["locationId"]
        self.recurringTimeSlots = shiftplan["recurringTimeslots"]

    def add_Shiftplan_to_OEE(self):
        oeeAPI.add_timeslots_for_shiftplan(self)
        log.info(f'Added shiftplan to OEE for location: {self.locationId}')

    def __create_task(self):
        task_callback = lambda:  {self.fetchNewShiftplan()}
        task = PeriodicTask(Shiftplan.polling_interval, Shiftplan.polling_interval, task_callback)
        log.debug(f'Create periodic task for pulling shiftplans - location {self.locationId} - running every {Shiftplan.polling_interval}')
        return task

    def fetchNewShiftplan(self):
        log.debug(f'Getting Shiftplan for location: {self.locationId}')
        self.setShiftplan(oeeAPI.get_shiftplan(self.locationId, f'{datetime.utcnow():{interface.DATE_FORMAT}}', f'{datetime.utcnow() + timedelta(seconds=Shiftplan.polling_interval):{interface.DATE_FORMAT}}'))

    def setShiftplan(self, shiftplan):
        log.info(f'Setting Shiftplan for location: {self.locationId}')
        self.recurringTimeSlots = shiftplan.get('recurringTimeSlots', [])

    def tick(self):
        self.task.tick()

    class RecurringTimeSlot:
        def __init__(self, recurringTimeSlotModel):
            self.id = recurringTimeSlotModel.get("id")
            self.seriesPostfix = recurringTimeSlotModel.get("seriesPostfix")
            self.slotType = recurringTimeSlotModel.get("slotType")
            self.slotStart = recurringTimeSlotModel.get("slotStart")
            self.slotEnd = recurringTimeSlotModel.get("slotEnd")
            self.description = recurringTimeSlotModel.get("description")
            self.active = recurringTimeSlotModel.get("active")
            self.slotRecurrence = self.SlotRecurrence(recurringTimeSlotModel.get("slotRecurrence"))
        
        class SlotRecurrence:
            def __init__(self, slotRecurrence):
                self.weekdays = slotRecurrence.get("weekdays")
            

