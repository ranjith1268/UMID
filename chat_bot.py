import streamlit as st
import requests

API_KEY = st.secrets["API_KEY"]

class OpenRouterLLM:
    def __init__(self, key):
        self.headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    
    def generate_response(self, messages):
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                            headers=self.headers, json={"model": "openai/gpt-3.5-turbo", "messages": messages})
            return r.json()["choices"][0]["message"]["content"]
        except: 
            return "Error"

base_llm = OpenRouterLLM(API_KEY)

def chat_bot():

    if prompt := st.chat_input("Message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): 
            st.write(prompt)
        with st.chat_message("assistant"):
            response = base_llm.generate_response(st.session_state.messages)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})