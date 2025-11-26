import streamlit as st
#import numpy as np

st.title("Echo bot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message['content"'])


#React to user input
if prompt := st.chat_input("What is up?"):
    with st.chat_message("user"):
        st.markdown(prompt)

        st.session_state.messages.append({"role":"user","content":prompt})

        response = f"Echo: {prompt}"

        with st.chat_message("assistant"):
            st.markdown(response)
        
        st.session_state.messages.append({"role":"assistant","content":response})
