import streamlit as st
import pandas as pd
import datetime
import os

def log_activity(pharmassist_id, action):
    """Log pharmacy assistant activities to log file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a") as log_file:
        log_file.write(f"{timestamp} - Pharmassist {pharmassist_id}: {action}\n")

def show_pharmassist_page(pharmassist_id):
    """Display pharmacy assistant dashboard"""
    st.title("Pharmacy Assistant Dashboard")
    st.sidebar.markdown(f"### Logged in as: {pharmassist_id}")
    
    try:
        # Load required data
        patient_data = pd.read_csv("patient_data.csv")
        
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
        
        # Create medication inventory file if it doesn't exist
        if not os.path.exists("medication_inventory.csv"):
            inventory = pd.DataFrame(columns=[
                "MedicationID", "Name", "Dosage", "Quantity", "ExpiryDate"
            ])
            inventory.loc[0] = [
                "MED001", "Lisinopril", "10mg", 100, "2025-12-31"
            ]
            inventory.loc[1] = [
                "MED002", "Aspirin", "81mg", 200, "2026-06-30"
            ]
            inventory.loc[2] = [
                "MED003", "Amoxicillin", "500mg", 50, "2025-06-15"
            ]
            inventory.to_csv("medication_inventory.csv", index=False)
        
        # Load medication inventory
        inventory = pd.read_csv("medication_inventory.csv")
        
        # Create transaction history file if it doesn't exist
        if not os.path.exists("medication_transactions.csv"):
            transactions = pd.DataFrame(columns=[
                "TransactionID", "PrescriptionID", "PatientID", "Date", 
                "Medications", "Quantity", "PharmassistID"
            ])
            transactions.to_csv("medication_transactions.csv", index=False)
            
        # Load transaction history
        transactions = pd.read_csv("medication_transactions.csv")
        
        # Create tabs for different sections
        tab1, tab2, tab3 = st.tabs([
            "View Prescriptions", "Dispense Medications", "Inventory Management"
        ])
        
        # Tab 1: View Prescriptions
        with tab1:
            st.header("Patient Prescriptions")
            
            # Search for patient prescriptions
            patient_id = st.text_input("Enter Patient ID:")
            
            if st.button("Search Prescriptions"):
                if patient_id:
                    # Get patient details
                    patient = patient_data[patient_data["ID"] == patient_id]
                    
                    if not patient.empty:
                        patient_info = patient.iloc[0]
                        st.success(f"Patient found: {patient_info['Name']}")
                        
                        # Display patient info
                        st.subheader("Patient Information")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**ID:** {patient_info['ID']}")
                            st.write(f"**Name:** {patient_info['Name']}")
                            st.write(f"**Age:** {patient_info['Age']}")
                            st.write(f"**Gender:** {patient_info['Gender']}")
                        
                        with col2:
                            st.write(f"**Blood Group:** {patient_info['BloodGroup']}")
                            st.write(f"**Allergies:** {patient_info['Allergies']}")
                            st.write(f"**Last Checkup:** {patient_info['LastCheckup']}")
                        
                        # Get prescriptions for this patient
                        patient_prescriptions = prescriptions[prescriptions["PatientID"] == patient_id]
                        
                        if not patient_prescriptions.empty:
                            st.subheader("Prescriptions")
                            for i, rx in patient_prescriptions.iterrows():
                                with st.expander(f"Prescription {rx['PrescriptionID']} - {rx['Date']} - {rx['Status']}"):
                                    st.write(f"**Doctor ID:** {rx['DoctorID']}")
                                    st.write(f"**Medications:** {rx['Medications']}")
                                    st.write(f"**Dosage:** {rx['Dosage']}")
                                    st.write(f"**Instructions:** {rx['Instructions']}")
                                    st.write(f"**Status:** {rx['Status']}")
                        else:
                            st.info("No prescriptions found for this patient.")
                    else:
                        st.error(f"No patient found with ID: {patient_id}")
                else:
                    st.warning("Please enter a Patient ID")
        
        # Tab 2: Dispense Medications
        with tab2:
            st.header("Dispense Medications")
            
            # Get pending prescriptions
            pending_rx = prescriptions[prescriptions["Status"] == "Pending"]
            
            if not pending_rx.empty:
                st.subheader("Pending Prescriptions")
                
                # Select prescription to dispense
                rx_ids = pending_rx["PrescriptionID"].tolist()
                selected_rx_id = st.selectbox("Select Prescription ID", rx_ids)
                
                if selected_rx_id:
                    rx = pending_rx[pending_rx["PrescriptionID"] == selected_rx_id].iloc[0]
                    
                    st.write(f"**Patient ID:** {rx['PatientID']}")
                    
                    # Get patient name
                    patient_name = patient_data[patient_data["ID"] == rx['PatientID']].iloc[0]["Name"] if not patient_data[patient_data["ID"] == rx['PatientID']].empty else "Unknown"
                    st.write(f"**Patient Name:** {patient_name}")
                    
                    st.write(f"**Doctor ID:** {rx['DoctorID']}")
                    st.write(f"**Date Prescribed:** {rx['Date']}")
                    
                    # Display medications
                    medications_list = [med.strip() for med in rx['Medications'].split(',')]
                    dosage_list = [dose.strip() for dose in rx['Dosage'].split(',')]
                    
                    st.subheader("Medications to Dispense")
                    
                    # Check if medications are in stock
                    medications_in_stock = True
                    for i, medication in enumerate(medications_list):
                        in_stock = medication in inventory["Name"].values
                        
                        if in_stock:
                            med_inventory = inventory[inventory["Name"] == medication].iloc[0]
                            quantity = med_inventory["Quantity"]
                            st.write(f"✓ {medication} - {dosage_list[i]} (Available: {quantity})")
                        else:
                            medications_in_stock = False
                            st.write(f"❌ {medication} - {dosage_list[i]} (OUT OF STOCK)")
                    
                    st.write(f"**Instructions:** {rx['Instructions']}")
                    
                    # Confirm dispensing
                    if medications_in_stock:
                        if st.button("Dispense Medications"):
                            # Update prescription status
                            prescriptions.loc[prescriptions["PrescriptionID"] == selected_rx_id, "Status"] = "Dispensed"
                            prescriptions.to_csv("prescriptions.csv", index=False)
                            
                            # Update inventory
                            for medication in medications_list:
                                inventory.loc[inventory["Name"] == medication, "Quantity"] -= 1
                            inventory.to_csv("medication_inventory.csv", index=False)
                            
                            # Create transaction record
                            new_transaction = pd.DataFrame({
                                "TransactionID": [f"T{len(transactions) + 1:05d}"],
                                "PrescriptionID": [selected_rx_id],
                                "PatientID": [rx['PatientID']],
                                "Date": [datetime.datetime.now().strftime("%Y-%m-%d")],
                                "Medications": [rx['Medications']],
                                "Quantity": [len(medications_list)],
                                "PharmassistID": [pharmassist_id]
                            })
                            
                            transactions = pd.concat([transactions, new_transaction], ignore_index=True)
                            transactions.to_csv("medication_transactions.csv", index=False)
                            
                            st.success(f"Medications for prescription {selected_rx_id} dispensed successfully!")
                            log_activity(pharmassist_id, f"Dispensed medications for prescription {selected_rx_id}")
                    else:
                        st.error("Cannot dispense: Some medications are out of stock.")
            else:
                st.info("No pending prescriptions to dispense.")
        
        # Tab 3: Inventory Management
        with tab3:
            st.header("Medication Inventory")
            
            # Display current inventory
            st.dataframe(inventory)
            
            st.subheader("Recent Transactions")
            if not transactions.empty:
                st.dataframe(transactions.tail(10))
            else:
                st.info("No transaction records found.")
            
            # Add new medication to inventory
            st.subheader("Add New Medication")
            with st.form("add_medication_form"):
                med_id = st.text_input("Medication ID (e.g., MED004)")
                med_name = st.text_input("Medication Name")
                med_dosage = st.text_input("Dosage")
                med_quantity = st.number_input("Quantity", min_value=1, value=50)
                med_expiry = st.date_input("Expiry Date", value=datetime.datetime.now().date() + datetime.timedelta(days=365))
                
                submit_med = st.form_submit_button("Add Medication")
                
                if submit_med:
                    # Validate inputs
                    if not med_id or not med_name or not med_dosage:
                        st.error("All fields are required.")
                    elif med_id in inventory["MedicationID"].values:
                        st.error(f"Medication ID {med_id} already exists.")
                    else:
                        # Add new medication to inventory
                        new_medication = pd.DataFrame({
                            "MedicationID": [med_id],
                            "Name": [med_name],
                            "Dosage": [med_dosage],
                            "Quantity": [med_quantity],
                            "ExpiryDate": [med_expiry.strftime("%Y-%m-%d")]
                        })
                        
                        inventory = pd.concat([inventory, new_medication], ignore_index=True)
                        inventory.to_csv("medication_inventory.csv", index=False)
                        
                        st.success(f"Medication '{med_name}' added to inventory successfully!")
                        log_activity(pharmassist_id, f"Added new medication to inventory: {med_name}")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        log_activity(pharmassist_id, f"Error in pharmacy assistant dashboard: {str(e)}")

if __name__ == "__main__":
    # This will only run if the script is run directly, not when imported
    st.write("This is a module to be imported by the main application.")