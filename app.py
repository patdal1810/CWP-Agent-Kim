import os
import streamlit as st
import requests
import json
import re

API_URL = "http://127.0.0.1:8000/ask-stream"
ASSISTANT_IMG = "assets/assistant.png"


# Helpers 
def normalize_fallback_text(s: str) -> str:
    """Fallback cleaner if JSON parsing fails."""
    if not s:
        return s
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r" +([,.;:!?])", r"\1", s)
    s = re.sub(r"\[\s*(\d+)\s*\]", r"[\1]", s)
    s = re.sub(r"\s*/\s*", "/", s)
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"\b(?:[A-Z]\s+){1,}[A-Z]\b", lambda m: m.group(0).replace(" ", ""), s)
    return s.strip()


def render_assistant_message(text: str, sources=None):
    sources = sources or []

    # Avatar LEFT + message RIGHT (same row)
    col_avatar, col_text = st.columns([0.6, 8], gap="small")

    with col_avatar:
        if os.path.exists(ASSISTANT_IMG):
            st.image(ASSISTANT_IMG, width=48)
        else:
            st.markdown("🤖")

    with col_text:
        st.markdown(f'<div class="msg assistant">{text}</div>', unsafe_allow_html=True)

    if sources:
        with st.expander("Sources used"):
            for s in sources:
                st.write(s)


def render_user_message(text: str):
    """ChatGPT-style user bubble aligned right."""
    st.markdown(
        f"""
        <div class="row-right">
          <div class="msg user">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Page config 
st.set_page_config(
    page_title="CWP Know-All Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS 
st.markdown(
    """
    <style>
      /* layout */
      .block-container { padding-top: 1.0rem; padding-bottom: 140px !important; max-width: 1100px; }
      header { visibility: hidden; height: 0px; }
      footer { visibility: hidden; height: 0px; }

      /* sticky bottom input (ChatGPT-ish) */
      section[data-testid="stChatInput"]{
        position: fixed;
        bottom: 20px;
        left: 0;
        right: 0;
        z-index: 9999;
        padding: 1.2rem 1.2rem;
        background: rgba(12,12,18,0.92);
        border-top: 1px solid rgba(255,255,255,0.10);
        backdrop-filter: blur(10px);
      }
      section[data-testid="stChatInput"] textarea{
        border-radius: 16px !important;
      }

      /* message bubbles */
      .msg{
        border-radius: 18px;
        padding: 0.9rem 1.1rem;
        border: 1px solid rgba(255,255,255,0.08);
        marging-bottom: 22px;
        marging-top: 22px;
        line-height: 1.6;
        font-size: 0.98rem;
        word-wrap: break-word;
        white-space: pre-wrap;
      }
      .msg.assistant{
        margin-top: 22px;
      }
      .assistant{
        background: rgba(255,255,255,0.04);
      }
      .user{
        background: rgba(46, 125, 247, 0.18);
        border-color: rgba(46, 125, 247, 0.25);
      }

      /* align user bubble to the right */
      .row-right{
        display: flex;
        justify-content: flex-end;
        margin-top: 18px;
        width: 100%;
      }
      .row-right .msg{
        max-width: 78%;
      }

      /* assistant layout */
      .avatar-fallback{
        width: 56px; height: 56px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 14px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        font-size: 22px;
      }

      /* title bar */
      .topbar{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.7rem 0.2rem 1.0rem 0.2rem;
      }
      .brand{
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: -0.02em;
      }
      .hint{
        opacity: 0.75;
        font-size: 0.92rem;
      }

      /* small separators */
      .divider{
        height: 1px;
        background: rgba(255,255,255,0.08);
        margin: 0.7rem 0 1.0rem 0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# Top bar 
st.markdown(
    """
    <div class="topbar">
      <div class="brand">CWP Agent Kim</div>
      <div class="hint">  Ask anything about CWP Academy</div>
    </div>
    <div class="divider"></div>
    """,
    unsafe_allow_html=True,
)

# Controls 
col_a, col_b = st.columns([1, 1])
with col_a:
    if st.button("🧹 Clear chat"):
        st.session_state.messages = []
        st.rerun()
# with col_b:
    #st.caption("Ingest docs with: `python ingest.py` (PDF/DOCX in `data/raw/`)")

# State 
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi! I’m your **CWP Know-All Agent**. Ask me anything about CWP Academy (pricing, refunds, courses, policies, schedules, etc.).",
            "sources": []
        }
    ]

# Render history 
for m in st.session_state.messages:
    if m["role"] == "user":
        render_user_message(m["content"])
    else:
        render_assistant_message(m["content"], m.get("sources"))

# Chat input 
user_q = st.chat_input("Message CWP Know-All Agent…")

if user_q:
    # render user bubble immediately
    st.session_state.messages.append({"role": "user", "content": user_q})
    render_user_message(user_q)

    # assistant response container

    raw_json = ""
    sources = []
    current_event = None

    # avatar at START of response
    col_avatar, col_text = st.columns([0.6, 8], gap="small")

    with col_avatar:
        if os.path.exists(ASSISTANT_IMG):
            st.image(ASSISTANT_IMG, width=48)
        else:
            st.markdown("🤖")

    with col_text:
        live_box = st.empty()

    try:
        with requests.post(
            API_URL,
            json={"question": user_q, "top_k": 5},
            stream=True,
            timeout=120,
        ) as r:
            r.raise_for_status()

            for raw_line in r.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue

                if raw_line.startswith("event:"):
                    current_event = raw_line.split(":", 1)[1].strip()
                    continue

                if raw_line.startswith("data:"):
                    payload = raw_line.split(":", 1)[1].lstrip()

                    try:
                        data = json.loads(payload)
                    except:
                        data = payload

                    if current_event == "token":
                        if isinstance(data, str):
                            raw_json += data
                            live_box.code(raw_json)

                    elif current_event == "sources":
                        if isinstance(data, list):
                            sources = data

                    elif current_event == "done":
                        break

        final_text = raw_json.strip()

        try:
            obj = json.loads(final_text)
            answer_md = obj.get("answer_markdown", "")
            citations = "".join(obj.get("citations", []))

            pretty = answer_md
            if citations and citations not in pretty:
                pretty += "\n\n" + citations
        except:
            pretty = normalize_fallback_text(final_text)

        live_box.markdown(
            f'<div class="msg assistant">{pretty}</div>',
            unsafe_allow_html=True
        )

        st.session_state.messages.append({
            "role": "assistant",
            "content": pretty,
            "sources": sources
        })

        if sources:
            with st.expander("Sources used"):
                for s in sources:
                    st.write(s)

    except Exception as e:
        err = f"Streaming error: {e}"
        live_box.markdown(
            f'<div class="msg assistant">{err}</div>',
            unsafe_allow_html=True
        )

        

    
