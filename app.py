import time
import requests
import streamlit as st

st.set_page_config(page_title="FindIt AI", page_icon="🎓", layout="centered")

DEFAULT_API_URL = "https://findit-ai-62d3c77f-763b-49c7-85b0-4bb70314d-4e9d1cbf.crewai.com"

st.markdown("""
<style>
.main {max-width: 850px; padding-top: 2rem;}
.hero {padding: 1.5rem; border-radius: 18px; background: linear-gradient(120deg,#e8f4fa,#f5f9ff); border: 1px solid #d5e8f3;}
.hero h1 {color:#1f2d3f; margin:0;}
.hero p {color:#42566b; margin:.45rem 0 0;}
.stChatMessage {border-radius: 14px;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>🎓 FindIt AI</h1>
<p>Your student action assistant — ask questions, understand topics, and plan your next steps.</p>
</div>
""", unsafe_allow_html=True)

# Credentials are stored in Streamlit Cloud Secrets, never in the public repository.
try:
    api_url = st.secrets.get("CREWAI_API_URL", DEFAULT_API_URL).rstrip("/")
    token = st.secrets.get("CREWAI_BEARER_TOKEN", "")
except Exception:
    api_url = DEFAULT_API_URL
    token = ""

if not token:
    st.warning("The website owner needs to add the CrewAI bearer token in the app's Secrets before chat can work.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("About FindIt AI")
    st.write("Ask a study question or request help planning your academic tasks.")
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()
    st.caption("Your questions are sent to the FindIt AI CrewAI deployment.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask FindIt AI a question…")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    history = []
    for item in st.session_state.messages[:-1]:
        history.append(f'{item["role"].capitalize()}: {item["content"]}')
    conversation_history = "\n".join(history[-12:])

    inputs = {
        "year": "Not specified",
        "course": "Not specified",
        "interests": "General student support",
        "exam_details": "Not specified",
        "study_document": "",
        "student_request": prompt,
        "conversation_history": conversation_history,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    with st.chat_message("assistant"):
        status_box = st.empty()
        answer_box = st.empty()
        try:
            status_box.info("FindIt AI is thinking…")
            kickoff_response = requests.post(
                f"{api_url}/kickoff",
                headers=headers,
                json={"inputs": inputs},
                timeout=45,
            )
            kickoff_response.raise_for_status()
            kickoff_data = kickoff_response.json()
            kickoff_id = kickoff_data.get("kickoff_id")
            if not kickoff_id:
                raise RuntimeError(f"CrewAI did not return a kickoff_id: {kickoff_data}")

            final_data = None
            deadline = time.time() + 240
            while time.time() < deadline:
                time.sleep(2)
                status_response = requests.get(
                    f"{api_url}/status/{kickoff_id}",
                    headers=headers,
                    timeout=30,
                )
                status_response.raise_for_status()
                data = status_response.json()
                state = str(data.get("state") or data.get("status") or "").upper()
                if state in {"SUCCESS", "COMPLETED", "COMPLETE"}:
                    final_data = data
                    break
                if state in {"FAILED", "ERROR"}:
                    raise RuntimeError(data.get("error") or data.get("message") or str(data))
            if final_data is None:
                raise TimeoutError("This request is taking longer than expected. Please try again.")

            result = final_data.get("result") or {}
            answer = result.get("raw") or result.get("output") or result.get("result") or ""
            if isinstance(answer, dict):
                answer = answer.get("raw") or answer.get("output") or str(answer)
            if not answer:
                answer = str(result) if result else str(final_data)
            status_box.empty()
            answer_box.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except requests.HTTPError as e:
            detail = ""
            try:
                detail = e.response.text
            except Exception:
                pass
            error_text = f"Connection error from CrewAI ({getattr(e.response, 'status_code', 'unknown')}): {detail or str(e)}"
            status_box.error(error_text)
            st.session_state.messages.append({"role": "assistant", "content": "I couldn't reach the AI service. Please try again later."})
        except Exception as e:
            status_box.error(f"Something went wrong: {e}")
            st.session_state.messages.append({"role": "assistant", "content": "I couldn't complete that request. Please try again."})
