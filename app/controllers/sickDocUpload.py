from fastapi import APIRouter, HTTPException, UploadFile, File, status
from datetime import date
from pathlib import Path
from app.models.sick_document import SickDocument
from app.database import (
    create_record,
    read_record,
    read_all_records,
    update_record,
    delete_record,
)
import shutil

sick_document_router = APIRouter()

UPLOAD_DIR = Path("./app/uploads/sick_documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def is_third_sick_leave(leave_request):
    employee_id = leave_request.get("employee_id")
    if not employee_id:
        return False
    sick_leaves = [
        req for req in read_all_records("leave_requests")
        if req.get("employee_id") == employee_id
        and req.get("status") == "approved"
        and req.get("type") == "sick"
    ]
    sick_leaves_sorted = sorted(
        sick_leaves, key=lambda x: x.get("approved_at") or x.get("created_at") or ""
    )
    current_id = leave_request.get("id")
    for idx, req in enumerate(sick_leaves_sorted):
        if req.get("id") == current_id:
            return idx == 2  # Third (zero-based)
    return False


@sick_document_router.post("/", response_model=SickDocument, status_code=status.HTTP_201_CREATED)
async def upload_sick_document(leave_request_id: int, file: UploadFile = File(...)):
    leave_request = read_record("leave_requests", leave_request_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave_request.get("type") != "sick":
        raise HTTPException(
            status_code=400,
            detail="Leave request is not of type 'sick'. Document upload not required."
        )

    if not is_third_sick_leave(leave_request):
        raise HTTPException(
            status_code=400,
            detail="Sick document can only be uploaded for the 3rd approved sick leave request."
        )

    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    record = {
        "leave_request_id": leave_request_id,
        "file_path": str(file_path),
        "file_name": file.filename,
        "uploaded_at": date.today().isoformat(),
        "document": await file.read()  # Save the contents to the database
    }
    # Note: Create two entries - one for file location, one for binary record
    sick_doc = create_record("sick_documents", record)
    return SickDocument(**sick_doc)


@sick_document_router.get("/{sick_document_id}", response_model=SickDocument)
def get_sick_document(sick_document_id: int):
    doc = read_record("sick_documents", sick_document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Sick document not found")
    return SickDocument(**doc)


@sick_document_router.get("/", response_model=list[SickDocument])
def list_sick_documents():
    docs = read_all_records("sick_documents")
    return [SickDocument(**doc) for doc in docs]


@sick_document_router.delete("/{sick_document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sick_document(sick_document_id: int):
    doc = read_record("sick_documents", sick_document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Sick document not found")

    try:
        Path(doc["file_path"]).unlink(missing_ok=True)
    except Exception:
        pass

    if not delete_record("sick_documents", sick_document_id):
        raise HTTPException(status_code=404, detail="Failed to delete sick document")

    return

