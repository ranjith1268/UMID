import streamlit as st
import requests
import hashlib
import time

API_KEY = st.secrets["API_KEY"]

class OpenRouterLLM:
    def __init__(self, key):
        self.headers = {
            "Authorization": f"Bearer {key}", 
            "Content-Type": "application/json"
        }
    
    def generate_response(self, messages):
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions", 
                headers=self.headers, 
                json={
                    "model": "openai/gpt-3.5-turbo", 
                    "messages": messages
                }
            )
            return r.json()["choices"][0]["message"]["content"]
        except:
            return "Error: Unable to generate response"

base_llm = OpenRouterLLM(API_KEY)

def get_user_session_id():
    """Generate a unique session ID for each user session"""
    if "user_session_id" not in st.session_state:
        # Create a unique session ID based on timestamp and random elements
        session_data = f"{time.time()}_{st.experimental_user.email if hasattr(st, 'experimental_user') and st.experimental_user else 'anonymous'}"
        st.session_state.user_session_id = hashlib.md5(session_data.encode()).hexdigest()[:8]
    return st.session_state.user_session_id

def chat_bot():
    """Main chatbot function with user-specific sessions"""
    # Get unique session ID for this user
    session_id = get_user_session_id()
    chat_key = f"chat_messages_{session_id}"
    
    # Initialize chat history for this specific user session
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
    
    # Header with session info and controls
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.caption(f"Session ID: {session_id}")
    with col2:
        if st.button("🔄 New Session"):
            # Clear current session and create new one
            if chat_key in st.session_state:
                del st.session_state[chat_key]
            del st.session_state.user_session_id
            st.rerun()
    with col3:
        if st.button("🗑️ Clear"):
            st.session_state[chat_key] = []
            st.rerun()
    
    st.divider()
    
    # Display chat messages from history
    for message in st.session_state[chat_key]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Accept user input
    if prompt := st.chat_input("Message..."):
        # Add user message to chat history
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            response = base_llm.generate_response(st.session_state[chat_key])
            st.write(response)
            # Add assistant response to chat history
            st.session_state[chat_key].append({"role": "assistant", "content": response})
