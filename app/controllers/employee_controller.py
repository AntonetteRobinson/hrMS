from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
import datetime
from app.models.employee import Employee
from app.models.enums import PaymentType
from app.database import init_session
from app.services.employee_service import EmployeeService

employee_router = APIRouter()

class EmployeeDto(BaseModel):
    name: str
    email: str
    type: PaymentType
    date_hired: datetime.date


@employee_router.get("/employees", status_code=status.HTTP_200_OK)
def get_employees(session: Session = Depends(init_session)):
    """Retrieve all employees"""
    employees = session.exec(select(Employee)).all()
    return employees


@employee_router.post("/employees/add", status_code=status.HTTP_201_CREATED)
def add_employee(employee_data: EmployeeDto, session: Session = Depends(init_session)):
    """Create an employee and initialize leave entitlements"""

    # Check if employee already exists
    existing = session.exec(
        select(Employee).where(Employee.email == employee_data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee already exists")

    employee = Employee(**employee_data.model_dump())
    session.add(employee)
    session.commit()
    session.refresh(employee)

    curr_year = datetime.date.today().year
    EmployeeService.init_leave_balance(session, employee, curr_year)
    return {
        "message": "Employee Created"
    }


