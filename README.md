# PDF RAG Assistant

A document-question-answering application built with **Python, LangChain, FastAPI, Streamlit, ChromaDB, Hugging Face embeddings, and Groq**.

The application lets a user upload PDF documents, converts them into searchable chunks, stores their vector embeddings in a persistent vector database, retrieves the most relevant chunks for a question, and asks an LLM to generate an answer using only the retrieved document context.

The project also prevents the **same PDF from being indexed repeatedly** by calculating a SHA-256 fingerprint and storing it in a small SQLite document registry.

---

## What This Project Does

The application follows this flow:

```text
PDF Upload
    ↓
FastAPI /upload
    ↓
Read PDF bytes
    ↓
SHA-256 fingerprint
    ↓
SQLite duplicate check
    ↓
New PDF?
    ├── No → Skip indexing
    └── Yes
          ↓
       PyMuPDF
          ↓
       Text extraction
          ↓
       Chunking
          ↓
       Hugging Face embeddings
          ↓
       ChromaDB

User Question
    ↓
Streamlit
    ↓
FastAPI /ask
    ↓
Open persistent ChromaDB
    ↓
Similarity retrieval
    ↓
Top relevant chunks
    ↓
Groq LLM
    ↓
Answer + source information
    ↓
Streamlit UI
```

---

## Main Features

- Upload PDF documents through a web UI.
- Extract text from PDFs using **PyMuPDF**.
- Split documents into smaller overlapping chunks.
- Generate semantic embeddings using **BAAI/bge-small-en-v1.5** through LangChain's Hugging Face integration.
- Store document chunks and embeddings in **ChromaDB**.
- Persist the vector database locally so it can be reopened after restarting the FastAPI server.
- Retrieve relevant chunks using similarity search with a score threshold.
- Generate grounded answers with **Groq** using the `openai/gpt-oss-20b` model identifier.
- Return source file and page metadata with the answer.
- Prevent duplicate indexing of the same PDF content using **SHA-256 + SQLite**.
- Provide a Streamlit-based chat interface.
- Keep the RAG logic separate from the API and UI layers.

---

## Technology Stack

### Programming Language

- **Python** — main programming language for the backend, RAG pipeline, document registry, and Streamlit UI.

### RAG and LangChain

- **LangChain Community** — PDF loading utilities.
- **LangChain Text Splitters** — recursive document chunking.
- **LangChain Hugging Face** — integration with the embedding model.
- **LangChain Chroma** — integration with ChromaDB.
- **LangChain Groq** — integration with Groq's chat model API.

### PDF Processing

- **PyMuPDF (`pymupdf`)** — extracts text and page information from PDF files.
- **`PyMuPDFLoader`** — LangChain loader used to convert PDF pages into LangChain `Document` objects.

### Chunking

- **`RecursiveCharacterTextSplitter`** — breaks extracted text into manageable chunks.
- Current prototype settings:
  - `chunk_size = 500`
  - `chunk_overlap = 50`

### Embeddings

- **Hugging Face embedding integration:** `HuggingFaceEmbeddings`
- **Embedding model:** `BAAI/bge-small-en-v1.5`
- The embedding model converts document chunks and questions into vector representations so semantically related text can be retrieved.

### Vector Database

- **ChromaDB** — stores document chunks, embeddings, and metadata.
- The project uses a persistent local directory named:

```text
chroma_db/
```

### LLM

- **Groq** — hosted inference provider.
- **LangChain Groq integration:** `ChatGroq`
- Current model configuration:

```python
model="openai/gpt-oss-20b"
temperature=0
```

The application uses the LLM only after retrieving relevant document context.

### Backend API

- **FastAPI** — provides API endpoints used by the frontend.
- **Uvicorn** — ASGI server used to run FastAPI.
- **Pydantic `BaseModel`** — validates the question request body.
- **`UploadFile` and `File`** — handle PDF uploads.

### Frontend

- **Streamlit** — Python-based web interface for PDF upload and chat.
- **Requests** — sends HTTP requests from Streamlit to the FastAPI backend.

