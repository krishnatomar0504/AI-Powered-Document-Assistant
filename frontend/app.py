import os

from datetime import datetime

from pathlib import Path

import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="PDF RAG Assistant",
    page_icon="📚",
    layout="wide"
)


if "messages" not in st.session_state:
    st.session_state.messages = []

if "documents" not in st.session_state:
    st.session_state.documents = []


st.markdown(
    """
    <style>

    .block-container {
        padding-top: 4rem;
        padding-bottom: 6rem;
    }

    [data-testid="stSidebar"] {
        background: #0b1b2d;
    }

    [data-testid="stSidebar"] > div:first-child {
        background: #0b1b2d;
        padding-top: 1.5rem;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffffff;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background: #12253c;
        border: 1px solid #28435f;
        border-radius: 10px;
        padding: 8px;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: #12253c;
        border: 1px dashed #3c5a76;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] {
        color: #c2d0df;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: #1769e8;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: #0f5ed8;
    }

    .stMarkdown h1.app-title {
        margin: 0 !important;
        padding: 0 !important;
        color: #f8fafc;
        font-size: clamp(1.6rem, 3vw, 2rem);
        font-weight: 750;
        line-height: 1.25 !important;
    }

    .app-subtitle {
        margin: 0.25rem 0 0;
        color: #a8b7ca;
        font-size: 15px;
        line-height: 1.5;
    }

    [data-testid="stChatMessage"] {
        border: 1px solid #263b53;
        border-radius: 14px;
        margin-bottom: 12px;
        padding: 12px 16px;
        background: #111e2e;
    }

    [data-testid="stChatMessageContent"],
    [data-testid="stChatMessageContent"] p {
        color: #e6edf5;
    }

    [data-testid="stChatInput"] {
        background: #111e2e;
        border: 1px solid #263b53;
        border-radius: 12px;
    }

    [data-testid="stChatInput"] textarea {
        background: #111e2e !important;
        color: #f8fafc !important;
        caret-color: #f8fafc;
        border: none !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #9aabc0 !important;
        opacity: 1;
    }

    [data-testid="stChatInput"] textarea:focus {
        box-shadow: none;
    }

    .document-card {
        padding: 10px;
        margin-bottom: 8px;
        background: #132d49;
        border: 1px solid #1f4568;
        border-radius: 8px;
    }

    .document-name {
        color: #ffffff;
        font-size: 13px;
        font-weight: 600;
    }

    .document-status {
        color: #a8b7ca;
        font-size: 11px;
        margin-top: 3px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


with st.sidebar:

    st.title("📖 DocAI")

    st.caption("Your RAG Assistant")

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"]
    )

    if st.button(
        "＋ Upload Documents",
        use_container_width=True
    ):

        if uploaded_file is None:

            st.warning("Please select a PDF first.")

        else:

            try:

                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        "application/pdf"
                    )
                }

                response = requests.post(
                    f"{API_URL}/upload",
                    files=files,
                    timeout=300
                )

                result = response.json()

                if response.status_code == 200:

                    message = result.get(
                        "message",
                        ""
                    )

                    file_hash = result.get(
                        "file_hash"
                    )

                    existing = any(
                        document["name"] == uploaded_file.name
                        for document in st.session_state.documents
                    )

                    if not existing:

                        st.session_state.documents.append(
                            {
                                "name": uploaded_file.name,
                                "message": message,
                                "file_hash": file_hash
                            }
                        )

                    if "already exists" in message.lower():

                        st.info(
                            "This PDF is already indexed."
                        )

                    else:

                        st.success(
                            "PDF uploaded and indexed successfully."
                        )

                else:

                    st.error(
                        result.get(
                            "message",
                            "Upload failed."
                        )
                    )

            except requests.exceptions.RequestException as error:

                st.error(
                    f"Could not reach the backend service at {API_URL}. "
                    f"Details: {error}"
                )

            except Exception as e:

                st.error(
                    f"Error: {e}"
                )


    st.divider()

    st.subheader("Your Documents")

    if st.session_state.documents:

        for index, document in enumerate(
            st.session_state.documents
        ):

            col1, col2 = st.columns(
                [5, 1]
            )

            with col1:

                st.markdown(
                    f"""
                    <div class="document-card">
                        <div class="document-name">
                            📄 {document["name"]}
                        </div>
                        <div class="document-status">
                            PDF document
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if "already exists" in document["message"].lower():

                    st.caption(
                        "Already indexed"
                    )

            with col2:

                if st.button(
                    "🗑",
                    key=f"delete_document_{index}",
                    help="Remove PDF"
                ):

                    try:

                        file_hash = document.get(
                            "file_hash"
                        )

                        if not file_hash:

                            st.error(
                                "File hash not found."
                            )

                        else:

                            response = requests.delete(
                                f"{API_URL}/documents/{file_hash}",
                                timeout=300
                            )

                            result = response.json()

                            if response.status_code == 200:

                                st.session_state.documents.pop(
                                    index
                                )

                                st.success(
                                    "PDF deleted successfully."
                                )

                                st.rerun()

                            else:

                                st.error(
                                    result.get(
                                        "message",
                                        "PDF deletion failed."
                                    )
                                )

                    except requests.exceptions.RequestException as error:

                        st.error(
                            f"Could not reach the backend service at {API_URL}. "
                            f"Details: {error}"
                        )

                    except Exception as e:

                        st.error(
                            f"Error: {e}"
                        )

    else:

        st.caption(
            "No documents uploaded yet."
        )


left, right = st.columns(
    [5, 1.6],
    vertical_alignment="center"
)


with left:

    st.markdown(
        '<h1 class="app-title">📖 PDF RAG Assistant</h1>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="app-subtitle">'
        'Ask questions about your PDF documents using AI.'
        '</div>',
        unsafe_allow_html=True
    )


with right:

    if st.button(
        "Clear chat",
        icon="🗑️",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()


st.divider()


if not st.session_state.messages:

    with st.container(border=True):

        st.subheader(
            "Ask your PDFs anything",
            anchor=False
        )

        st.write(
            "Upload a PDF from the sidebar, then ask a question here. "
            "Answers include source pages so you can check the original "
            "document."
        )


for message in st.session_state.messages:

    with st.chat_message(
        message["role"],
        avatar="👤" if message["role"] == "user" else "🤖"
    ):

        st.write(
            message["content"]
        )

        if message["role"] == "assistant":

            sources = message.get(
                "sources",
                []
            )

            if sources:

                st.divider()

                st.markdown(
                    "**Sources**"
                )

                for source in sources:

                    source_name = Path(
                        source.get(
                            "source",
                            "Unknown"
                        )
                    ).name

                    page = source.get(
                        "page"
                    )

                    if page is not None:

                        st.markdown(
                            f"📄 **{source_name}** "
                            f"(Page {page + 1})"
                        )

                    else:

                        st.markdown(
                            f"📄 **{source_name}**"
                        )

        st.caption(
            message["time"]
        )


question = st.chat_input(
    "Type your question here..."
)


if question:

    current_time = datetime.now().strftime(
        "%I:%M %p"
    )

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
            "time": current_time
        }
    )

    try:

        with st.spinner(
            "Searching your documents..."
        ):

            response = requests.post(
                f"{API_URL}/ask",
                json={
                    "question": question
                },
                timeout=300
            )

        result = response.json()

        if response.status_code == 200:

            answer = result.get(
                "answer",
                "No answer received."
            )

            sources = result.get(
                "sources",
                []
            )

        else:

            answer = result.get(
                "message",
                "Failed to get an answer."
            )

            sources = []

    except requests.exceptions.RequestException as error:

        answer = (
            f"Could not reach the backend service at {API_URL}. "
            f"Details: {error}"
        )

        sources = []

    except Exception as e:

        answer = f"Error: {e}"

        sources = []


    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "time": datetime.now().strftime(
                "%I:%M %p"
            )
        }
    )

    st.rerun()