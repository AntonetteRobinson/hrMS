from sqlmodel import SQLModel, Field
from datetime import date

from app.models.enums import LeaveType, LeaveStatus
from app.models.sick_document import SickDocument


class LeaveRequest(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id", index=True)
    leave_type: LeaveType
    start_date: date
    end_date: date
    status: LeaveStatus = LeaveStatus.PENDING
    sick_note: SickDocument | None