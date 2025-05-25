# admin.py - Fixed Streamlit Form Button Issues
import streamlit as st
import pandas as pd
import datetime
import hashlib
import os
import re
from biometric_auth import BiometricAuth, integrate_biometric_registration

from langchain_openai import AzureChatOpenAI

base_llm=AzureChatOpenAI(
        azure_endpoint=st.secrets["AZURE_ENDPOINT"],
        api_key=st.secrets["AZURE_API_KEY"],
        azure_deployment=st.secrets["AZURE_DEPLOYMENT"],
        api_version="2024-05-01-preview",
        temperature=0.1,
        max_retries=2,
    )

def log_activity(admin_id, action):
    """Log admin activities to log file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a") as log_file:
        log_file.write(f"{timestamp} - Admin {admin_id}: {action}\n")

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
    """Display admin dashboard with biometric integration"""
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
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Dashboard", "Manage Users", "Manage Patients", 
            "Manage Doctors", "Manage Pharmacy", "System Analysis", "Biometric Access"
        ])
        
        # Tab 1: Dashboard
        with tab1:
            st.header("UMID System Overview")
            
            # Display counts
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Users", len(credentials_df))
            with col2:
                st.metric("Patients", len(patient_data))
            with col3:
                st.metric("Doctors", len(doctor_data))
            with col4:
                # Display biometric registration stats
                try:
                    biometric_data = pd.read_csv("biometric_data.csv")
                    st.metric("Biometric Users", len(biometric_data))
                except:
                    st.metric("Biometric Users", 0)
            
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
        
        # Tab 2: Manage Users (Fixed - Removed buttons from forms)
        with tab2:
            st.header("Manage System Users")
            
            # Display current users
            st.subheader("Current Users")
            st.dataframe(credentials_df)
            
            # Add new user with biometric registration option
            st.subheader("Add New User")
            with st.form("add_user_form"):
                new_user_id = st.text_input("User ID")
                new_user_category = st.selectbox("User Category", ["user", "doctor", "admin", "pharmassist"])
                new_user_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                # Biometric registration option
                enable_biometric = st.checkbox("🔐 Enable Biometric Registration", value=True)
                
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
                        
                        # Store the new user ID in session state for biometric registration
                        if enable_biometric:
                            st.session_state['new_user_for_biometric'] = new_user_id
                        
                        # Prompt for additional details based on user category
                        if new_user_category == "user":
                            st.info("Please go to the 'Manage Patients' tab to add patient details.")
                        elif new_user_category == "doctor":
                            st.info("Please go to the 'Manage Doctors' tab to add doctor details.")
                        elif new_user_category == "pharmassist":
                            st.info("Please go to the 'Manage Pharmacy' tab to add pharmacy assistant details.")
            
            # Biometric registration section (moved outside form)
            if 'new_user_for_biometric' in st.session_state:
                new_user_id = st.session_state['new_user_for_biometric']
                st.markdown("---")
                st.subheader(f"🔐 Biometric Setup for {new_user_id}")
                
                face_image, fingerprint_hash, biometric_auth = integrate_biometric_registration()
                
                if st.button(f"💾 Save Biometric Data for {new_user_id}"):
                    if face_image is not None or fingerprint_hash is not None:
                        success = biometric_auth.register_biometric_data(
                            new_user_id, face_image, fingerprint_hash
                        )
                        if success:
                            st.success("✅ Biometric data registered successfully!")
                            log_activity(admin_id, f"Registered biometric data for user: {new_user_id}")
                            # Clear the session state
                            del st.session_state['new_user_for_biometric']
                        else:
                            st.error("❌ Failed to register biometric data.")
                    else:
                        st.warning("⚠️ No biometric data captured. Please capture face or fingerprint.")
                
                if st.button("Skip Biometric Registration"):
                    del st.session_state['new_user_for_biometric']
                    st.info("Biometric registration skipped. User can register later.")
            
            # Delete user section (outside form)
            st.subheader("Delete User")
            user_to_delete = st.selectbox("Select User ID to Delete", [""] + credentials_df["ID"].tolist())
            
            if user_to_delete and st.button("Delete User"):
                # Check if the user is the current admin
                if user_to_delete == admin_id:
                    st.error("You cannot delete your own account while logged in.")
                else:
                    # Remove from credentials
                    credentials_df = credentials_df[credentials_df["ID"] != user_to_delete]
                    credentials_df.to_csv("credentials.csv", index=False)
                    
                    # Remove biometric data if exists
                    try:
                        biometric_data = pd.read_csv("biometric_data.csv")
                        biometric_data = biometric_data[biometric_data["ID"] != user_to_delete]
                        biometric_data.to_csv("biometric_data.csv", index=False)
                        
                        # Remove from face encodings
                        import pickle
                        try:
                            with open("face_encodings.pkl", 'rb') as f:
                                face_encodings = pickle.load(f)
                            if user_to_delete in face_encodings:
                                del face_encodings[user_to_delete]
                                with open("face_encodings.pkl", 'wb') as f:
                                    pickle.dump(face_encodings, f)
                        except:
                            pass
                    except:
                        pass
                    
                    # If user is a patient or doctor, also remove their data
                    if user_to_delete in patient_data["ID"].values:
                        patient_data = patient_data[patient_data["ID"] != user_to_delete]
                        patient_data.to_csv("patient_data.csv", index=False)
                    
                    if user_to_delete in doctor_data["ID"].values:
                        doctor_data = doctor_data[doctor_data["ID"] != user_to_delete]
                        doctor_data.to_csv("doctor_data.csv", index=False)
                    
                    st.success(f"User '{user_to_delete}' and all associated data deleted successfully.")
                    log_activity(admin_id, f"Deleted user and biometric data: {user_to_delete}")
        
        # Tab 3: Manage Patients (Fixed - Moved update section outside form)
        with tab3:
            st.header("Manage Patients")
            
            # Display current patients
            st.subheader("Current Patients")
            if not patient_data.empty:
                st.dataframe(patient_data)
            else:
                st.info("No patient data available.")
            
            # Add new patient
            st.subheader("Add New Patient")
            with st.form("add_patient_form"):
                patient_id = st.selectbox("Patient ID", 
                    [uid for uid in credentials_df[credentials_df["category"] == "user"]["ID"].tolist() 
                     if uid not in patient_data["ID"].values])
                
                if patient_id:
                    patient_name = st.text_input("Full Name")
                    patient_age = st.number_input("Age", min_value=0, max_value=150, value=25)
                    patient_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                    patient_blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
                    patient_phone = st.text_input("Phone Number")
                    patient_email = st.text_input("Email")
                    patient_address = st.text_area("Address")
                    patient_emergency_contact = st.text_input("Emergency Contact")
                    patient_medications = st.text_area("Current Medications (comma-separated)")
                    patient_allergies = st.text_area("Allergies")
                    patient_conditions = st.text_area("Medical Conditions")
                    
                    submit_patient = st.form_submit_button("Add Patient")
                    
                    if submit_patient:
                        if not patient_name:
                            st.error("Patient name is required.")
                        else:
                            new_patient = pd.DataFrame({
                                "ID": [patient_id],
                                "Name": [patient_name],
                                "Age": [patient_age],
                                "Gender": [patient_gender],
                                "BloodGroup": [patient_blood],
                                "Phone": [patient_phone],
                                "Email": [patient_email],
                                "Address": [patient_address],
                                "EmergencyContact": [patient_emergency_contact],
                                "Medications": [patient_medications],
                                "Allergies": [patient_allergies],
                                "Conditions": [patient_conditions]
                            })
                            
                            patient_data = pd.concat([patient_data, new_patient], ignore_index=True)
                            patient_data.to_csv("patient_data.csv", index=False)
                            
                            st.success(f"Patient '{patient_name}' added successfully.")
                            log_activity(admin_id, f"Added new patient: {patient_name} ({patient_id})")
                else:
                    st.warning("No available user IDs for new patients. Please add a user first in the 'Manage Users' tab.")
            
            # Update patient section (moved outside form)
            st.subheader("Update Patient Information")
            if not patient_data.empty:
                patient_to_update = st.selectbox("Select Patient to Update", [""] + patient_data["ID"].tolist())
                
                if patient_to_update:
                    current_patient = patient_data[patient_data["ID"] == patient_to_update].iloc[0]
                    
                    with st.form("update_patient_form"):
                        updated_name = st.text_input("Full Name", value=current_patient["Name"])
                        updated_age = st.number_input("Age", min_value=0, max_value=150, value=int(current_patient["Age"]))
                        updated_gender = st.selectbox("Gender", ["Male", "Female", "Other"], 
                                                    index=["Male", "Female", "Other"].index(current_patient["Gender"]))
                        updated_blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
                                                   index=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].index(current_patient["BloodGroup"]))
                        updated_phone = st.text_input("Phone Number", value=str(current_patient["Phone"]))
                        updated_email = st.text_input("Email", value=str(current_patient["Email"]))
                        updated_address = st.text_area("Address", value=str(current_patient["Address"]))
                        updated_emergency = st.text_input("Emergency Contact", value=str(current_patient["EmergencyContact"]))
                        updated_medications = st.text_area("Current Medications", value=str(current_patient["Medications"]))
                        updated_allergies = st.text_area("Allergies", value=str(current_patient["Allergies"]))
                        updated_conditions = st.text_area("Medical Conditions", value=str(current_patient["Conditions"]))
                        
                        submit_update = st.form_submit_button("Update Patient")
                        
                        if submit_update:
                            # Update the patient data
                            patient_data.loc[patient_data["ID"] == patient_to_update, "Name"] = updated_name
                            patient_data.loc[patient_data["ID"] == patient_to_update, "Age"] = updated_age
                            patient_data.loc[patient_data["ID"] == patient_to_update, "Gender"] = updated_gender
                            patient_data.loc[patient_data["ID"] == patient_to_update, "BloodGroup"] = updated_blood
                            patient_data.loc[patient_data["ID"] == patient_to_update, "Phone"] = updated_phone
                            patient_data.loc[patient_data["ID"] == patient_to_update, "Email"] = updated_email
                            patient_data.loc[patient_data["ID"] == patient_to_update, "Address"] = updated_address
                            patient_data.loc[patient_data["ID"] == patient_to_update, "EmergencyContact"] = updated_emergency
                            patient_data.loc[patient_data["ID"] == patient_to_update, "Medications"] = updated_medications
                            patient_data.loc[patient_data["ID"] == patient_to_update, "Allergies"] = updated_allergies
                            patient_data.loc[patient_data["ID"] == patient_to_update, "Conditions"] = updated_conditions
                            
                            patient_data.to_csv("patient_data.csv", index=False)
                            st.success(f"Patient '{updated_name}' updated successfully.")
                            log_activity(admin_id, f"Updated patient information: {updated_name} ({patient_to_update})")
        
        # Tab 4: Manage Doctors
        # Tab 4: Manage Doctors (Fixed)
        with tab4:
            st.header("Manage Doctors")
            
            # Display current doctors
            st.subheader("Current Doctors")
            if not doctor_data.empty:
                st.dataframe(doctor_data)
            else:
                st.info("No doctor data available.")
            
            # Add new doctor
            st.subheader("Add New Doctor")
            
            # Get available doctor IDs
            available_doctor_ids = [uid for uid in credentials_df[credentials_df["category"] == "doctor"]["ID"].tolist() 
                                if uid not in doctor_data["ID"].values]
            
            if available_doctor_ids:
                with st.form("add_doctor_form"):
                    doctor_id = st.selectbox("Doctor ID", available_doctor_ids)
                    doctor_name = st.text_input("Full Name")
                    doctor_specialization = st.text_input("Specialization")
                    doctor_department = st.text_input("Department")
                    doctor_phone = st.text_input("Phone Number")
                    doctor_email = st.text_input("Email")
                    doctor_experience = st.number_input("Years of Experience", min_value=0, max_value=50, value=5)
                    doctor_qualifications = st.text_area("Qualifications")
                    doctor_schedule = st.text_area("Schedule (Days and Hours)")
                    
                    submit_doctor = st.form_submit_button("Add Doctor")
                    
                    if submit_doctor:
                        if not doctor_name:
                            st.error("Doctor name is required.")
                        else:
                            new_doctor = pd.DataFrame({
                                "ID": [doctor_id],
                                "Name": [doctor_name],
                                "Specialization": [doctor_specialization],
                                "Department": [doctor_department],
                                "Phone": [doctor_phone],
                                "Email": [doctor_email],
                                "Experience": [doctor_experience],
                                "Qualifications": [doctor_qualifications],
                                "Schedule": [doctor_schedule]
                            })
                            
                            doctor_data = pd.concat([doctor_data, new_doctor], ignore_index=True)
                            doctor_data.to_csv("doctor_data.csv", index=False)
                            
                            st.success(f"Doctor '{doctor_name}' added successfully.")
                            log_activity(admin_id, f"Added new doctor: {doctor_name} ({doctor_id})")
            else:
                st.warning("No available doctor IDs. Please add a doctor user first in the 'Manage Users' tab.")
                st.info("💡 **How to add a doctor:**\n1. Go to the 'Manage Users' tab\n2. Add a new user with category 'doctor'\n3. Return here to add doctor details")
            
            # Update doctor section (if there are existing doctors)
            if not doctor_data.empty:
                st.subheader("Update Doctor Information")
                doctor_to_update = st.selectbox("Select Doctor to Update", [""] + doctor_data["ID"].tolist())
                
                if doctor_to_update:
                    current_doctor = doctor_data[doctor_data["ID"] == doctor_to_update].iloc[0]
                    
                    with st.form("update_doctor_form"):
                        updated_name = st.text_input("Full Name", value=current_doctor["Name"])
                        updated_specialization = st.text_input("Specialization", value=str(current_doctor["Specialization"]))
                        updated_department = st.text_input("Department", value=str(current_doctor["Department"]))
                        updated_phone = st.text_input("Phone Number", value=str(current_doctor["Phone"]))
                        updated_email = st.text_input("Email", value=str(current_doctor["Email"]))
                        updated_experience = st.number_input("Years of Experience", min_value=0, max_value=50, 
                                                        value=int(current_doctor["Experience"]))
                        updated_qualifications = st.text_area("Qualifications", value=str(current_doctor["Qualifications"]))
                        updated_schedule = st.text_area("Schedule", value=str(current_doctor["Schedule"]))
                        
                        submit_update = st.form_submit_button("Update Doctor")
                        
                        if submit_update:
                            # Update the doctor data
                            doctor_data.loc[doctor_data["ID"] == doctor_to_update, "Name"] = updated_name
                            doctor_data.loc[doctor_data["ID"] == doctor_to_update, "Specialization"] = updated_specialization
                            doctor_data.loc[doctor_data["ID"] == doctor_to_update, "Department"] = updated_department
                            doctor_data.loc[doctor_data["ID"] == doctor_to_update, "Phone"] = updated_phone
                            doctor_data.loc[doctor_data["ID"] == doctor_to_update, "Email"] = updated_email
                            doctor_data.loc[doctor_data["ID"] == doctor_to_update, "Experience"] = updated_experience
                            doctor_data.loc[doctor_data["ID"] == doctor_to_update, "Qualifications"] = updated_qualifications
                            doctor_data.loc[doctor_data["ID"] == doctor_to_update, "Schedule"] = updated_schedule
                            
                            doctor_data.to_csv("doctor_data.csv", index=False)
                            st.success(f"Doctor '{updated_name}' updated successfully.")
                            log_activity(admin_id, f"Updated doctor information: {updated_name} ({doctor_to_update})")
                
                # Delete doctor section (outside form)
                st.subheader("Delete Doctor")
                doctor_to_delete = st.selectbox("Select Doctor to Delete", [""] + doctor_data["ID"].tolist())
                
                if doctor_to_delete and st.button("Delete Doctor"):
                    # Remove from doctor data
                    doctor_data = doctor_data[doctor_data["ID"] != doctor_to_delete]
                    doctor_data.to_csv("doctor_data.csv", index=False)
                    
                    st.success(f"Doctor '{doctor_to_delete}' deleted successfully.")
                    log_activity(admin_id, f"Deleted doctor: {doctor_to_delete}")
                    st.rerun()  # Refresh to update the display
        # Tab 5: Manage Pharmacy
        with tab5:
            st.header("Manage Pharmacy")
            
            # Load pharmacy data
            try:
                pharmacy_data = pd.read_csv("pharmacy_data.csv")
            except FileNotFoundError:
                pharmacy_data = pd.DataFrame(columns=["ID", "Name", "Department", "Phone", "Email", "Shift"])
                pharmacy_data.to_csv("pharmacy_data.csv", index=False)
            
            # Display current pharmacy assistants
            st.subheader("Current Pharmacy Assistants")
            if not pharmacy_data.empty:
                st.dataframe(pharmacy_data)
            else:
                st.info("No pharmacy assistant data available.")
            
            # Add new pharmacy assistant
            st.subheader("Add New Pharmacy Assistant")
            with st.form("add_pharmacy_form"):
                pharm_id = st.selectbox("Pharmacy Assistant ID", 
                    [uid for uid in credentials_df[credentials_df["category"] == "pharmassist"]["ID"].tolist() 
                     if uid not in pharmacy_data["ID"].values])
                
                if pharm_id:
                    pharm_name = st.text_input("Full Name")
                    pharm_department = st.selectbox("Department", ["Inpatient Pharmacy", "Outpatient Pharmacy", "Clinical Pharmacy", "Emergency Pharmacy"])
                    pharm_phone = st.text_input("Phone Number")
                    pharm_email = st.text_input("Email")
                    pharm_shift = st.selectbox("Shift", ["Morning (6AM-2PM)", "Evening (2PM-10PM)", "Night (10PM-6AM)"])
                    
                    submit_pharm = st.form_submit_button("Add Pharmacy Assistant")
                    
                    if submit_pharm:
                        if not pharm_name:
                            st.error("Pharmacy assistant name is required.")
                        else:
                            new_pharm = pd.DataFrame({
                                "ID": [pharm_id],
                                "Name": [pharm_name],
                                "Department": [pharm_department],
                                "Phone": [pharm_phone],
                                "Email": [pharm_email],
                                "Shift": [pharm_shift]
                            })
                            
                            pharmacy_data = pd.concat([pharmacy_data, new_pharm], ignore_index=True)
                            pharmacy_data.to_csv("pharmacy_data.csv", index=False)
                            
                            st.success(f"Pharmacy Assistant '{pharm_name}' added successfully.")
                            log_activity(admin_id, f"Added new pharmacy assistant: {pharm_name} ({pharm_id})")
                else:
                    st.warning("No available pharmacy assistant IDs. Please add a pharmassist user first in the 'Manage Users' tab.")
        
        # Tab 6: System Analysis (Fixed - Moved button outside form context)
        with tab6:
            st.header("System Data Analysis")
            
            # System statistics
            st.subheader("📊 System Statistics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**User Distribution**")
                user_category_counts = credentials_df["category"].value_counts()
                st.bar_chart(user_category_counts)
                
                if not patient_data.empty and "Age" in patient_data.columns:
                    st.markdown("**Patient Age Distribution**")
                    age_ranges = pd.cut(patient_data["Age"], bins=[0, 18, 35, 50, 65, 100], labels=["0-18", "19-35", "36-50", "51-65", "65+"])
                    age_dist = age_ranges.value_counts()
                    st.bar_chart(age_dist)
            
            with col2:
                if not patient_data.empty and "Gender" in patient_data.columns:
                    st.markdown("**Patient Gender Distribution**")
                    gender_counts = patient_data["Gender"].value_counts()
                    st.bar_chart(gender_counts)
                
                if not patient_data.empty and "BloodGroup" in patient_data.columns:
                    st.markdown("**Blood Group Distribution**")
                    blood_counts = patient_data["BloodGroup"].value_counts()
                    st.bar_chart(blood_counts)
            
            # AI-powered data analysis chatbot (Fixed - Button outside form)
            st.subheader("🤖 AI Data Analysis Assistant")
            st.markdown("Ask questions about your hospital data and get AI-powered insights!")
            
            query = st.text_input("Enter your question about the hospital data:", 
                                placeholder="e.g., What is the average age of patients? Which medications are most common?")
            
            if st.button("Analyze Data"):
                if query:
                    with st.spinner("Analyzing data..."):
                        response = data_analysis_chatbot(query, patient_data, doctor_data, credentials_df)
                        st.markdown("**Analysis Result:**")
                        st.write(response)
                        log_activity(admin_id, f"Used AI analysis for query: {query}")
                else:
                    st.warning("Please enter a question to analyze.")
            
            # Export data options (Fixed - Buttons outside form)
            st.subheader("📤 Export Data")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Export Patient Data"):
                    csv = patient_data.to_csv(index=False)
                    st.download_button(
                        label="Download Patient Data CSV",
                        data=csv,
                        file_name=f"patient_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    log_activity(admin_id, "Exported patient data")
            
            with col2:
                if st.button("Export Doctor Data"):
                    csv = doctor_data.to_csv(index=False)
                    st.download_button(
                        label="Download Doctor Data CSV",
                        data=csv,
                        file_name=f"doctor_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    log_activity(admin_id, "Exported doctor data")
            
            with col3:
                if st.button("Export System Logs"):
                    try:
                        with open("log.txt", "r") as log_file:
                            logs = log_file.read()
                            st.download_button(
                                label="Download System Logs",
                                data=logs,
                                file_name=f"system_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain"
                            )
                            log_activity(admin_id, "Exported system logs")
                    except FileNotFoundError:
                        st.error("Log file not found.")
        
        # Tab 7: Biometric Access Management (Fixed - All buttons outside forms)
        with tab7:
            st.header("🔐 Biometric Access Management")
            
            # Display biometric registration status
            try:
                biometric_data = pd.read_csv("biometric_data.csv")
                
                st.subheader("📊 Biometric Registration Status")
                
                if not biometric_data.empty:
                    # Create status overview
                    total_users = len(credentials_df)
                    biometric_users = len(biometric_data)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Users", total_users)
                    with col2:
                        st.metric("Biometric Enabled", biometric_users)
                    with col3:
                        coverage = (biometric_users / total_users) * 100 if total_users > 0 else 0
                        st.metric("Coverage", f"{coverage:.1f}%")
                    
                    # Display biometric data table
                    st.subheader("📋 Registered Biometric Users")
                    
                    # Create a display version of biometric data
                    display_data = biometric_data.copy()
                    display_data['Face Recognition'] = display_data['face_encoding'].apply(
                        lambda x: "✅ Registered" if pd.notna(x) and x != '' else "❌ Not Set"
                    )
                    display_data['Fingerprint'] = display_data['fingerprint_hash'].apply(
                        lambda x: "✅ Registered" if pd.notna(x) and x != '' else "❌ Not Set"
                    )
                    
                    # Show only relevant columns
                    st.dataframe(display_data[['ID', 'Face Recognition', 'Fingerprint', 'registration_date']])
                    
                    # Biometric test interface (Fixed - Button outside form)
                    st.subheader("🧪 Test Biometric Authentication")
                    
                    if st.button("🔍 Test Biometric Login"):
                        biometric_auth = BiometricAuth()
                        test_user = biometric_auth.biometric_login_interface()
                        
                        if test_user:
                            st.success(f"✅ Successfully authenticated user: {test_user}")
                            log_activity(admin_id, f"Tested biometric authentication for user: {test_user}")
                        else:
                            st.error("❌ Biometric authentication failed")
                    
                    # Manual biometric registration for existing users (Fixed - Button outside form)
                    st.subheader("🔄 Manual Biometric Registration")
                    
                    # Find users without biometric data
                    users_without_biometric = []
                    for user_id in credentials_df["ID"].tolist():
                        if user_id not in biometric_data["ID"].values:
                            users_without_biometric.append(user_id)
                    
                    if users_without_biometric:
                        selected_user = st.selectbox("Select user for biometric registration:", 
                                                   [""] + users_without_biometric)
                        
                        if selected_user:
                            st.info(f"Setting up biometric registration for: {selected_user}")
                            
                            face_image, fingerprint_hash, biometric_auth = integrate_biometric_registration()
                            
                            if st.button(f"💾 Register Biometric Data for {selected_user}"):
                                if face_image is not None or fingerprint_hash is not None:
                                    success = biometric_auth.register_biometric_data(
                                        selected_user, face_image, fingerprint_hash
                                    )
                                    if success:
                                        st.success(f"✅ Biometric data registered for {selected_user}!")
                                        log_activity(admin_id, f"Manually registered biometric data for user: {selected_user}")
                                        st.rerun()  # Refresh to update the display
                                    else:
                                        st.error("❌ Failed to register biometric data.")
                                else:
                                    st.warning("⚠️ No biometric data captured. Please capture face or fingerprint.")
                    else:
                        st.info("✅ All users have biometric data registered!")
                    
                    # Biometric data management (Fixed - Buttons outside forms)
                    st.subheader("🗑️ Remove Biometric Data")
                    
                    if not biometric_data.empty:
                        user_to_remove_bio = st.selectbox("Select user to remove biometric data:", 
                                                        [""] + biometric_data["ID"].tolist())
                        
                        if user_to_remove_bio and st.button(f"🗑️ Remove Biometric Data for {user_to_remove_bio}"):
                            # Remove from biometric_data.csv
                            biometric_data = biometric_data[biometric_data["ID"] != user_to_remove_bio]
                            biometric_data.to_csv("biometric_data.csv", index=False)
                            
                            # Remove from face encodings pickle file
                            try:
                                import pickle
                                with open("face_encodings.pkl", 'rb') as f:
                                    face_encodings = pickle.load(f)
                                if user_to_remove_bio in face_encodings:
                                    del face_encodings[user_to_remove_bio]
                                    with open("face_encodings.pkl", 'wb') as f:
                                        pickle.dump(face_encodings, f)
                            except:
                                pass
                            
                            st.success(f"✅ Biometric data removed for {user_to_remove_bio}")
                            log_activity(admin_id, f"Removed biometric data for user: {user_to_remove_bio}")
                            st.rerun()  # Refresh to update the display
                
                else:
                    st.info("No biometric data found. Users need to register their biometric information.")
                    
                    # Show all users who can register biometric data
                    st.subheader("👥 Users Available for Biometric Registration")
                    all_users = credentials_df["ID"].tolist()
                    
                    if all_users:
                        selected_new_user = st.selectbox("Select user for new biometric registration:", 
                                                       [""] + all_users)
                        
                        if selected_new_user:
                            st.info(f"Setting up biometric registration for: {selected_new_user}")
                            
                            face_image, fingerprint_hash, biometric_auth = integrate_biometric_registration()
                            
                            if st.button(f"💾 Register First Biometric Data for {selected_new_user}"):
                                if face_image is not None or fingerprint_hash is not None:
                                    success = biometric_auth.register_biometric_data(
                                        selected_new_user, face_image, fingerprint_hash
                                    )
                                    if success:
                                        st.success(f"✅ First biometric data registered for {selected_new_user}!")
                                        log_activity(admin_id, f"First biometric registration for user: {selected_new_user}")
                                        st.rerun()  # Refresh to update the display
                                    else:
                                        st.error("❌ Failed to register biometric data.")
                                else:
                                    st.warning("⚠️ No biometric data captured. Please capture face or fingerprint.")
                    else:
                        st.warning("No users found in the system.")
            
            except FileNotFoundError:
                st.info("No biometric data file found. This is normal for a new system.")
                
                # Initialize biometric system for first time
                st.subheader("🚀 Initialize Biometric System")
                st.markdown("Set up the first biometric user to initialize the system.")
                
                if not credentials_df.empty:
                    first_user = st.selectbox("Select first user for biometric setup:", 
                                            [""] + credentials_df["ID"].tolist())
                    
                    if first_user:
                        st.info(f"Initializing biometric system with user: {first_user}")
                        
                        face_image, fingerprint_hash, biometric_auth = integrate_biometric_registration()
                        
                        if st.button(f"🚀 Initialize System with {first_user}"):
                            if face_image is not None or fingerprint_hash is not None:
                                success = biometric_auth.register_biometric_data(
                                    first_user, face_image, fingerprint_hash
                                )
                                if success:
                                    st.success(f"✅ Biometric system initialized with {first_user}!")
                                    log_activity(admin_id, f"Initialized biometric system with user: {first_user}")
                                    st.rerun()  # Refresh to update the display
                                else:
                                    st.error("❌ Failed to initialize biometric system.")
                            else:
                                st.warning("⚠️ No biometric data captured. Please capture face or fingerprint.")
                else:
                    st.warning("No users found. Please add users first in the 'Manage Users' tab.")
            
            # System maintenance and cleanup (Fixed - Buttons outside forms)
            st.subheader("🔧 System Maintenance")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🧹 Clean Orphaned Biometric Data"):
                    try:
                        biometric_data = pd.read_csv("biometric_data.csv")
                        valid_users = credentials_df["ID"].tolist()
                        
                        # Find orphaned biometric entries
                        orphaned_entries = biometric_data[~biometric_data["ID"].isin(valid_users)]
                        
                        if not orphaned_entries.empty:
                            # Remove orphaned entries
                            cleaned_data = biometric_data[biometric_data["ID"].isin(valid_users)]
                            cleaned_data.to_csv("biometric_data.csv", index=False)
                            
                            # Clean face encodings as well
                            try:
                                import pickle
                                with open("face_encodings.pkl", 'rb') as f:
                                    face_encodings = pickle.load(f)
                                
                                # Remove orphaned face encodings
                                cleaned_encodings = {k: v for k, v in face_encodings.items() if k in valid_users}
                                
                                with open("face_encodings.pkl", 'wb') as f:
                                    pickle.dump(cleaned_encodings, f)
                            except:
                                pass
                            
                            st.success(f"✅ Cleaned {len(orphaned_entries)} orphaned biometric entries")
                            log_activity(admin_id, f"Cleaned {len(orphaned_entries)} orphaned biometric entries")
                        else:
                            st.info("✅ No orphaned biometric data found")
                    except FileNotFoundError:
                        st.info("No biometric data to clean")
            
            with col2:
                if st.button("📊 Generate Biometric Report"):
                    try:
                        biometric_data = pd.read_csv("biometric_data.csv")
                        
                        report = f"""
