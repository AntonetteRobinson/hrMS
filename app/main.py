import uvicorn
from fastapi import FastAPI

from app.controllers.employee_controller import employee_router
from app.controllers.hr_controller import hr_router
from app.controllers.leave_requests_controller import leave_request_router
from app.controllers.reports_controller import reports_router

app = FastAPI()

app.include_router(employee_router)
app.include_router(hr_router)
app.include_router(leave_request_router)
app.include_router(reports_router)


if __name__ == "__main__":
    uvicorn.run(app)