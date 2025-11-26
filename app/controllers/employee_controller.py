from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.models.enums import PaymentType
from app.database import init_session

router = APIRouter()

class EmployeeCreate(BaseModel):
    employee_id: int
    name: str
    email: str
    date_hired: date
    type: PaymentType

@router.post("/employees/add")
def add_employee(data: EmployeeCreate,
                 session: Session = Depends(init_session())
                 ):
    employee = Employee(**data.model_dump())
    session.add(employee)
    session.commit()
    return {
        "message": "Employee Created"
    }


@router.get("employees/{id}")
def get_employee(employee_id: int, session: Session = Depends(init_session())):
    employee = session.get(Employee, employee_id)
    return {
        "employee_id": employee.employee_id,
        "name": employee.name
    }