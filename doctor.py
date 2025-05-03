import streamlit as st
import pandas as pd
import datetime
import os

def log_activity(doctor_id, action):
    """Log doctor activities to log file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a") as log_file:
        log_file.write(f"{timestamp} - Doctor {doctor_id}: {action}\n")

def advanced_medical_chatbot(query):
    """Advanced medical chatbot for doctors"""
    query = query.lower()
    
    # Advanced medical responses for doctors
    if "diagnosis" in query or "symptoms" in query:
        return "Differential diagnosis should consider patient history, physical examination findings, laboratory results, and imaging studies. Consider using clinical decision support tools for complex cases."
    elif "treatment" in query or "protocol" in query:
        return "Treatment protocols should follow evidence-based guidelines while being tailored to individual patient factors including comorbidities, allergies, and preferences. Regular monitoring and follow-up is recommended."
    elif "medication" in query or "dosage" in query:
        return "Medication selection should consider efficacy, side effect profile, drug interactions, and patient-specific factors. Always verify dosing with appropriate references and check for contraindications."
    elif "research" in query or "study" in query:
        return "Recent medical research is accessible through PubMed, Cochrane Library, and specialized journals in your field. Consider consulting clinical practice guidelines for evidence-based recommendations."
    elif "referral" in query:
        return "Patient referrals should include comprehensive history, examination findings, diagnostic results, and specific clinical questions. Ensure proper communication channels with the specialist."
    elif "emergency" in query or "urgent" in query:
        return "For medical emergencies, stabilize the patient following ACLS/BLS protocols as appropriate, initiate critical interventions, and arrange for immediate transfer if necessary."
    else:
        return "I'm an advanced medical assistant for healthcare providers. For specific medical guidelines, please consult appropriate clinical resources. How else may I assist you with medical information?"

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
                    
                    else:
                        st.error(f"No records found for Patient ID: {patient_id}")
                        log_activity(doctor_id, f"Searched for non-existent patient ID: {patient_id}")
                
                else:
                    st.warning("Please enter a Patient ID")
            
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