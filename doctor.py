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

def log_activity(doctor_id, action):
    """Log doctor activities to log file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a") as log_file:
        log_file.write(f"{timestamp} - Doctor {doctor_id}: {action}\n")

def advanced_medical_chatbot(query):
    """
    Medical chatbot that uses a language model (base_llm) to generate responses
    to general healthcare questions in 30 words or less.
    """
    query = query.lower()
    prompt = f"You are a medical assistant. Provide a clear, accurate, and concise answer (max 30 words) to this general healthcare question:\n\n{query}"
    response = base_llm.invoke(prompt)
    return response.content if hasattr(response, "content") else "Error: No response received"

def show_doctor_page(doctor_id):
    """Display doctor dashboard"""
    st.title(f"Doctor Dashboard")
    st.sidebar.markdown(f"### Logged in as: {doctor_id}")
    
    # Load doctor data
    try:
        doctor_data = pd.read_csv("doctor_data.csv")
        doctor_info = doctor_data[doctor_data["ID"] == doctor_id]
        
        if not doctor_info.empty:
            doctor_details = doctor_info.iloc[0]
            
            # Display doctor information
            st.header("Doctor Information")
            st.write(f"**Name:** {doctor_details['Name']}")
            st.write(f"**Specialization:** {doctor_details['Specialization']}")
            st.write(f"**Experience:** {doctor_details['Experience']}")
            
            # Patient records section
            st.header("Patient Records")
            
            # Load patient data
            patient_data = pd.read_csv("patient_data.csv")
            
            # Search for patient by ID
            patient_id = st.text_input("Enter Patient ID to view their records:")
            
            if st.button("Search Patient"):
                if patient_id:
                    patient_record = patient_data[patient_data["ID"] == patient_id]
                    
                    if not patient_record.empty:
                        patient = patient_record.iloc[0]
                        
                        st.subheader(f"Patient: {patient['Name']} (ID: {patient['ID']})")
                        
                        # Display patient information in columns
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Age:** {patient['Age']}")
                            st.write(f"**Gender:** {patient['Gender']}")
                            st.write(f"**Blood Group:** {patient['BloodGroup']}")
                        
                        with col2:
                            st.write(f"**Medical History:** {patient['MedicalHistory']}")
                            st.write(f"**Current Medications:** {patient['Medications']}")
                            st.write(f"**Allergies:** {patient['Allergies']}")
                        
                        st.write(f"**Last Checkup:** {patient['LastCheckup']}")
                        
                        # Update doctor notes
                        st.subheader("Update Doctor Notes")
                        
                        current_notes = patient['DoctorNotes']
                        st.write("Current Notes:", current_notes)
                        
                        new_notes = st.text_area("Add/Update Notes:", value=current_notes)
                        
                        if st.button("Save Notes"):
                            # Update the notes in the dataframe
                            patient_data.loc[patient_data["ID"] == patient_id, "DoctorNotes"] = new_notes
                            # Save the updated dataframe to CSV
                            patient_data.to_csv("patient_data.csv", index=False)
                            st.success("Notes updated successfully!")
                            log_activity(doctor_id, f"Updated notes for patient {patient_id}")
                        
                        # Create prescription data file if it doesn't exist
                        if not os.path.exists("prescriptions.csv"):
                            prescriptions = pd.DataFrame(columns=[
                                "PrescriptionID", "PatientID", "DoctorID", "Date", 
                                "Medications", "Dosage", "Instructions", "Status"
                            ])
                            prescriptions.loc[0] = [
                                "RX00001", "patient1", "doctor1", "2024-12-15",
                                "Lisinopril, Aspirin", "10mg daily, 81mg daily",
                                "Take with food, Take in the morning", "Pending"
                            ]
                            prescriptions.to_csv("prescriptions.csv", index=False)

                        # Load prescription data
                        prescriptions = pd.read_csv("prescriptions.csv")

                        # Add prescription section for the currently viewed patient
                        st.subheader("Prescriptions")
                        
                        # Display existing prescriptions for this patient
                        patient_prescriptions = prescriptions[prescriptions["PatientID"] == patient_id]
                        
                        if not patient_prescriptions.empty:
                            st.write("Existing Prescriptions:")
                            for i, rx in patient_prescriptions.iterrows():
                                with st.expander(f"Prescription {rx['PrescriptionID']} - {rx['Date']} - {rx['Status']}"):
                                    st.write(f"**Medications:** {rx['Medications']}")
                                    st.write(f"**Dosage:** {rx['Dosage']}")
                                    st.write(f"**Instructions:** {rx['Instructions']}")
                        
                        # Add new prescription
                        st.write("Create New Prescription:")
                        with st.form(f"add_prescription_form_{patient_id}"):
                            # Generate prescription ID
                            next_rx_id = f"RX{len(prescriptions) + 1:05d}"
                            st.write(f"Prescription ID: {next_rx_id}")
                            
                            # Prescription details
                            medications = st.text_area("Medications (comma separated)")
                            dosage = st.text_area("Dosage (comma separated)")
                            instructions = st.text_area("Instructions")
                            date = st.date_input("Prescription Date", value=datetime.datetime.now().date())
                            
                            submit_prescription = st.form_submit_button("Create Prescription")
                            
                            if submit_prescription:
                                if not medications or not dosage:
                                    st.error("Medications and dosage are required.")
                                else:
                                    # Add new prescription
                                    new_prescription = pd.DataFrame({
                                        "PrescriptionID": [next_rx_id],
                                        "PatientID": [patient_id],
                                        "DoctorID": [doctor_id],
                                        "Date": [date.strftime("%Y-%m-%d")],
                                        "Medications": [medications],
                                        "Dosage": [dosage],
                                        "Instructions": [instructions],
                                        "Status": ["Pending"]
                                    })
                                    
                                    prescriptions = pd.concat([prescriptions, new_prescription], ignore_index=True)
                                    prescriptions.to_csv("prescriptions.csv", index=False)
                                    
                                    st.success(f"Prescription {next_rx_id} created successfully.")
                                    log_activity(doctor_id, f"Created prescription {next_rx_id} for patient {patient_id}")
                    
                    else:
                        st.error(f"No records found for Patient ID: {patient_id}")
                        log_activity(doctor_id, f"Searched for non-existent patient ID: {patient_id}")
                
                else:
                    st.warning("Please enter a Patient ID")
            
            # Also add a section to view and manage all prescriptions written by this doctor
            st.header("Your Prescriptions")
            
            # Load prescriptions data if it exists
            if os.path.exists("prescriptions.csv"):
                prescriptions = pd.read_csv("prescriptions.csv")
                doctor_prescriptions = prescriptions[prescriptions["DoctorID"] == doctor_id]

                if not doctor_prescriptions.empty:
                    # Sort by date (newest first)
                    doctor_prescriptions = doctor_prescriptions.sort_values(by="Date", ascending=False)
                    
                    for i, rx in doctor_prescriptions.iterrows():
                        # Get patient name
                        patient_name = "Unknown"
                        if rx["PatientID"] in patient_data["ID"].values:
                            patient_name = patient_data[patient_data["ID"] == rx["PatientID"]].iloc[0]["Name"]
                        
                        with st.expander(f"Prescription {rx['PrescriptionID']} - {patient_name} - {rx['Date']} - {rx['Status']}"):
                            st.write(f"**Patient ID:** {rx['PatientID']}")
                            st.write(f"**Medications:** {rx['Medications']}")
                            st.write(f"**Dosage:** {rx['Dosage']}")
                            st.write(f"**Instructions:** {rx['Instructions']}")
                            
                            # Allow cancellation if status is pending
                            if rx["Status"] == "Pending":
                                if st.button(f"Cancel Prescription {rx['PrescriptionID']}", key=f"cancel_{rx['PrescriptionID']}"):
                                    prescriptions.loc[prescriptions["PrescriptionID"] == rx["PrescriptionID"], "Status"] = "Cancelled"
                                    prescriptions.to_csv("prescriptions.csv", index=False)
                                    st.success(f"Prescription {rx['PrescriptionID']} cancelled.")
                                    log_activity(doctor_id, f"Cancelled prescription {rx['PrescriptionID']}")
                else:
                    st.info("You haven't created any prescriptions yet.")
            else:
                st.info("Prescription system is being initialized. Create your first prescription to get started.")
            
            # Advanced medical chatbot for doctors
            st.header("Medical Knowledge Assistant")
            st.write("Ask about diagnoses, treatments, or medical research:")
            
            query = st.text_input("Your medical query:")
            if query:
                response = advanced_medical_chatbot(query)
                st.write("**Medical Assistant:**", response)
                log_activity(doctor_id, f"Used advanced medical chatbot: '{query}'")
        
        else:
            st.error(f"No doctor record found for ID: {doctor_id}")
            log_activity(doctor_id, "Attempted to access doctor dashboard - No record found")
    
    except Exception as e:
        st.error(f"Error loading doctor data: {str(e)}")
        log_activity(doctor_id, f"Error accessing doctor data: {str(e)}")

if __name__ == "__main__":
    # This will only run if the script is run directly, not when imported
    st.write("This is a module to be imported by the main application.")