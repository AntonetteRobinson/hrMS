from sqlmodel import SQLModel, Field, Relationship
from datetime import date

from app.models.enums import PaymentType


class Employee(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    type: PaymentType
    date_hired: date

    leave_requests: list["LeaveRequest"] = Relationship(back_populates="employee")
    leave_balances: list["LeaveBalance"] = Relationship(back_populates="employee")