### Duplicate Detection and Local Registry

- **Python `hashlib`** — calculates SHA-256 fingerprints for uploaded PDF bytes.
- **SQLite (`sqlite3`)** — built into Python and used as a lightweight document registry.
- Registry file:

```text
documents.db
```

### Environment and Secrets

- **python-dotenv** — loads variables from `.env` during local development.
- The main secret is:

```text
GROQ_API_KEY=your_groq_api_key
```

---

## Project Architecture

The project is intentionally separated into three layers:

### 1. RAG Pipeline

File:

```text
backend/rag_pipeline.py
```

Responsibilities:

- Load a PDF.
- Split it into chunks.
- Create embeddings.
- Add chunks to ChromaDB.
- Reopen the persistent Chroma collection.
- Retrieve relevant chunks.
- Build grounded prompts.
- Generate answers with Groq.
- Return answer and source metadata.

Important functions:

```python
ingest_pdf(pdf_path)
get_vectorstore()
ask_question(question)
```

### 2. API Layer

File:

```text
backend/main.py
```

Responsibilities:

- Receive PDF uploads.
- Calculate the SHA-256 fingerprint.
- Ask the SQLite registry whether the document is already known.
- Start ingestion only for a new document.
- Expose the question-answering endpoint.

Endpoints:

```text
POST /upload
POST /ask
```

FastAPI's automatic API testing page is available at:

```text
http://127.0.0.1:8000/docs
```

### 3. User Interface

File:

```text
frontend/app.py
```

Responsibilities:

- Show the document upload interface.
- Display uploaded document names.
- Accept user questions.
- Call FastAPI.
- Display answers.
- Display source file and page information.
- Maintain the current chat history in Streamlit session state.

---

## Project Structure

A typical local project structure is:

```text
RAG/
│
├── backend/
│   ├── main.py
│   ├── rag_pipeline.py
│   └── document_registry.py
│
├── frontend/
│   └── app.py
│
├── data/
│   └── pdf/
│
├── notebook/
│   └── document.ipynb
│
├── chroma_db/
├── documents.db
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

`notebook/document.ipynb` is used as a learning/prototyping environment for understanding the RAG pipeline before moving reusable code into the backend Python modules.

---

## RAG Pipeline in Detail

### 1. PDF Loading

The application uses `PyMuPDFLoader` to turn a PDF into LangChain `Document` objects.

Each document contains information such as:

```text
page_content → extracted text
metadata     → source/page information
```

### 2. Chunking

The extracted text is split using:

```python
RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
```

The overlap keeps some surrounding context between neighboring chunks.

### 3. Embeddings

Each chunk is converted into a vector using:

```text
BAAI/bge-small-en-v1.5
```

The same embedding function is used when embedding a user's question for retrieval.

### 4. ChromaDB

Chroma stores the chunks together with their vectors and metadata.

The persistent collection is:

```text
collection_name = "rag_documents"
```

and its database directory is configured by `DATA_DIR`:

```text
<DATA_DIR>/chroma_db
```

When `DATA_DIR` is not set, the project root is used.

### 5. Retrieval

The current retriever configuration is:

```python
search_type="similarity_score_threshold"
```

with:

```python
k=3
score_threshold=0.5
```

This means the system tries to return up to three relevant chunks and rejects results below the configured similarity threshold.

### 6. Context Building

Retrieved chunks are combined into a context string and passed to the LLM.

The prompt instructs the model to answer only from the supplied context and to say:

```text
I don't know based on the provided document.
```

when the answer is not present in the retrieved context.

### 7. Answer Generation

The context and question are sent to Groq through LangChain's `ChatGroq` integration.

The API response contains:

```json
{
  "answer": "...",
  "sources": [
    {
      "source": "...",
      "page": 0
    }
  ]
}
```

---

## Duplicate PDF Prevention

A major feature of the project is preventing the same PDF from being processed repeatedly.

The backend reads the PDF bytes and calculates:

```python
file_hash = hashlib.sha256(file_bytes).hexdigest()
```

This hash is stored as the primary key in SQLite.

The registry contains fields conceptually like:

```text
file_hash | filename | status
```

The status can be:

```text
processing
indexed
```

When a second user uploads exactly the same PDF content, the generated hash is the same.

The registry then prevents another call to:

```python
ingest_pdf(file_path)
```

Therefore the system skips the expensive:

```text
PDF loading
→ chunking
→ embedding
→ Chroma insertion
```

for an already indexed document.

### Important behavior

The deduplication key is the **PDF content hash**, not the filename.

Therefore:

```text
machine_learning.pdf
ML_notes.pdf
```

can still be recognized as the same document when their actual PDF bytes are identical.

---

## Persistence

ChromaDB is persistent because the vector store is reopened from:

```text
<DATA_DIR>/chroma_db/
```

instead of being kept only in a Python variable.

The question path uses the persistent vector store again, which means restarting FastAPI does not automatically remove the indexed vectors.

The SQLite registry is stored in:

```text
<DATA_DIR>/documents.db
```

By default, `DATA_DIR` is the project root, preserving the local paths
`chroma_db/` and `documents.db`. In production, set `DATA_DIR=/data` and mount
a persistent volume at `/data`; Chroma and SQLite will then use
`/data/chroma_db` and `/data/documents.db`. Uploaded PDFs are stored in
`<DATA_DIR>/pdf` in production, or the existing `data/pdf` directory locally.
The SHA-256 registry and vectors survive restarts only when this storage is
persistent.

---

## Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
DATA_DIR=
ALLOWED_ORIGINS=
```

