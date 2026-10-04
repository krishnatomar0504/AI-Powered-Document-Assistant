from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import hashlib
import os

from backend.rag_pipeline import (
    ingest_pdf,
    ask_question,
    delete_document
)

from backend.document_registry import (
    reserve_document,
    mark_indexed,
    remove_document,
    get_document
)


app = FastAPI()


allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501"
).split(",")


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):

    file_bytes = file.file.read()

    file_hash = hashlib.sha256(
        file_bytes
    ).hexdigest()

    is_new = reserve_document(
        file_hash,
        file.filename
    )

    if not is_new:
        return {
            "message": "PDF already exists. Skipping indexing.",
            "filename": file.filename,
            "file_hash": file_hash
        }

    file_path = f"data/pdf/{file.filename}"

    try:

        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)

        ingest_pdf(
            file_path,
            file_hash
        )

        mark_indexed(file_hash)

        return {
            "message": "PDF uploaded and indexed successfully.",
            "filename": file.filename,
            "file_hash": file_hash
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

    return ask_question(
        request.question
    )


@app.delete("/documents/{file_hash}")
def delete_pdf(file_hash: str):

    document = get_document(
        file_hash
    )

    if document is None:
        return {
            "message": "Document not found."
        }

    filename = document[1]

    try:

        delete_document(
            file_hash
        )

        file_path = f"data/pdf/{filename}"

        if os.path.exists(file_path):
            os.remove(file_path)

        remove_document(
            file_hash
        )

        return {
            "message": "PDF deleted successfully.",
            "filename": filename
        }

    except Exception as e:

        return {
            "message": "PDF deletion failed.",
            "error": str(e)
        }