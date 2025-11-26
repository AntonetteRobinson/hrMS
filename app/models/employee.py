from sqlmodel import SQLModel, Field, Session
from datetime import date

from app.models.enums import PaymentType
from app.models.leave_balance import LeaveBalance

class Employee(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_id: int = Field(unique=True, index=True)
    name: str
    email: str
    type: PaymentType
    date_hired: date
    leave_requests: list["LeaveRequet"]
    leave_balances: list["LeaveBalance"]

