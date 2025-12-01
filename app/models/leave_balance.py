from typing import Optional

from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

from app.models.enums import LeaveType


class LeaveBalance(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id", index=True)
    year: int
    leave_type: LeaveType
    entitled_days: int
    used_days:int = 0
    remaining_days: int
    last_updated: datetime = Field(default_factory=datetime.now)

    employee: Optional["Employee"] = Relationship(back_populates="leave_balances")