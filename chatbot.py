
import streamlit as st
import os
from dotenv import load_dotenv
#from vectorize_client import Vectorize
from langchain_vectorize.retrievers import VectorizeRetriever
import getpass

VECTORIZE_ORG_ID = "2bd970bf-2207-4759-a02a-7964de963540" #getpass.getpass("Enter Vectorize organization ID: ")
VECTORIZE_API_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjQyNDMxMTgsImF1ZCI6IjJiZDk3MGJmLTIyMDctNDc1OS1hMDJhLTc5NjRkZTk2MzU0MCIsInJvbGUiOiJhZG1pbiIsImF1dGhvcml6YXRpb25fZGV0YWlscyI6W3sibmFtZSI6IlJFVFJJRVZBTF9BQ0NFU1NfVE9LRU4iLCJpc1N0YW5kYXJkUm9sZSI6dHJ1ZSwicGVybWlzc2lvbnMiOnsiVmVyc2lvbiI6IjEuMCIsIlN0YXRlbWVudCI6W3siQWN0aW9uIjpbIk9yZzpQaXBlbGluZXM6UmV0cmlldmFsIl0sIlJlc291cmNlIjpbIi9vcmdhbml6YXRpb24vMmJkOTcwYmYtMjIwNy00NzU5LWEwMmEtNzk2NGRlOTYzNTQwIl0sIkVmZmVjdCI6IkFsbG93In1dfX1dLCJleHAiOjE3NjY4MzUxMTgsInN1YiI6Ik15IHRva2VuIn0.OmzgiKFZe1JS6Rv9yVMPT1ccmh0gURvjLSayy6BhJaMsTsdg5e7nXVaC8cUIbOkv7GaYytR7BaUQmkRwk7BflOipIHyZwD-RRs_5_nTfSI6bYfyh5xJ2wE7EtInwl8iP6IY_bSXlfYBWEkq5sSZJHTG3043Ph7S8f846c23w9haC7T8-O0s3E_wvtALsPyjqrPk2zQ6bmm0vr1uCV4D9e7VfnFW4lLjrISlZqsS-gpnlDHdz9l69PKo0ZcD-g4NOQvAZLUXep07_AaXo55heULe0xEyf6ZLiZE2UtMzM4o3g9Q1n-83FXcRKBp74WytUsHIIZha855Hjxf1FkXG8vw" #getpass.getpass("Enter Vectorize API Token: ")



# Load environment variables from .env file (optional, but recommended)
load_dotenv()
#VECTORIZE_API_TOKEN = os.getenv("VECTORIZE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAG_PIPELINE_ID = "aip91328-99a4-4a6f-b597-82532ad9dbf1" # Replace with your actual pipeline ID from vectorize.io

# Initialize clients
if not VECTORIZE_API_TOKEN or not OPENAI_API_KEY:
    st.error("API keys not found. Please create a .env file or set environment variables.")
    st.stop()

#v = Vectorize(api_key=VECTORIZE_API_KEY)


v = VectorizeRetriever(
    api_token=VECTORIZE_API_TOKEN,
    organization=VECTORIZE_ORG_ID,
    pipeline_id=RAG_PIPELINE_ID,
)

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

