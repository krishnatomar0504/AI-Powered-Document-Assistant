import hashlib
import os

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import PDF_DIR
from backend.rag_pipeline import ingest_pdf, ask_question
from backend.document_registry import (
    reserve_document,
    mark_indexed,
    remove_document
)

app = FastAPI()

allowed_origins = {
    "http://localhost:8501",
    "http://127.0.0.1:8501",
}
allowed_origins.update(
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(allowed_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):

    file_bytes = file.file.read()

    file_hash = hashlib.sha256(file_bytes).hexdigest()

    is_new = reserve_document(
        file_hash,
        file.filename
    )

    if not is_new:
        return {
            "message": "PDF already exists. Skipping indexing.",
            "filename": file.filename
        }

    filename = (
        (file.filename or "uploaded.pdf")
        .replace("\\", "/")
        .split("/")[-1]
    )
    file_path = PDF_DIR / filename

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)

        ingest_pdf(file_path)

        mark_indexed(file_hash)

        return {
            "message": "PDF uploaded and indexed successfully.",
            "filename": file.filename
        }

    except Exception as e:
        remove_document(file_hash)

        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "message": "PDF processing failed.",
            "error": str(e)
        }


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
def ask(request: QuestionRequest):
    return ask_question(request.question)