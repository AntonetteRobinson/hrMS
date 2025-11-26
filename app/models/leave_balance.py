from sqlmodel import SQLModel, Field

from app.models.employee import Employee
from app.models.enums import LeaveType


class LeaveBalance(SQLModel, tbale=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id", index=True)
    year: int
    leave_type: LeaveType
    entitled_days: int
    used_days:int = 0
    remaining_days = int
    last_updated: datetime = Field(default_factory=datetime.now)