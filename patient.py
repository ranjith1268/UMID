import streamlit as st
import pandas as pd
import datetime
import os
from langchain_openai import AzureChatOpenAI



base_llm=AzureChatOpenAI(
        azure_endpoint=st.secrets["AZURE_ENDPOINT"],
        api_key=st.secrets["AZURE_API_KEY"],
        azure_deployment=st.secrets["AZURE_DEPLOYMENT"],
        api_version="2024-05-01-preview",
        temperature=0.1,
        max_retries=2,
    )

def log_activity(user_id, action):
    """Log user activities to log file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a") as log_file:
        log_file.write(f"{timestamp} - Patient {user_id}: {action}\n")

def medical_chatbot(query):
    """
    Medical chatbot that uses a language model (base_llm) to generate responses
    to general healthcare questions in 30 words or less.
    """
    query = query.lower()
    prompt = f"You are a medical assistant. Provide a clear, accurate, and concise answer (max 30 words) to this general healthcare question:\n\n{query}"
    response = base_llm.invoke(prompt)
    return response.content if hasattr(response, "content") else "Error: No response received"


def show_patient_page(user_id):
    """Display patient dashboard"""
    st.title(f"Patient Dashboard")
    st.sidebar.markdown(f"### Logged in as: {user_id}")
    
    # Load patient data
    try:
        patient_data = pd.read_csv("patient_data.csv")
        user_data = patient_data[patient_data["ID"] == user_id]
        
        if not user_data.empty:
            user_info = user_data.iloc[0]
            
            # Display patient information
            st.header("Your Medical Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Personal Details")
                st.write(f"**Name:** {user_info['Name']}")
                st.write(f"**Age:** {user_info['Age']}")
                st.write(f"**Gender:** {user_info['Gender']}")
                st.write(f"**Blood Group:** {user_info['BloodGroup']}")
                
            with col2:
                st.subheader("Medical Details")
                st.write(f"**Medical History:** {user_info['MedicalHistory']}")
                st.write(f"**Current Medications:** {user_info['Medications']}")
                st.write(f"**Allergies:** {user_info['Allergies']}")
                st.write(f"**Last Checkup:** {user_info['LastCheckup']}")
            
            # Display doctor's notes
            st.subheader("Doctor's Notes")
            st.write(user_info['DoctorNotes'])
            
            # Medical chatbot
            st.header("Medical Assistant")
            st.write("Ask questions about general health, medications, or symptoms:")
            
            query = st.text_input("Your question:")
            if query:
                response = medical_chatbot(query)
                st.write("**Medical Assistant:**", response)
                log_activity(user_id, f"Used medical chatbot: '{query}'")
            
        else:
            st.error(f"No records found for user ID: {user_id}")
            log_activity(user_id, "Attempted to access patient dashboard - No records found")
    
    except Exception as e:
        st.error(f"Error loading patient data: {str(e)}")
        log_activity(user_id, f"Error accessing patient data: {str(e)}")

if __name__ == "__main__":
    # This will only run if the script is run directly, not when imported
    st.write("This is a module to be imported by the main application.")