The backend loads it with:

```python
from dotenv import load_dotenv

load_dotenv()
```

`DATA_DIR` is optional locally (defaults to the project root). In production,
set it to `/data`. `ALLOWED_ORIGINS` is an optional comma-separated list of
additional frontend origins; localhost Streamlit origins are allowed by
default. Never commit `.env` or a real API key to GitHub.

---

## Installation

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The main dependencies used by the project are:

```text
langchain-community
langchain-text-splitters
langchain-huggingface
sentence-transformers
pymupdf
langchain-chroma
chromadb
langchain-groq
fastapi
uvicorn
python-multipart
jupyter
ipykernel
python-dotenv
streamlit
requests
```

---

## Running the Application Locally

The application has two running processes.

### Terminal 1 — FastAPI

From the project root:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

FastAPI runs at:

```text
http://127.0.0.1:8000
```

API documentation/testing:

```text
http://127.0.0.1:8000/docs
```

### Terminal 2 — Streamlit

From the project root:

```bash
streamlit run frontend/app.py
```

The Streamlit interface normally opens at:

```text
http://localhost:8501
```

Keep both processes running while using the application.

---

## API Usage

### Upload a PDF

Endpoint:

```text
POST /upload
```

The request contains a PDF file as multipart form data.

Successful first upload:

```json
{
  "message": "PDF uploaded and indexed successfully.",
  "filename": "example.pdf"
}
```

Duplicate upload:

```json
{
  "message": "PDF already exists. Skipping indexing.",
  "filename": "example.pdf"
}
```

### Ask a Question

Endpoint:

```text
POST /ask
```

Request:

```json
{
  "question": "What is artificial intelligence?"
}
```

Response:

```json
{
  "answer": "...",
  "sources": [
    {
      "source": "data/pdf/example.pdf",
      "page": 0
    }
  ]
}
```

---

## Why RAG Is Used

Instead of asking an LLM to answer from an entire document collection every time, the application first retrieves the most relevant document chunks.

This gives the system a simple grounded workflow:

```text
Documents
    ↓
Semantic search
    ↓
Relevant context
    ↓
LLM
    ↓
Grounded answer
```

This approach is particularly useful when the application needs to work with private, changing, or multiple documents and should provide document-based source information.

---

## Streamlit vs FastAPI in This Project

### Streamlit

Streamlit is the user-facing interface.

It provides:

- PDF uploader
- Chat input
- Chat messages
- Source display
- Document list

