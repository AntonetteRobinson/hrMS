from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel
from datetime import date
import app.database as db

from app.models.enums import LeaveType
from app.services.leave_service import LeaveService

leave_request_router = APIRouter()

class LeaveRequestDto(BaseModel):
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date

#Creates leave request
@leave_request_router.post("/leave-requests", status_code=status.HTTP_201_CREATED)
def create_leave_request(data: LeaveRequestDto):
    #Checks if employee exists in database
    employee = db.find_one("employees", id=data.employee_id)
    if not employee:
        raise HTTPException(404, "Employee not found.")
    
    #Checks if dates are valid
    if data.end_date < data.start_date:
        raise HTTPException(400, "End date cannot be before start date.")
    
    #Checks if leave_balance data exists
    balance = db.find_one("leave_balances",
                          employee_id = data.employee_id,
                          leave_type = data.leave_type,
                          year = date.today().year)
    
    if not balance:
        raise HTTPException(400, "No leave balance records found for this employee/year.")
    
    #Requests service layer to calculate and validate leave days
    days_requested = LeaveService.calc_leave_days(
        start_date = data.start_date,
        end_date = data.end_date,
        leave_type = data.leave_type)
    
    if days_requested > balance:
        raise HTTPException(400, "Not enough leave days available.")
    
    #Creates leave_request record
    leave_request = db.create_record("leave_requests", {
        "employee_id": data.employee_id,
        "leave_type": data.leave_type,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "days_requested": days_requested,
        "status": "PENDING",
        "date_requested": date.today()
        })

    return {
        "Message": "Leave request submitted.",
        "leave_request_id": leave_request["id"]
        }

#Get Leave Request
@leave_request_router.get("/leave-requests/{request_id}", status_code=status.HTTP_200_OK)
def get_leave_request(request_id: int):
    request = db.find_one("leave_requests", id=request_id)
    if not request:
        raise HTTPException(404, "Leave request not found.")
    return request

#Get list of requests per employee
@leave_request_router.get("/employees/{employee_id}/leave-requests", status_code=status.HTTP_200_OK)
def list_employee_leave_requests(employee_id: int):
    requests = db.read_all_records("leave_requests")
    for r in requests:
        if r["employee_id"] == employee_id:
            return r