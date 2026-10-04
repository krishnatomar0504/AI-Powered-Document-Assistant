from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

import hashlib
import os

from backend.rag_pipeline import ingest_pdf, ask_question
from backend.document_registry import (
    reserve_document,
    mark_indexed,
    remove_document
)

app = FastAPI()


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

    file_path = f"data/pdf/{file.filename}"

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