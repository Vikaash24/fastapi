import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models, schemas

# Initialize database
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(title="📄 FastAPI Document Manager")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🟢 Upload document
@app.post("/upload", response_model=schemas.Document)
async def upload_document(
    file: UploadFile = File(...),
    description: str = Form(None),
):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db = next(get_db())
    doc = models.Document(filename=file.filename, path=file_path, description=description)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

# 🟢 List all documents
@app.get("/documents", response_model=list[schemas.Document])
def list_documents():
    db = next(get_db())
    return db.query(models.Document).all()

# 🟢 Get (download) document by ID
@app.get("/documents/{doc_id}")
def get_document(doc_id: int):
    db = next(get_db())
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(doc.path, filename=doc.filename)

# 🟡 Update document
@app.put("/documents/{doc_id}", response_model=schemas.Document)
async def update_document(
    doc_id: int,
    new_file: UploadFile = File(None),
    description: str = Form(None)
):
    db = next(get_db())
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if new_file:
        new_path = os.path.join(UPLOAD_FOLDER, new_file.filename)
        with open(new_path, "wb") as buffer:
            shutil.copyfileobj(new_file.file, buffer)
        if os.path.exists(doc.path):
            os.remove(doc.path)
        doc.filename = new_file.filename
        doc.path = new_path

    if description is not None:
        doc.description = description

    db.commit()
    db.refresh(doc)
    return doc

# 🔴 Delete document
@app.delete("/documents/{doc_id}")
def delete_document(doc_id: int):
    db = next(get_db())
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(doc.path):
        os.remove(doc.path)
    db.delete(doc)
    db.commit()
    return {"message": f"Document '{doc.filename}' deleted successfully"}
