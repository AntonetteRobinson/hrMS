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
    sick_note: SickDocument