
import streamlit as st
import os
from dotenv import load_dotenv
from vectorize import Vectorize
from openai import OpenAI

# Load environment variables from .env file (optional, but recommended)
load_dotenv()
VECTORIZE_API_KEY = os.getenv("VECTORIZE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAG_PIPELINE_ID = "YOUR_PIPELINE_ID_HERE" # Replace with your actual pipeline ID from vectorize.io

# Initialize clients
if not VECTORIZE_API_KEY or not OPENAI_API_KEY:
    st.error("API keys not found. Please create a .env file or set environment variables.")
    st.stop()

v = Vectorize(api_key=VECTORIZE_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

# Streamlit UI configuration
st.set_page_config(page_title="Vectorize.io Streamlit Chatbot")
st.title("📄 Chat with Your Data (Vectorize.io + Streamlit)")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Function to get response from the RAG pipeline
def get_rag_response(user_input):
    # Query the vectorize.io RAG pipeline
    # The 'query' method will retrieve relevant context from your vector store
    # and use the configured LLM (e.g., OpenAI) to generate a response.
    response = v.pipelines.query(RAG_PIPELINE_ID, query_text=user_input)
    # The exact response structure depends on your pipeline configuration, 
    # but typically you get a ready-made answer.
    return response.answer 

# User input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get the AI response
    with st.spinner("Thinking..."):
        ai_response = get_rag_response(prompt)
    
    # Add AI response to chat history
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    with st.chat_message("assistant"):
        st.markdown(ai_response)

