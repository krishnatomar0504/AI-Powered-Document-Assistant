import os
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def get_api_url():
    api_url = os.getenv("API_URL")
    if api_url:
        return api_url.rstrip("/")

    try:
        return st.secrets["API_URL"].rstrip("/")
    except (KeyError, StreamlitSecretNotFoundError):
        return "http://127.0.0.1:8000"


st.set_page_config(
    page_title="PDF RAG Assistant",
    page_icon="📚",
    layout="wide"
)

API_URL = get_api_url()


if "messages" not in st.session_state:
    st.session_state.messages = []

if "documents" not in st.session_state:
    st.session_state.documents = []


st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
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

    .app-title {
        color: #12213a;
        font-size: 30px;
        font-weight: 750;
        margin-bottom: 0;
    }

    .app-subtitle {
        color: #68778d;
        font-size: 15px;
        margin-bottom: 20px;
    }

    [data-testid="stChatMessage"] {
        border: 1px solid #dfe7f0;
        border-radius: 14px;
        margin-bottom: 12px;
        padding: 12px 16px;
        background: #ffffff;
    }

    [data-testid="stChatMessageContent"] {
        color: #172033;
    }

    [data-testid="stChatInput"] textarea {
        background: #ffffff;
        color: #172033;
        border: 1px solid #ccd8e5;
        border-radius: 10px;
    }

    [data-testid="stChatInput"] textarea:focus {
        border-color: #1769e8;
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

                    message = result.get("message", "")

                    existing = any(
                        document["name"] == uploaded_file.name
                        for document in st.session_state.documents
                    )

                    if not existing:
                        st.session_state.documents.append(
                            {
                                "name": uploaded_file.name,
                                "message": message
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

            except requests.exceptions.RequestException:

                st.error(
                    "Cannot connect to FastAPI."
                )

            except Exception as e:

                st.error(f"Error: {e}")


    st.divider()

    st.subheader("Your Documents")

    if st.session_state.documents:

        for document in st.session_state.documents:

            st.write(
                f"📄 **{document['name']}**"
            )

            if "already exists" in document["message"].lower():

                st.caption("Already indexed")

    else:

        st.caption("No documents uploaded yet.")


left, right = st.columns([5, 1])


with left:

    st.markdown(
        '<div class="app-title">📖 PDF RAG Assistant</div>',
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
        "🗑 Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []
        st.rerun()


st.divider()


for message in st.session_state.messages:

    with st.chat_message(
        message["role"],
        avatar="👤" if message["role"] == "user" else "🤖"
    ):

        st.write(
            message["content"]
        )

        if message["role"] == "assistant":

            sources = message.get("sources", [])

            if sources:

                st.divider()

                st.markdown("**Sources**")

                for source in sources:

                    source_name = Path(
                        source.get("source", "Unknown")
                    ).name

                    page = source.get("page")

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

    except requests.exceptions.RequestException:

        answer = (
            "Cannot connect to FastAPI. "
            "Make sure the backend is running."
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