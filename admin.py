import streamlit as st
import pandas as pd
import datetime
import hashlib
import os
import re

from langchain_openai import AzureChatOpenAI

AZURE_ENDPOINT = "https://sqml-ais.openai.azure.com/"
AZURE_DEPLOYMENT = "sqmlgpt35t16krk"
AZURE_API_KEY = "7b19136844b04a679e1fa10579fa7d29"

base_llm=AzureChatOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        api_key=AZURE_API_KEY,
        azure_deployment=AZURE_DEPLOYMENT,
        api_version="2024-05-01-preview",
        temperature=0.1,
        max_retries=2,
    )

def log_activity(admin_id, action):
    """Log admin activities to log file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a") as log_file:
        log_file.write(f"{timestamp} - Admin {admin_id}: {action}\n")

import pandas as pd

def data_analysis_chatbot(query, patient_data, doctor_data, credentials):
    """
    Advanced data analysis chatbot for admins using base_llm to interpret queries 
    and provide insights from patient and system data.
    """
    query = query.strip()
    if not query:
        return "Please enter a valid query."

    # Prepare summarized data for the model
    num_patients = len(patient_data)
    num_doctors = len(doctor_data)
    num_users = len(credentials)

    gender_dist = (
        patient_data["Gender"].value_counts().to_dict()
        if not patient_data.empty and "Gender" in patient_data.columns
        else {}
    )
    
    avg_age = (
        round(patient_data["Age"].mean(), 1)
        if not patient_data.empty and "Age" in patient_data.columns
        else "N/A"
    )

    blood_dist = (
        patient_data["BloodGroup"].value_counts().to_dict()
        if not patient_data.empty and "BloodGroup" in patient_data.columns
        else {}
    )

    med_counts = {}
    if not patient_data.empty and "Medications" in patient_data.columns:
        all_meds = []
        for meds in patient_data["Medications"].dropna().str.split(","):
            all_meds.extend([m.strip() for m in meds])
        if all_meds:
            med_counts = pd.Series(all_meds).value_counts().to_dict()

    # Construct context for the language model
    context = f"""
You are a data analyst assistant for a hospital system. Here is the summary of the current data:
- Number of patients: {num_patients}
- Number of doctors: {num_doctors}
- Number of total users: {num_users}
- Average age of patients: {avg_age}
- Gender distribution: {gender_dist}
- Blood group distribution: {blood_dist}
- Top medications: {dict(list(med_counts.items())[:5])}

