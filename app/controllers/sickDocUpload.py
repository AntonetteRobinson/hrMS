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

"note: sick document uploads documents  and deletes documents, however at the moment it just uploads and deletes documents,"
"it does have the logic that notfies hr to upload document after the 3rd sick day."

sick_document_router = APIRouter()

UPLOAD_DIR = Path("./app/uploads/sick_documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@sick_document_router.post("/", response_model=SickDocument, status_code=status.HTTP_201_CREATED)
async def upload_sick_document(
    leave_request_id: int,
    file: UploadFile = File(...)
):
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    record = {
        "leave_request_id": leave_request_id,
        "file_path": str(file_path),
        "file_name": file.filename,
        "uploaded_at": date.today().isoformat(),
    }
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

    # Remove file from storage
    try:
        Path(doc["file_path"]).unlink(missing_ok=True)
    except Exception:
        pass

    if not delete_record("sick_documents", sick_document_id):
        raise HTTPException(status_code=404, detail="Failed to delete sick document")

    return

