import uvicorn
from fastapi import FastAPI

from app.controllers import employee_controller
from app.database import init_db

app = FastAPI()

app.include_router(employee_controller.employee_router)

init_db()

if __name__ == "__main__":
    uvicorn.run(app)