from dotenv import load_dotenv

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

load_dotenv()


embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)


llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)


def get_vectorstore():
    return Chroma(
        collection_name="rag_documents",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )


def ingest_pdf(pdf_path):
    loader = PyMuPDFLoader(pdf_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = text_splitter.split_documents(documents)

    vectorstore = get_vectorstore()

    vectorstore.add_documents(chunks)

    return vectorstore


def ask_question(question):
    vectorstore = get_vectorstore()

    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": 3,
            "score_threshold": 0.5
        }
    )

    results = retriever.invoke(question)

    if not results:
        return {
            "answer": "I don't know based on the provided document.",
            "sources": []
        }

    context = ""

    for result in results:
        context += result.page_content + "\n\n"

    prompt = f"""
Answer the question using only the context below.

If the answer is not present in the context, say:
"I don't know based on the provided document."

Context:
{context}

Question:
{question}

Answer:
"""

    response = llm.invoke(prompt)

    sources = []

    for result in results:
        sources.append({
            "source": result.metadata.get("source"),
            "page": result.metadata.get("page")
        })

    return {
        "answer": response.content,
        "sources": sources
    }