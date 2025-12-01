from typing import Optional

from sqlmodel import SQLModel, Field, Relationship
from datetime import date

from app.models.enums import LeaveType, LeaveStatus


class LeaveRequest(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id", index=True)
    leave_type: LeaveType
    start_date: date
    end_date: date
    status: LeaveStatus = LeaveStatus.PENDING

    employee: Optional["Employee"] = Relationship(back_populates="leave_requests")
    sick_note: list["SickDocument"] = Relationship(back_populates="leave_request")