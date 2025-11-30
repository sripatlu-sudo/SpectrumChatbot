# app.py
import os
import json
import requests
import streamlit as st
from openai import OpenAI

# -------------------------
# Config (from environment)
# -------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTORIZE_API_KEY = os.getenv("VECTORIZE_API_KEY")        # optional but recommended
VECTORIZE_PIPELINE_URL = os.getenv("VECTORIZE_PIPELINE_URL")  # your pipeline URL (the one you shared)

if not OPENAI_API_KEY:
    st.error("Missing OPENAI_API_KEY. Set it in Streamlit secrets or environment.")
    st.stop()

if not VECTORIZE_PIPELINE_URL:
    st.warning("Missing VECTORIZE_PIPELINE_URL. Set it in Streamlit secrets or environment. "
               "The app will still run but cannot search Vectorize pipeline until this is set.")

client = OpenAI(api_key=OPENAI_API_KEY)

# Models (feel free to change)
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-mini"

# -------------------------
# UI Theme - AI Techno Fest
# -------------------------
st.set_page_config(page_title="Spectrum TechnoFest Support", layout="centered")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');

    .stApp {
      background: radial-gradient(circle at 10% 10%, #0c0018, #000000 60%);
      color: #dbeafe;
      min-height: 100vh;
    }
    header {display:none}
    .title {
      font-family: 'Orbitron', sans-serif;
      text-align: center;
      color: #00eaff;
      font-size: 36px;
      text-shadow: 0 0 12px #00eaff;
      margin-bottom: 8px;
    }
    .subtitle {
      text-align:center;
      color:#9bdcff;
      margin-bottom:20px;
    }
    .chat-bubble-user {
      padding: 12px;
      background: linear-gradient(90deg,#130025,#2a003f);
      border-left: 4px solid #8a2be2;
      border-radius: 8px;
      margin-bottom: 8px;
      color:#f0f7ff;
    }
    .chat-bubble-bot {
      padding: 12px;
      background: linear-gradient(90deg,#00162b,#00304d);
      border-left: 4px solid #00eaff;
      border-radius: 8px;
      margin-bottom: 18px;
      color:#eafcff;
    }
    .footer-note { text-align:center; color:#7fb8d9; margin-top:14px; font-size:12px }
    </style>
    <div class="title">⚡ Spectrum Support — AI Techno Fest</div>
    <div class="subtitle">Neon help desk — powered by RAG (OpenAI + Vectorize)</div>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Embedding helper
# -------------------------
def get_embedding(text: str):
    resp = client.embeddings.create(model=EMBED_MODEL, input=text)
    return resp.data[0].embedding

# -------------------------
# Vectorize pipeline query
# - We POST the embedding to the pipeline URL
# - Expected shape (most common): {"vector": [..], "limit": k}
# - If pipeline accepts {"text": "..."}, the code will fallback to sending the text.
# -------------------------
def query_vectorize_pipeline(query: str, k: int = 6):
    if not VECTORIZE_PIPELINE_URL:
        return []

    emb = get_embedding(query)

    headers = {
        "Content-Type": "application/json",
    }
    if VECTORIZE_API_KEY:
        headers["Authorization"] = f"Bearer {VECTORIZE_API_KEY}"

    # Try: POST embedding (most typical)
    body_vector = {"vector": emb, "limit": k}
    try:
        r = requests.post(VECTORIZE_PIPELINE_URL, headers=headers, json=body_vector, timeout=12)
        # Accept 200-ish responses
        if r.status_code == 200:
            j = r.json()
            # common keys: 'matches', 'results', 'matches' → list of items with metadata.text
            results = []
            if isinstance(j, dict):
                # Try common response shapes
                if "matches" in j:
                    for m in j["matches"]:
                        text = m.get("metadata", {}).get("text") or m.get("text") or m.get("payload") or m.get("content")
                        if text:
                            results.append(text)
                elif "results" in j:
                    # pipeline may return results list
                    for item in j["results"]:
                        # adapt to several shapes
                        text = item.get("metadata", {}).get("text") or item.get("text") or item.get("content")
                        if text:
                            results.append(text)
                else:
                    # fallback: gather any top-level list of dicts
                    if isinstance(j, list):
                        for item in j:
                            if isinstance(item, dict) and "metadata" in item:
                                t = item["metadata"].get("text")
                                if t:
                                    results.append(t)
            if results:
                return results

    except Exception as e:
        # swallow and fallback to text-based query
        st.debug if hasattr(st, "debug") else None

    # Fallback: try sending raw text (some pipelines accept text)
    try:
        body_text = {"text": query, "limit": k}
        r2 = requests.post(VECTORIZE_PIPELINE_URL, headers=headers, json=body_text, timeout=8)
        if r2.status_code == 200:
            j = r2.json()
            results = []
            # attempt to parse like above
            if isinstance(j, dict) and "results" in j:
                for item in j["results"]:
                    text = item.get("metadata", {}).get("text") or item.get("text") or item.get("content")
                    if text:
                        results.append(text)
            elif isinstance(j, dict) and "matches" in j:
                for m in j["matches"]:
                    text = m.get("metadata", {}).get("text") or m.get("text")
                    if text:
                        results.append(text)
            return results
    except Exception:
        return []

    return []

# -------------------------
# Compose RAG Prompt
# -------------------------
def build_rag_and_answer(query: str, chat_history: list, k: int = 6):
    docs = query_vectorize_pipeline(query, k=k)
    context = "\n\n".join(docs[:6]) if docs else "No relevant documents found."

    messages = [
        {"role": "system", "content": "You are a friendly Spectrum support assistant — speak clearly and helpfully."},
        {"role": "system", "content": f"Use the following knowledge base to answer user queries:\n\n{context}"}
    ]
    # add history (pair list of (user, bot))
    for u, b in chat_history:
        messages.append({"role": "user", "content": u})
        messages.append({"role": "assistant", "content": b})

    messages.append({"role": "user", "content": query})

    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=600
    )
    return resp.choices[0].message.content

# -------------------------
# Streamlit chat handling
# -------------------------
if "history" not in st.session_state:
    st.session_state.history = []  # list of tuples (user, bot)

with st.form(key="ask_form", clear_on_submit=True):
    user_question = st.text_input("Ask the Techno-Assistant", placeholder="How do I reset my Spectrum modem?")
    submitted = st.form_submit_button("⚡ Ask")

if submitted and user_question:
    with st.spinner("Querying Vectorize pipeline & composing answer..."):
        answer = build_rag_and_answer(user_question, st.session_state.history, k=6)
        st.session_state.history.append((user_question, answer))

# Render chat
for user_msg, bot_msg in reversed(st.session_state.history):
    st.markdown(f"<div class='chat-bubble-user'><b>You:</b> {st.session_state.history[-1][0] if False else user_msg}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chat-bubble-bot'><b>AI:</b> {bot_msg}</div>", unsafe_allow_html=True)

st.markdown("<div class='footer-note'>Powered by OpenAI + Vectorize.io • AI Techno Fest Edition ⚡</div>", unsafe_allow_html=True)
