from pydantic import BaseModel, Field
from datetime import date

from app.models.enums import LeaveType, LeaveStatus
from app.models.sick_document import SickDocument


class LeaveRequest(BaseModel):
    id: int
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    status: LeaveStatus = LeaveStatus.PENDING
    sick_note: SickDocument = None      #Sick note to be uploaded after 3 sick days

    #Validates dates
    def validate_dates(self):
        if self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date.")
    
    def req_sick_doc(self):
        if self.leave_type != LeaveType.SICK:
            return
        #Rule to attach sick note on the third sick day
        days = (self.end_date - self.start_date) + 1
        if days > 2 and not self.sick_note:
            raise ValueError("Sick note required for sick leave of 3 days or longer.")
    
    #Submission of leave request
    def submit_request(self):
        self.validate_dates()
        self.req_sick_doc()
        return True
    
    #Approval
    def approve(self, approver):
        if approver not in ("hr", "manager"):
            raise PermissionError("Only HR or Managers can approve requests.")
        if self.status != LeaveStatus.PENDING:
            raise ValueError("Only pending requests can be approved.")
        self.status == LeaveStatus.APPROVED

    #Denial
    def deny(self, approver):
        if approver not in ("hr", "manager"):
            raise PermissionError("Only HR or Managers can deny requests.")
        if self.status != LeaveStatus.PENDING:
            raise ValueError("Only pending requests can be denied.")
        self.status == LeaveStatus.DENIED