# Biometric System Report
Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics
- Total Users in System: {len(credentials_df)}
- Users with Biometric Data: {len(biometric_data)}
- Coverage Rate: {(len(biometric_data) / len(credentials_df) * 100):.1f}%

## Registration Breakdown
"""
                        
                        # Face vs fingerprint breakdown
                        if not biometric_data.empty:
                            face_count = biometric_data['face_encoding'].notna().sum()
                            fingerprint_count = biometric_data['fingerprint_hash'].notna().sum()
                            both_count = ((biometric_data['face_encoding'].notna()) & 
                                        (biometric_data['fingerprint_hash'].notna())).sum()
                            
                            report += f"""
- Users with Face Recognition: {face_count}
- Users with Fingerprint: {fingerprint_count}
- Users with Both Methods: {both_count}
"""
                        
                        # Users without biometric data
                        users_without_bio = []
                        for user_id in credentials_df["ID"].tolist():
                            if user_id not in biometric_data["ID"].values:
                                user_category = credentials_df[credentials_df["ID"] == user_id]["category"].iloc[0]
                                users_without_bio.append(f"- {user_id} ({user_category})")
                        
                        if users_without_bio:
                            report += f"\n## Users Without Biometric Data ({len(users_without_bio)})\n"
                            report += "\n".join(users_without_bio)
                        else:
                            report += "\n## ✅ All users have biometric data registered!"
                        
                        st.download_button(
                            label="📊 Download Biometric Report",
                            data=report,
                            file_name=f"biometric_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown"
                        )
                        
                        st.success("✅ Biometric report generated!")
                        log_activity(admin_id, "Generated biometric report")
                        
                    except FileNotFoundError:
                        st.error("❌ No biometric data found to generate report")
    
    except FileNotFoundError as e:
        st.error(f"Required data file not found: {e}")
        st.info("Please ensure all required CSV files are present in the system directory.")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Please contact the system administrator for assistance.")

# Additional utility functions for admin operations
def reset_user_password(user_id, new_password):
    """Reset a user's password (admin function)"""
    try:
        credentials_df = pd.read_csv("credentials.csv")
        
        if user_id in credentials_df["ID"].values:
            hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
            credentials_df.loc[credentials_df["ID"] == user_id, "password"] = hashed_password
            credentials_df.to_csv("credentials.csv", index=False)
            return True
        return False
    except:
        return False