### FastAPI

FastAPI is the backend API layer.

It provides:

- `/upload`
- `/ask`

It also coordinates the duplicate check and calls the reusable RAG pipeline functions.

---

## Security and Git

The following should be ignored by Git:

```text
.env
.venv/
__pycache__/
*.pyc
chroma_db/
documents.db
```

A typical `.gitignore` is:

```gitignore
.env
.venv/
__pycache__/
*.pyc
chroma_db/
documents.db
```

Never commit the Groq API key to the repository.

---

## Deployment Notes

For a deployed version, the Streamlit frontend and FastAPI backend can be hosted separately.

Example architecture:

```text
User
  ↓
Streamlit Cloud
  ↓
Public FastAPI URL
  ↓
RAG backend
  ↓
Persistent Chroma + SQLite
  ↓
Groq
```

The local API URL:

```text
http://127.0.0.1:8000
```

is the Streamlit fallback for local development. To use a different URL, set
`API_URL` in the environment or Streamlit secrets.

### Deploy FastAPI

Deploy the project repository to a Python hosting platform that supports a
persistent disk, and configure these backend environment variables:

```text
GROQ_API_KEY=<your Groq API key>
DATA_DIR=/data
ALLOWED_ORIGINS=https://<your-streamlit-app>.streamlit.app
```

Mount the platform's persistent volume at `/data`. Set the platform's `PORT`
environment variable and use this exact start command:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

The service's public HTTPS URL is the backend URL; its `/docs` path provides
FastAPI's API documentation. Keep `GROQ_API_KEY` in the hosting platform's
secret/environment-variable settings, not in source code.

### Deploy Streamlit Community Cloud

Deploy `frontend/app.py` from this repository on Streamlit Community Cloud.
In the app's **Settings → Secrets**, configure the deployed backend URL:

```toml
API_URL = "https://<your-fastapi-service>"
```

The Streamlit app sends its `/upload` and `/ask` requests to
`{API_URL}/upload` and `{API_URL}/ask`. This URL must be the reachable public
FastAPI service URL, not `127.0.0.1`, `localhost`, or `0.0.0.0`. Streamlit Cloud
does not start FastAPI; the backend must already be deployed and running.

For a real multi-user deployment, document authorization should also be added if uploaded documents are private. The current SHA-256 mechanism answers **“Has this exact document content already been indexed?”**; it does not by itself implement user-specific access control.

---

## Current Project Scope

The current implementation focuses on the core RAG workflow:

```text
PDF ingestion
Chunking
Embeddings
Vector database
Retrieval
LLM generation
Source metadata
Duplicate prevention
FastAPI API
Streamlit UI
```

It is intentionally kept simple enough to understand, demonstrate, and extend.

Possible future improvements include:

- user authentication and authorization
- per-user document access control
- document deletion
- document management database
- background ingestion jobs
- streaming LLM responses
- better citation rendering
- OCR for scanned PDFs
- hybrid keyword + vector retrieval
- reranking
- conversation memory
- evaluation and retrieval metrics
- production database/storage
- deployment automation

---

## Learning Journey

The project was developed incrementally:

```text
1. PDF loading
2. Chunking
3. Embeddings
4. ChromaDB
5. Retrieval
6. Groq generation
7. Reusable RAG functions
8. FastAPI endpoints
9. Streamlit UI
10. SHA-256 duplicate detection
11. SQLite document registry
12. Persistent Chroma access
13. Deployment preparation
```

The notebook was used to understand and test each RAG stage before moving the reusable logic into `backend/rag_pipeline.py`.

---

## Summary

**PDF RAG Assistant** is a full document-aware question-answering application.

It combines:

```text
Python
+ LangChain
+ PyMuPDF
+ Hugging Face embeddings
+ ChromaDB
+ Groq
+ FastAPI
+ Streamlit
+ SQLite
+ SHA-256
```

The key idea is simple:

> Upload a PDF once, store its searchable representations, retrieve only the relevant information for each question, and generate an answer grounded in the retrieved document context.
