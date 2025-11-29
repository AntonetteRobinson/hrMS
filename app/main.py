import uvicorn
from fastapi import FastAPI

from app.controllers import employee_controller
from app.database import init_db, init_session

app = FastAPI()

app.include_router(employee_controller.router)

init_db()

if __name__ == "__main__":
    uvicorn.run(app)