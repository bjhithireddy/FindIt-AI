
import streamlit as st
import requests
import time
from io import BytesIO
from pypdf import PdfReader
from docx import Document

st.set_page_config(page_title="FindIt AI", page_icon="🎓", layout="centered")

st.title("🎓 FindIt AI")
st.write("Your AI Student Action Agent — ask questions, understand topics and get help with your studies.")

# Read private settings from Streamlit Secrets
try:
    API_URL = st.secrets["CREWAI_API_URL"].rstrip("/")
    TOKEN = st.secrets["CREWAI_BEARER_TOKEN"]
except Exception:
    st.error("The app owner needs to configure the CrewAI settings in Streamlit Secrets.")
    st.stop()

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Student details
with st.expander("Your student details", expanded=True):
    year = st.selectbox(
        "Year of study",
        ["1st year", "2nd year", "3rd year", "4th year"]
    )
    course = st.text_input("Course", "B.Tech Computer Science")
    interests = st.text_input("Your interests", "AI, technology, web development")
    exam_details = st.text_input("Upcoming exams", "No upcoming exams")

st.subheader("📎 Upload your study document")
uploaded_file = st.file_uploader(
    "Choose a PDF, DOCX or TXT file",
    type=["pdf", "docx", "txt"]
)

def extract_text(file):
    file_bytes = file.getvalue()

    if file.name.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if file.name.lower().endswith(".docx"):
        document = Document(BytesIO(file_bytes))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    if file.name.lower().endswith(".txt"):
        return file_bytes.decode("utf-8", errors="replace")

    return ""

study_document = ""

if uploaded_file:
    try:
        study_document = extract_text(uploaded_file)
        if study_document.strip():
            st.success(f"Uploaded: {uploaded_file.name}")
            st.caption(f"Extracted approximately {len(study_document)} characters.")
        else:
            st.warning("No readable text was found in this document.")
    except Exception as e:
        st.error(f"Could not read this file: {e}")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask FindIt AI anything about your studies...")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    conversation_history = "\n".join(
        f'{m["role"]}: {m["content"]}'
        for m in st.session_state.messages[-10:]
    )

    inputs = {
        "year": year,
        "course": course,
        "interests": interests,
        "exam_details": exam_details,
        "study_document": study_document,
        "student_request": question,
        "conversation_history": conversation_history
    }

    with st.chat_message("assistant"):
        with st.spinner("FindIt AI is thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/kickoff",
                    headers=headers,
                    json={"inputs": inputs},
                    timeout=60
                )
                response.raise_for_status()
                kickoff_data = response.json()
                kickoff_id = kickoff_data.get("kickoff_id")

                if not kickoff_id:
                    st.error("The agent did not return a task ID. Please try again.")
                    st.stop()

                result_data = None

                for _ in range(60):
                    status_response = requests.get(
                        f"{API_URL}/status/{kickoff_id}",
                        headers=headers,
                        timeout=30
                    )
                    status_response.raise_for_status()
                    status_data = status_response.json()

                    if status_data.get("state") == "SUCCESS":
                        result_data = status_data.get("result", {})
                        break

                    if status_data.get("state") == "FAILED":
                        st.error("The agent could not complete this request. Please try again.")
                        st.stop()

                    time.sleep(2)

                if result_data is None:
                    st.error("The agent is taking too long. Please try again.")
                    st.stop()

                answer = result_data.get("raw", "I couldn't find an answer. Please try again.")

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except requests.exceptions.RequestException as e:
                st.error(f"Connection problem: {e}")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

if st.button("Clear chat"):
    st.session_state.messages = []
    st.rerun()
