from typing import Optional

from sqlmodel import SQLModel, Field, Relationship



class SickDocument(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    leave_id: int = Field(foreign_key="leaverequest.id", index=True)
    file_path: str
    file_name: str

    leave_request: Optional["LeaveRequest"] = Relationship(back_populates="sick_note")