Now, based on this data, answer the following question in a clear and concise manner:
{query}
    """

    # Use base_llm to interpret and respond
    response = base_llm.invoke(context)
    return response.content if hasattr(response, "content") else "Error: No response received"


def show_admin_page():
    """Display admin dashboard"""
    st.title("Admin Dashboard")
    
    # Check if the user is already in the session state
    if "user_id" in st.session_state:
        admin_id = st.session_state.user_id
        st.sidebar.markdown(f"### Logged in as: {admin_id} (Admin)")
    else:
        admin_id = "admin"  # Default fallback
    
    # Load all data
    try:
        credentials_df = pd.read_csv("credentials.csv")
        patient_data = pd.read_csv("patient_data.csv")
        doctor_data = pd.read_csv("doctor_data.csv")
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Dashboard", "Manage Users", "Manage Patients", 
            "Manage Doctors", "System Analysis"
        ])
        
        # Tab 1: Dashboard
        with tab1:
            st.header("UMID System Overview")
            
            # Display counts
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Users", len(credentials_df))
            with col2:
                st.metric("Patients", len(patient_data))
            with col3:
                st.metric("Doctors", len(doctor_data))
            
            # Display recent logs
            st.subheader("Recent System Activity")
            try:
                with open("log.txt", "r") as log_file:
                    logs = log_file.readlines()
                    recent_logs = logs[-15:]  # Show last 15 log entries
                    
                for log in recent_logs:
                    st.text(log.strip())
            except FileNotFoundError:
                st.warning("Log file not found.")
        
        # Tab 2: Manage Users
        with tab2:
            st.header("Manage System Users")
            
            # Display current users
            st.subheader("Current Users")
            st.dataframe(credentials_df)
            
            # Add new user
            st.subheader("Add New User")
            with st.form("add_user_form"):
                new_user_id = st.text_input("User ID")
                new_user_category = st.selectbox("User Category", ["user", "doctor", "admin"])
                new_user_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                submit_user = st.form_submit_button("Add User")
                
                if submit_user:
                    if not new_user_id or not new_user_password:
                        st.error("User ID and Password are required.")
                    elif new_user_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif new_user_id in credentials_df["ID"].values:
                        st.error(f"User ID '{new_user_id}' already exists.")
                    else:
                        # Hash the password
                        hashed_password = hashlib.sha256(new_user_password.encode()).hexdigest()
                        
                        # Add new user to credentials
                        new_user = pd.DataFrame({
                            "ID": [new_user_id],
                            "category": [new_user_category],
                            "password": [hashed_password]
                        })
                        
                        credentials_df = pd.concat([credentials_df, new_user], ignore_index=True)
                        credentials_df.to_csv("credentials.csv", index=False)
                        
                        st.success(f"User '{new_user_id}' added successfully as {new_user_category}.")
                        log_activity(admin_id, f"Added new {new_user_category} user: {new_user_id}")
                        
                        # If adding a patient or doctor, prompt to add their details
                        if new_user_category == "user":
                            st.info("Please go to the 'Manage Patients' tab to add patient details.")
                        elif new_user_category == "doctor":
                            st.info("Please go to the 'Manage Doctors' tab to add doctor details.")
            
            # Delete user
            st.subheader("Delete User")
            user_to_delete = st.selectbox("Select User ID to Delete", credentials_df["ID"].tolist())
            
            if st.button("Delete User"):
                if user_to_delete:
                    # Check if the user is the current admin
                    if user_to_delete == admin_id:
                        st.error("You cannot delete your own account while logged in.")
                    else:
                        # Remove from credentials
                        credentials_df = credentials_df[credentials_df["ID"] != user_to_delete]
                        credentials_df.to_csv("credentials.csv", index=False)
                        
                        # If user is a patient or doctor, also remove their data
                        if user_to_delete in patient_data["ID"].values:
                            patient_data = patient_data[patient_data["ID"] != user_to_delete]
                            patient_data.to_csv("patient_data.csv", index=False)
                        
                        if user_to_delete in doctor_data["ID"].values:
                            doctor_data = doctor_data[doctor_data["ID"] != user_to_delete]
                            doctor_data.to_csv("doctor_data.csv", index=False)
                        
                        st.success(f"User '{user_to_delete}' deleted successfully.")
                        log_activity(admin_id, f"Deleted user: {user_to_delete}")
        
        # Tab 3: Manage Patients
        with tab3:
            st.header("Manage Patient Records")
            
            # Display current patients
            st.subheader("Current Patients")
            st.dataframe(patient_data)
            
            # Add new patient
            st.subheader("Add/Update Patient Record")
            patient_ids = credentials_df[credentials_df["category"] == "user"]["ID"].tolist()
            
            # Only show users that don't already have patient records
            new_patient_ids = [pid for pid in patient_ids if pid not in patient_data["ID"].values]
            existing_patient_ids = [pid for pid in patient_ids if pid in patient_data["ID"].values]
            
            # Choose between adding new patient or updating existing one
            action = st.radio("Action", ["Add New Patient", "Update Existing Patient"])
            
            if action == "Add New Patient":
                if not new_patient_ids:
                    st.warning("No user accounts available to add as patients. Create user accounts first.")
                else:
                    selected_id = st.selectbox("Select User ID", new_patient_ids)
                    
                    with st.form("add_patient_form"):
                        name = st.text_input("Full Name")
                        age = st.number_input("Age", min_value=0, max_value=120, value=30)
                        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                        blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
                        medical_history = st.text_area("Medical History")
                        medications = st.text_area("Current Medications")
                        allergies = st.text_area("Allergies")
                        last_checkup = st.date_input("Last Checkup Date")
                        doctor_notes = st.text_area("Doctor Notes")
                        
                        submit_patient = st.form_submit_button("Add Patient")
                        
                        if submit_patient:
                            if not name:
                                st.error("Patient name is required.")
                            else:
                                # Add new patient record
                                new_patient = pd.DataFrame({
                                    "ID": [selected_id],
                                    "Name": [name],
                                    "Age": [age],
                                    "Gender": [gender],
                                    "BloodGroup": [blood_group],
                                    "MedicalHistory": [medical_history],
                                    "Medications": [medications],
                                    "Allergies": [allergies],
                                    "LastCheckup": [last_checkup.strftime("%Y-%m-%d")],
                                    "DoctorNotes": [doctor_notes]
                                })
                                
                                patient_data = pd.concat([patient_data, new_patient], ignore_index=True)
                                patient_data.to_csv("patient_data.csv", index=False)
                                
                                st.success(f"Patient record for '{name}' added successfully.")
                                log_activity(admin_id, f"Added patient record for user: {selected_id}")
            else:  # Update Existing Patient
                if not existing_patient_ids:
                    st.warning("No existing patients to update.")
                else:
                    selected_id = st.selectbox("Select Patient ID", existing_patient_ids)
                    patient_row = patient_data[patient_data["ID"] == selected_id].iloc[0]
                    
                    with st.form("update_patient_form"):
                        name = st.text_input("Full Name", value=patient_row["Name"])
                        age = st.number_input("Age", min_value=0, max_value=120, value=patient_row["Age"])
                        gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(patient_row["Gender"]))
                        blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], 
                                                  index=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].index(patient_row["BloodGroup"]))
                        medical_history = st.text_area("Medical History", value=patient_row["MedicalHistory"])
                        medications = st.text_area("Current Medications", value=patient_row["Medications"])
                        allergies = st.text_area("Allergies", value=patient_row["Allergies"])
                        
                        # Parse the date string to a datetime object
                        try:
                            last_checkup_date = datetime.datetime.strptime(patient_row["LastCheckup"], "%Y-%m-%d").date()
                        except ValueError:
                            last_checkup_date = datetime.datetime.now().date()
                            
                        last_checkup = st.date_input("Last Checkup Date", value=last_checkup_date)
                        doctor_notes = st.text_area("Doctor Notes", value=patient_row["DoctorNotes"])
                        
                        submit_update = st.form_submit_button("Update Patient")
                        
                        if submit_update:
                            if not name:
                                st.error("Patient name is required.")
                            else:
                                # Update patient record
                                patient_data.loc[patient_data["ID"] == selected_id, "Name"] = name
                                patient_data.loc[patient_data["ID"] == selected_id, "Age"] = age
                                patient_data.loc[patient_data["ID"] == selected_id, "Gender"] = gender
                                patient_data.loc[patient_data["ID"] == selected_id, "BloodGroup"] = blood_group
                                patient_data.loc[patient_data["ID"] == selected_id, "MedicalHistory"] = medical_history
                                patient_data.loc[patient_data["ID"] == selected_id, "Medications"] = medications
                                patient_data.loc[patient_data["ID"] == selected_id, "Allergies"] = allergies
                                patient_data.loc[patient_data["ID"] == selected_id, "LastCheckup"] = last_checkup.strftime("%Y-%m-%d")
                                patient_data.loc[patient_data["ID"] == selected_id, "DoctorNotes"] = doctor_notes
                                
                                patient_data.to_csv("patient_data.csv", index=False)
                                
                                st.success(f"Patient record for '{name}' updated successfully.")
                                log_activity(admin_id, f"Updated patient record for user: {selected_id}")
        
        # Tab 4: Manage Doctors
        with tab4:
            st.header("Manage Doctor Records")
            
            # Display current doctors
            st.subheader("Current Doctors")
            st.dataframe(doctor_data)
            
            # Add new doctor
            st.subheader("Add/Update Doctor Record")
            doctor_ids = credentials_df[credentials_df["category"] == "doctor"]["ID"].tolist()
            
            # Only show users that don't already have doctor records
            new_doctor_ids = [did for did in doctor_ids if did not in doctor_data["ID"].values]
            existing_doctor_ids = [did for did in doctor_ids if did in doctor_data["ID"].values]
            
            # Choose between adding new doctor or updating existing one
            action = st.radio("Action", ["Add New Doctor", "Update Existing Doctor"], key="doctor_action")
            
            if action == "Add New Doctor":
                if not new_doctor_ids:
                    st.warning("No user accounts available to add as doctors. Create doctor accounts first.")
                else:
                    selected_id = st.selectbox("Select User ID", new_doctor_ids)
                    
                    with st.form("add_doctor_form"):
                        name = st.text_input("Full Name")
                        specialization = st.text_input("Specialization")
                        experience = st.text_input("Experience (e.g., '10 years')")
                        email = st.text_input("Email")
                        phone = st.text_input("Phone Number")
                        
                        submit_doctor = st.form_submit_button("Add Doctor")
                        
                        if submit_doctor:
                            if not name or not specialization:
                                st.error("Doctor name and specialization are required.")
                            else:
                                # Add new doctor record
                                new_doctor = pd.DataFrame({
                                    "ID": [selected_id],
                                    "Name": [name],
                                    "Specialization": [specialization],
                                    "Experience": [experience],
                                    "Email": [email],
                                    "Phone": [phone]
                                })
                                
                                doctor_data = pd.concat([doctor_data, new_doctor], ignore_index=True)
                                doctor_data.to_csv("doctor_data.csv", index=False)
                                
                                st.success(f"Doctor record for '{name}' added successfully.")
                                log_activity(admin_id, f"Added doctor record for user: {selected_id}")
            else:  # Update Existing Doctor
                if not existing_doctor_ids:
                    st.warning("No existing doctors to update.")
                else:
                    selected_id = st.selectbox("Select Doctor ID", existing_doctor_ids)
                    doctor_row = doctor_data[doctor_data["ID"] == selected_id].iloc[0]
                    
                    with st.form("update_doctor_form"):
                        name = st.text_input("Full Name", value=doctor_row["Name"])
                        specialization = st.text_input("Specialization", value=doctor_row["Specialization"])
                        experience = st.text_input("Experience", value=doctor_row["Experience"])
                        email = st.text_input("Email", value=doctor_row["Email"])
                        phone = st.text_input("Phone Number", value=doctor_row["Phone"])
                        
                        submit_update = st.form_submit_button("Update Doctor")
                        
                        if submit_update:
                            if not name or not specialization:
                                st.error("Doctor name and specialization are required.")
                            else:
                                # Update doctor record
                                doctor_data.loc[doctor_data["ID"] == selected_id, "Name"] = name
                                doctor_data.loc[doctor_data["ID"] == selected_id, "Specialization"] = specialization
                                doctor_data.loc[doctor_data["ID"] == selected_id, "Experience"] = experience
                                doctor_data.loc[doctor_data["ID"] == selected_id, "Email"] = email
                                doctor_data.loc[doctor_data["ID"] == selected_id, "Phone"] = phone
                                
                                doctor_data.to_csv("doctor_data.csv", index=False)
                                
                                st.success(f"Doctor record for '{name}' updated successfully.")
                                log_activity(admin_id, f"Updated doctor record for user: {selected_id}")
        
        # Tab 5: System Analysis
        with tab5:
            st.header("System Analysis")
            
            # Display system statistics
            st.subheader("System Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Users", len(credentials_df))
                user_types = credentials_df["category"].value_counts().to_dict()
                for user_type, count in user_types.items():
                    st.write(f"- {user_type.capitalize()}s: {count}")
            
            with col2:
                if not patient_data.empty and "Gender" in patient_data.columns:
                    gender_counts = patient_data["Gender"].value_counts().to_dict()
                    st.write("Gender Distribution:")
                    for gender, count in gender_counts.items():
                        st.write(f"- {gender}: {count}")
                    
                    if "Age" in patient_data.columns:
                        avg_age = patient_data["Age"].mean()
                        st.metric("Average Patient Age", f"{avg_age:.1f} years")
            
            with col3:
                if not patient_data.empty and "BloodGroup" in patient_data.columns:
                    blood_counts = patient_data["BloodGroup"].value_counts().to_dict()
                    st.write("Blood Group Distribution:")
                    for blood, count in blood_counts.items():
                        st.write(f"- {blood}: {count}")
            
            # Data analysis chatbot
            st.subheader("Data Analysis Assistant")
            st.write("Ask questions about system data and statistics:")
            
            query = st.text_input("Your query about the system data:")
            if query:
                response = data_analysis_chatbot(query, patient_data, doctor_data, credentials_df)
                st.write("**Data Analysis:**", response)
                log_activity(admin_id, f"Used data analysis chatbot: '{query}'")
                
            # View system logs
            st.subheader("System Logs")
            if st.button("View Complete Log"):
                try:
                    with open("log.txt", "r") as log_file:
                        logs = log_file.read()
                    st.text_area("Complete System Log", logs, height=300)
                except FileNotFoundError:
                    st.warning("Log file not found.")
    
    except Exception as e:
        st.error(f"Error loading system data: {str(e)}")
        log_activity(admin_id, f"Error accessing system data: {str(e)}")

if __name__ == "__main__":
    # This will only run if the script is run directly, not when imported
    st.write("This is a module to be imported by the main application.")