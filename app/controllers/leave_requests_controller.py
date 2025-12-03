from fastapi import APIRouter, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from datetime import date
from datetime import date as DateType
from pathlib import Path
import shutil
import app.database as db
from app.models.enums import LeaveType, LeaveStatus

leave_request_router = APIRouter()

UPLOAD_DIR = Path("./app/uploads/sick_documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class LeaveRequestDto(BaseModel):
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date


# Helper: calculate leave days

def working_days(start: DateType, end: DateType) -> int:
    """Count weekdays between start and end (inclusive)."""
    from datetime import timedelta
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # Monday–Friday
            count += 1
        current += timedelta(days=1)
    return count


def calc_leave_days(start: DateType, end: DateType, leave_type: LeaveType) -> int:
    """Calculate days requested based on leave type."""
    if leave_type == LeaveType.VACATION:
        return working_days(start, end)
    elif leave_type == LeaveType.SICK:
        return (end - start).days + 1
    else:
        # Fallback – treat as calendar days
        return (end - start).days + 1



# CREATE LEAVE REQUEST

@leave_request_router.post("/leave-requests", status_code=status.HTTP_201_CREATED)
def create_leave_request(data: LeaveRequestDto):
    # 1. Check if employee exists
    employee = db.find_one("employees", id=data.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    # 2. Validate dates
    if data.end_date < data.start_date:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date."
        )

    # 3. Check leave balance
    balance = db.find_one(
        "leave_balances",
        employee_id=data.employee_id,
        leave_type=data.leave_type.value,   # store enum as its string value
        year=date.today().year
    )
    if not balance:
        raise HTTPException(
            status_code=400,
            detail="No leave balance records found for this employee/year."
        )

# Extract available days from LeaveBalance structure
    available_days = None

    if isinstance(balance, dict):
    # Use remaining_days if present
     if "remaining_days" in balance:
        available_days = balance["remaining_days"]
    # Fallback if someone stored entitled_days instead
     elif "entitled_days" in balance and "used_days" in balance:
        available_days = balance["entitled_days"] - balance["used_days"]
     else:
        raise HTTPException(500, "Invalid leave balance format.")
    else:
     raise HTTPException(500, "Leave balance must be stored as a dictionary.")


    # 4. Calculate requested leave days
    days_requested = calc_leave_days(
        start=data.start_date,
        end=data.end_date,
        leave_type=data.leave_type
    )

    if days_requested > available_days:
        raise HTTPException(
            status_code=400,
            detail="Not enough leave days available."
        )

    # 5. Create leave request record
    leave_request = db.create_record("leave_requests", {
        "employee_id": data.employee_id,
        "leave_type": data.leave_type.value,            # "vacation" / "sick"
        "start_date": data.start_date,                  # JSONEncoder will isoformat this
        "end_date": data.end_date,
        "days_requested": days_requested,
        "status": LeaveStatus.PENDING.value,            # "pending"
        "date_requested": date.today(),
        "sick_document_id": None                        # will be filled after upload
    })

    return {
        "message": "Leave request submitted.",
        "leave_request_id": leave_request["id"]
    }



# GET A SINGLE LEAVE REQUEST

@leave_request_router.get("/leave-requests/{request_id}", status_code=status.HTTP_200_OK)
def get_leave_request(request_id: int):
    leave_request = db.find_one("leave_requests", id=request_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found.")
    return leave_request



# LIST LEAVE REQUESTS PER EMPLOYEE

@leave_request_router.get("/employees/{employee_id}/leave-requests", status_code=status.HTTP_200_OK)
def list_employee_leave_requests(employee_id: int):
    all_requests = db.read_all_records("leave_requests")
    employee_requests = [
        req for req in all_requests
        if req.get("employee_id") == employee_id
    ]
    return employee_requests



# UPLOAD SICK NOTE
# Sick note required/allowed when SICK leave is > 2 days.

@leave_request_router.post("/leave-requests/{leave_request_id}/upload-sick-note")
async def upload_sick_document(leave_request_id: int, file: UploadFile = File(...)):
    # 1. Fetch the leave request
    leave_request = db.find_one("leave_requests", id=leave_request_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found.")

    # 2. Validate leave type is SICK
    if leave_request.get("leave_type") != LeaveType.SICK.value:
        raise HTTPException(
            status_code=400,
            detail="Sick document upload is only allowed for sick leave."
        )

    # 3. Determine duration of the sick leave
    #    start_date and end_date were stored by JSONEncoder as ISO strings.
    raw_start = leave_request.get("start_date")
    raw_end = leave_request.get("end_date")

    if isinstance(raw_start, str):
        start = DateType.fromisoformat(raw_start)
    else:
        start = raw_start

    if isinstance(raw_end, str):
        end = DateType.fromisoformat(raw_end)
    else:
        end = raw_end

    total_days = (end - start).days + 1

    # Option 2 rule: only require/allow doc when sick leave > 2 days
    if total_days <= 2:
        raise HTTPException(
            status_code=400,
            detail="Sick note is only required/allowed for sick leave longer than 2 days."
        )

    # 4. Save file to disk
    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(ex)}"
        )

    # 5. Create sick document record
    sick_document = db.create_record("sick_documents", {
        "leave_request_id": leave_request_id,
        "file_path": str(file_path),
        "file_name": file.filename,
        "uploaded_at": date.today().isoformat()
    })

    # 6. Link the sick document back to the leave request
    db.update_record("leave_requests", leave_request_id, {
        "sick_document_id": sick_document["id"]
    })

    return {
        "message": "Sick document uploaded",
        "document": sick_document
    }
