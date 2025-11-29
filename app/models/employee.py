from sqlmodel import SQLModel, Field, Session
from datetime import date

from app.models.enums import PaymentType
from app.models.leave_balance import LeaveBalance
from app.models.leave_request import LeaveRequest


class Employee(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    type: PaymentType
    date_hired: date
    leave_requests: list[LeaveRequest]
    leave_balances: list[LeaveBalance]