def backup_system_data():
    """Create a backup of all system data"""
    import shutil
    import zipfile
    from datetime import datetime
    
    try:
        backup_name = f"umid_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        with zipfile.ZipFile(backup_name, 'w') as backup_zip:
            # Add all CSV files
            for file in ["credentials.csv", "patient_data.csv", "doctor_data.csv", 
                        "pharmacy_data.csv", "biometric_data.csv"]:
                try:
                    backup_zip.write(file)
                except FileNotFoundError:
                    pass
            
            # Add log file
            try:
                backup_zip.write("log.txt")
            except FileNotFoundError:
                pass
            
            # Add face encodings
            try:
                backup_zip.write("face_encodings.pkl")
            except FileNotFoundError:
                pass
        
        return backup_name
    except Exception as e:
        return None

def get_system_health_status():
    """Check system health and return status"""
    health_status = {
        "overall": "healthy",
        "issues": [],
        "warnings": []
    }
    
    required_files = ["credentials.csv", "patient_data.csv", "doctor_data.csv"]
    
    for file in required_files:
        if not os.path.exists(file):
            health_status["issues"].append(f"Missing required file: {file}")
            health_status["overall"] = "critical"
    
    # Check for empty critical files
    try:
        credentials_df = pd.read_csv("credentials.csv")
        if credentials_df.empty:
            health_status["issues"].append("No users in system")
            health_status["overall"] = "critical"
        elif len(credentials_df[credentials_df["category"] == "admin"]) == 0:
            health_status["warnings"].append("No admin users found")
            if health_status["overall"] == "healthy":
                health_status["overall"] = "warning"
    except:
        pass
    
    # Check biometric system
    try:
        biometric_data = pd.read_csv("biometric_data.csv")
        if biometric_data.empty:
            health_status["warnings"].append("No biometric data registered")
            if health_status["overall"] == "healthy":
                health_status["overall"] = "warning"
    except:
        health_status["warnings"].append("Biometric system not initialized")
        if health_status["overall"] == "healthy":
            health_status["overall"] = "warning"
    
    return health_status

if __name__ == "__main__":
    show_admin_page()