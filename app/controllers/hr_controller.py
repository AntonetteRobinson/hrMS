from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import date
import app.database as db
from app.services.employee_service import EmployeeService

hr_router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
@hr_router.get("/hr/dashboard", response_class=HTMLResponse)
async def hr_dashboard(request: Request):
    # Get all leave requests
    all_requests = db.read_all_records("leave_requests")
    
    # Enrich with employee data
    for req in all_requests:
        employee = db.read_record("employees", req.get("employee_id"))
        if employee:
            req["employee_name"] = employee.get("name", "Unknown")
            req["employee_email"] = employee.get("email", "")
    
    # Sort by most recent first
    all_requests.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Calculate stats
    pending_count = len([r for r in all_requests if r.get("status") == "pending"])
    
    today = date.today().isoformat()
    approved_today = len([r for r in all_requests 
                         if r.get("status") == "approved" 
                         and r.get("updated_at", "")[:10] == today])
    
    context = {
        "request": request,
        "leave_requests": all_requests,
        "pending_count": pending_count,
        "approved_today": approved_today,
        "total_requests": len(all_requests)
    }
    
    
    return templates.TemplateResponse("HR.html", context)