import streamlit as st
import pandas as pd
import os
import datetime
import hashlib
from pathlib import Path
from admin import data_analysis_chatbot
from chat_bot import chat_bot

# Safe import of biometric authentication with error handling
try:
    from biometric_auth import BiometricAuth, integrate_biometric_registration, get_scanner_status, setup_scanner_demo_data
    BIOMETRIC_AVAILABLE = True
except ImportError as e:
    st.warning(f"Biometric module not available: {e}")
    BIOMETRIC_AVAILABLE = False
except Exception as e:
    st.error(f"Error loading biometric module: {e}")
    BIOMETRIC_AVAILABLE = False

def log_activity(user_id, action):
    """Log user activities to log file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("log.txt", "a", encoding='utf-8') as log_file:
            log_file.write(f"{timestamp} - User {user_id}: {action}\n")
    except Exception as e:
        st.error(f"Failed to log activity: {e}")

def load_credentials():
    """Load credentials from CSV file"""
    try:
        return pd.read_csv("credentials.csv")
    except FileNotFoundError:
        # Create default credentials file if it doesn't exist
        default_credentials = pd.DataFrame({
            "ID": ["admin1", "doctor1", "patient1", "pharmassist1"],
            "category": ["admin", "doctor", "user", "pharmassist"],
            "password": [
                hashlib.sha256("admin123".encode()).hexdigest(),
                hashlib.sha256("doctor123".encode()).hexdigest(),
                hashlib.sha256("patient123".encode()).hexdigest(),
                hashlib.sha256("pharma123".encode()).hexdigest()
            ]
        })
        default_credentials.to_csv("credentials.csv", index=False)
        return default_credentials

def verify_login(user_id, password, credentials_df):
    """Verify login credentials"""
    try:
        if user_id in credentials_df["ID"].values:
            user_row = credentials_df[credentials_df["ID"] == user_id]
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if user_row["password"].values[0] == hashed_password:
                return True, user_row["category"].values[0]
        return False, None
    except Exception as e:
        st.error(f"Login verification error: {e}")
        return False, None

def get_user_category(user_id, credentials_df):
    """Get user category from credentials"""
    try:
        if user_id in credentials_df["ID"].values:
            user_row = credentials_df[credentials_df["ID"] == user_id]
            return user_row["category"].values[0]
        return None
    except Exception as e:
        st.error(f"Error getting user category: {e}")
        return None

def create_required_files():
    """Create required CSV files if they don't exist"""
    try:
        # Create credentials.csv
        if not os.path.exists("credentials.csv"):
            load_credentials()
        
        # Create patient_data.csv
        if not os.path.exists("patient_data.csv"):
            patient_data = pd.DataFrame(columns=[
                "ID", "Name", "Age", "Gender", "BloodGroup", 
                "MedicalHistory", "Medications", "Allergies", 
                "LastCheckup", "DoctorNotes"
            ])
            sample_data = [
                ["patient1", "Sai", 35, "Male", "O+", "Hypertension", "Lisinopril", "None", "2024-12-15", "Regular checkup; BP slightly elevated"],
                ["patient2", "Imran", 42, "male", "A+", "Diabetes Type 2", "Metformin", "Penicillin", "2024-12-10", "Blood sugar levels stable"],
                ["patient3", "Aravindh", 28, "Male", "B-", "Asthma", "Albuterol", "None", "2024-12-12", "Mild asthma, well controlled"]
            ]
            for i, data in enumerate(sample_data):
                patient_data.loc[i] = data
            patient_data.to_csv("patient_data.csv", index=False)
        
        # Create doctor_data.csv
        if not os.path.exists("doctor_data.csv"):
            doctor_data = pd.DataFrame(columns=[
                "ID", "Name", "Specialization", "Experience", "Email", "Phone"
            ])
            sample_doctors = [
                ["doctor1", "Dr. Bharath", "Cardiologist", "15 years", "dr.jane@umid.com", "+1-555-123-4567"],
                ["doctor2", "Dr. Hariharan", "Endocrinologist", "12 years", "dr.michael@umid.com", "+1-555-123-4568"],
                ["doctor3", "Dr. Imran", "Pulmonologist", "8 years", "dr.sarah@umid.com", "+1-555-123-4569"]
            ]
            for i, data in enumerate(sample_doctors):
                doctor_data.loc[i] = data
            doctor_data.to_csv("doctor_data.csv", index=False)
        
        # Create appointments.csv
        if not os.path.exists("appointments.csv"):
            appointments_data = pd.DataFrame(columns=[
                "ID", "PatientID", "DoctorID", "Date", "Time", "Status", "Notes"
            ])
            sample_appointments = [
                ["APT001", "patient1", "doctor1", "2024-12-20", "10:00", "Scheduled", "Regular checkup"],
                ["APT002", "patient2", "doctor2", "2024-12-21", "14:30", "Scheduled", "Diabetes follow-up"],
                ["APT003", "patient3", "doctor3", "2024-12-22", "09:15", "Scheduled", "Asthma management"]
            ]
            for i, data in enumerate(sample_appointments):
                appointments_data.loc[i] = data
            appointments_data.to_csv("appointments.csv", index=False)
        
        # Create inventory.csv
        if not os.path.exists("inventory.csv"):
            inventory_data = pd.DataFrame(columns=[
                "MedicationID", "Name", "Stock", "MinStock", "Price", "ExpiryDate", "Supplier"
            ])
            sample_inventory = [
                ["MED001", "Lisinopril", 150, 20, 15.50, "2025-06-15", "PharmaCorp"],
                ["MED002", "Metformin", 200, 25, 12.30, "2025-08-20", "MediSupply"],
                ["MED003", "Albuterol", 80, 15, 25.75, "2025-04-10", "HealthPlus"],
                ["MED004", "Aspirin", 300, 50, 8.99, "2025-12-30", "PharmaCorp"],
                ["MED005", "Ibuprofen", 180, 30, 11.25, "2025-10-15", "MediSupply"]
            ]
            for i, data in enumerate(sample_inventory):
                inventory_data.loc[i] = data
            inventory_data.to_csv("inventory.csv", index=False)
        
        # Create log file
        log_file = Path("log.txt")
        if not log_file.exists():
            log_file.touch()
        
        # Setup demo biometric data if available and not already setup
        if BIOMETRIC_AVAILABLE and 'biometric_demo_setup' not in st.session_state:
            try:
                success, message = setup_scanner_demo_data()
                st.session_state.biometric_demo_setup = True
                if success:
                    st.info(f"✅ {message}")
                else:
                    st.warning(f"⚠️ {message}")
            except Exception as e:
                st.warning(f"Biometric setup warning: {e}")
                
    except Exception as e:
        st.error(f"Error creating required files: {e}")

def show_traditional_login(credentials_df):
    """Show traditional username/password login"""
    st.subheader("🔑 Credential Login")
    
    with st.form("login_form"):
        user_id = st.text_input("User ID", placeholder="Enter your User ID")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit_button = st.form_submit_button("🔓 Login with Credentials", use_container_width=True)
        
        if submit_button:
            if not user_id or not password:
                st.error("❌ Please enter both User ID and password")
                return
                
            is_valid, category = verify_login(user_id, password, credentials_df)
            if is_valid:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.user_category = category
                st.session_state.login_method = "credentials"
                log_activity(user_id, f"Logged in via credentials as {category}")
                st.success(f"✅ Welcome {user_id}! Logged in as {category}")
                st.rerun()
            else:
                st.error("❌ Invalid User ID or password")

def show_fingerprint_login(credentials_df):
    """Show fingerprint authentication login"""
    st.subheader("👆 Fingerprint Authentication")
    
    if not BIOMETRIC_AVAILABLE:
        st.warning("⚠️ Biometric authentication is not available")
        return
    
    try:
        biometric_auth = BiometricAuth()
        
        # Check scanner status
        scanner_connected, scanner_status = get_scanner_status()
        
        if scanner_connected:
            st.success(f"🟢 Scanner Status: {scanner_status}")
        else:
            st.warning(f"🟡 Scanner Status: {scanner_status}")
            st.info("ℹ️ Running in demo mode. In production, connect a real fingerprint scanner.")
        
        # Check if there are any registered biometric users
        try:
            biometric_data = pd.read_csv("biometric_data.csv")
            if biometric_data.empty:
                st.info("ℹ️ No biometric data found. Please register your fingerprint first or use credential login.")
                return
        except FileNotFoundError:
            st.info("ℹ️ No biometric data found. Please register your fingerprint first or use credential login.")
            return
        
        # Authentication section
        st.markdown("### 🔐 Authenticate with Fingerprint")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("👆 Place your finger on the scanner when ready")
            
            if st.button("🔍 Scan Fingerprint", use_container_width=True, type="primary"):
                with st.spinner("🔄 Scanning fingerprint..."):
                    # Attempt fingerprint authentication
                    try:
                        user_id, message = biometric_auth.authenticate_fingerprint()
                        
                        if user_id:
                            category = get_user_category(user_id, credentials_df)
                            if category:
                                st.session_state.logged_in = True
                                st.session_state.user_id = user_id
                                st.session_state.user_category = category
                                st.session_state.login_method = "fingerprint"
                                log_activity(user_id, "Successful fingerprint login")
                                st.success(f"✅ {message}")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ User not found in system")
                                log_activity(user_id, "Fingerprint authenticated but user not in system")
                        else:
                            st.error(f"❌ {message}")
                            log_activity("Unknown", "Failed fingerprint login attempt")
                    except Exception as e:
                        st.error(f"❌ Authentication error: {e}")
        
        with col2:
            st.markdown("**Quick Tips:**")
            st.markdown("• Clean your finger")
            st.markdown("• Press firmly")
            st.markdown("• Hold steady")
            st.markdown("• Try different angles")
            
    except Exception as e:
        st.error(f"Biometric authentication error: {e}")

def show_fingerprint_registration():
    """Show fingerprint registration interface"""
    st.subheader("📝 Fingerprint Registration")
    
    if not BIOMETRIC_AVAILABLE:
        st.warning("⚠️ Biometric authentication is not available")
        return
    
    # Check if user is logged in with credentials first
    if not st.session_state.get('logged_in', False) or st.session_state.get('login_method') != 'credentials':
        st.warning("⚠️ Please login with credentials first to register your fingerprint.")
        return
    
    try:
        user_id = st.session_state.user_id
        biometric_auth = BiometricAuth()
        
        # Check if user already has fingerprint registered
        existing_fingerprints = biometric_auth.get_user_fingerprints(user_id)
        
        if existing_fingerprints:
            st.info(f"✅ You already have a fingerprint registered.")
            
            with st.expander("📊 View Registration Details"):
                for fp in existing_fingerprints:
                    st.write(f"**Registered:** {fp.get('registration_date', 'Unknown')}")
                    st.write(f"**Last Used:** {fp.get('last_used', 'Never')}")
                    st.write(f"**Quality Score:** {fp.get('quality_score', 'N/A')}")
            
            if st.button("🗑️ Remove Current Fingerprint"):
                success, message = biometric_auth.remove_fingerprint(user_id)
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            
            return
        
        # Registration process
        st.markdown("### 👆 Register Your Fingerprint")
        
        scanner_connected, scanner_status = get_scanner_status()
        
        if scanner_connected:
            st.success(f"🟢 Scanner Ready: {scanner_status}")
        else:
            st.warning(f"🟡 Demo Mode: {scanner_status}")
        
        st.info("""
        **Registration Process:**
        1. Place your finger on the scanner
        2. Hold steady until first scan completes
        3. Remove finger when prompted
        4. Place same finger again for verification
        5. Registration complete!
        """)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("🎯 Start Fingerprint Registration", use_container_width=True, type="primary"):
                with st.spinner("🔄 Starting fingerprint registration..."):
                    try:
                        success, message = biometric_auth.register_fingerprint(user_id)
                        
                        if success:
                            st.success(f"✅ {message}")
                            log_activity(user_id, "Successful fingerprint registration")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                            log_activity(user_id, f"Failed fingerprint registration: {message}")
                    except Exception as e:
                        st.error(f"❌ Registration error: {e}")
        
        with col2:
            st.markdown("**Registration Tips:**")
            st.markdown("• Use clean, dry finger")
            st.markdown("• Press with moderate pressure")
            st.markdown("• Use same finger for both scans")
            st.markdown("• Stay still during scanning")
            
    except Exception as e:
        st.error(f"Registration error: {e}")

def show_patient_dashboard():
    """Complete patient dashboard"""
    st.title("🏥 Patient Dashboard")
    st.write(f"Welcome, {st.session_state.user_id}!")
    
    # Load patient data
    try:
        patient_data = pd.read_csv("patient_data.csv")
        user_data = patient_data[patient_data["ID"] == st.session_state.user_id]
        
        if not user_data.empty:
            user_info = user_data.iloc[0]
            
            # Patient Information Section
            st.subheader("📋 Your Medical Information")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Name:** {user_info['Name']}")
                st.info(f"**Age:** {user_info['Age']}")
                st.info(f"**Gender:** {user_info['Gender']}")
                st.info(f"**Blood Group:** {user_info['BloodGroup']}")
            
            with col2:
                st.info(f"**Medical History:** {user_info['MedicalHistory']}")
                st.info(f"**Current Medications:** {user_info['Medications']}")
                st.info(f"**Allergies:** {user_info['Allergies']}")
                st.info(f"**Last Checkup:** {user_info['LastCheckup']}")
            
            # Doctor's Notes
            st.subheader("🩺 Latest Doctor's Notes")
            st.text_area("Notes", value=user_info['DoctorNotes'], disabled=True, height=100)
            
            # Appointments Section
            st.subheader("📅 Your Appointments")
            try:
                appointments = pd.read_csv("appointments.csv")
                user_appointments = appointments[appointments["PatientID"] == st.session_state.user_id]
                
                if not user_appointments.empty:
                    st.dataframe(user_appointments[["Date", "Time", "DoctorID", "Status", "Notes"]], use_container_width=True)
                else:
                    st.info("No upcoming appointments")
                    
            except FileNotFoundError:
                st.info("No appointment data available")
            
            # Medication History
            st.subheader("💊 Medication Information")
            with st.expander("Current Medications Details"):
                medications = user_info['Medications'].split(',') if user_info['Medications'] != 'None' else []
                if medications:
                    for med in medications:
                        st.write(f"• {med.strip()}")
                        st.caption("Take as prescribed by your doctor")
                else:
                    st.info("No current medications")
            
            # Health Metrics (Mock data)
            st.subheader("📊 Health Metrics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Blood Pressure", "120/80", delta="Normal")
            with col2:
                st.metric("Heart Rate", "72 bpm", delta="2 bpm")
            with col3:
                st.metric("Weight", "70 kg", delta="-1 kg")
            with col4:
                st.metric("BMI", "22.5", delta="Healthy")
                
        else:
            st.warning("⚠️ No medical records found for your account")
            
    except Exception as e:
        st.error(f"Error loading patient data: {e}")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📅 Book Appointment", use_container_width=True):
            st.info("📞 Please call UMID-MEDICAL to book an appointment")
    
    with col2:
        if st.button("💊 Prescription Refill", use_container_width=True):
            st.info("📋 Contact your pharmacy for prescription refills")
    
    with col3:
        if st.button("📧 Contact Doctor", use_container_width=True):
            st.info("✉️ Send message through patient portal")
    
    with col4:
        if st.button("📄 Download Records", use_container_width=True):
            st.info("📋 Medical records download feature coming soon")

    st.title("🤖 YOUR MEDICAL ASSISTANT")
    chat_bot()

def show_doctor_dashboard():
    """Complete doctor dashboard"""
    st.title("👨‍⚕️ Doctor Dashboard")
    st.write(f"Welcome, Dr. {st.session_state.user_id}!")
    
    # Load doctor data
    try:
        doctor_data = pd.read_csv("doctor_data.csv")
        user_data = doctor_data[doctor_data["ID"] == st.session_state.user_id]
        
        if not user_data.empty:
            user_info = user_data.iloc[0]
            st.subheader(f"👩‍⚕️ Dr. {user_info['Name']} - {user_info['Specialization']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Experience:** {user_info['Experience']}")
                st.info(f"**Email:** {user_info['Email']}")
            with col2:
                st.info(f"**Phone:** {user_info['Phone']}")
                st.info(f"**Department:** {user_info['Specialization']}")
    except Exception as e:
        st.error(f"Error loading doctor data: {e}")
    
    # Today's Schedule
    st.subheader("📅 Today's Schedule")
    try:
        appointments = pd.read_csv("appointments.csv")
        today_appointments = appointments[
            (appointments["DoctorID"] == st.session_state.user_id) & 
            (appointments["Date"] == str(datetime.date.today()))
        ]
        
        if not today_appointments.empty:
            st.dataframe(today_appointments[["Time", "PatientID", "Status", "Notes"]], use_container_width=True)
        else:
            st.info("No appointments scheduled for today")
            
    except FileNotFoundError:
        st.info("No appointment data available")
    
    # Patient Management
    st.subheader("👥 Patient Management")
    
    try:
        patient_data = pd.read_csv("patient_data.csv")
        
        tab1, tab2, tab3 = st.tabs(["View All Patients", "Update Patient Records", "Add New Patient"])
        
        with tab1:
            st.dataframe(patient_data, use_container_width=True)
            
            # Quick stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Patients", len(patient_data))
            with col2:
                st.metric("Male Patients", len(patient_data[patient_data["Gender"] == "Male"]))
            with col3:
                st.metric("Female Patients", len(patient_data[patient_data["Gender"] == "Female"]))
            with col4:
                avg_age = patient_data["Age"].mean()
                st.metric("Average Age", f"{avg_age:.1f}")
        
        with tab2:
            selected_patient = st.selectbox("Select Patient", patient_data["ID"].tolist())
            if selected_patient:
                patient_info = patient_data[patient_data["ID"] == selected_patient].iloc[0]
                
                st.write(f"**Updating records for:** {patient_info['Name']}")
                
                with st.form("update_patient"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_medications = st.text_input("Medications", value=patient_info["Medications"])
                        new_allergies = st.text_input("Allergies", value=patient_info["Allergies"])
                        new_checkup = st.date_input("Last Checkup", value=pd.to_datetime(patient_info["LastCheckup"]).date())
                    
                    with col2:
                        new_history = st.text_area("Medical History", value=patient_info["MedicalHistory"])
                        new_notes = st.text_area("Doctor Notes", value=patient_info["DoctorNotes"])
                    
                    if st.form_submit_button("💾 Update Record", use_container_width=True):
                        patient_data.loc[patient_data["ID"] == selected_patient, "Medications"] = new_medications
                        patient_data.loc[patient_data["ID"] == selected_patient, "Allergies"] = new_allergies
                        patient_data.loc[patient_data["ID"] == selected_patient, "MedicalHistory"] = new_history
                        patient_data.loc[patient_data["ID"] == selected_patient, "DoctorNotes"] = new_notes
                        patient_data.loc[patient_data["ID"] == selected_patient, "LastCheckup"] = str(new_checkup)
                        patient_data.to_csv("patient_data.csv", index=False)
                        log_activity(st.session_state.user_id, f"Updated patient record for {selected_patient}")
                        st.success("✅ Patient record updated successfully!")
                        st.rerun()
        
        with tab3:
            st.write("**Add New Patient to System**")
            
            with st.form("add_patient"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_id = st.text_input("Patient ID*")
                    new_name = st.text_input("Full Name*")
                    new_age = st.number_input("Age", min_value=1, max_value=120, value=30)
                    new_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                    new_blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
                
                with col2:
                    new_history = st.text_area("Medical History")
                    new_medications = st.text_input("Current Medications")
                    new_allergies = st.text_input("Known Allergies")
                    initial_notes = st.text_area("Initial Notes")
                
                if st.form_submit_button("➕ Add Patient", use_container_width=True):
                    if new_id and new_name:
                        if new_id not in patient_data["ID"].values:
                            new_row = {
                                "ID": new_id, "Name": new_name, "Age": new_age, "Gender": new_gender,
                                "BloodGroup": new_blood, "MedicalHistory": new_history,
                                "Medications": new_medications, "Allergies": new_allergies,
                                "LastCheckup": str(datetime.date.today()), "DoctorNotes": initial_notes
                            }
                            patient_data = pd.concat([patient_data, pd.DataFrame([new_row])], ignore_index=True)
                            patient_data.to_csv("patient_data.csv", index=False)
                            log_activity(st.session_state.user_id, f"Added new patient: {new_id}")
                            st.success("✅ New patient added successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Patient ID already exists")
                    else:
                        st.error("❌ Please fill in Patient ID and Name (marked with *)")

        st.title("🤖 YOUR ASSISTANT")
        chat_bot()

    except Exception as e:
        st.error(f"Error managing patient data: {e}")

def show_admin_dashboard():
    """Complete admin dashboard"""
    st.title("⚙️ Admin Dashboard")
    st.write(f"Welcome, Administrator {st.session_state.user_id}!")
    
    tab1, tab2, tab3, tab4, tab5 ,tab6= st.tabs(["System Overview", "User Management", "Activity Logs", "Biometric Setup", "System Settings", "Data Analytics ChatBot"])
    
    with tab1:
        st.subheader("📊 System Statistics")
        
        try:
            # Load data for statistics
            credentials_df = load_credentials()
            patient_data = pd.read_csv("patient_data.csv") if os.path.exists("patient_data.csv") else pd.DataFrame()
            doctor_data = pd.read_csv("doctor_data.csv") if os.path.exists("doctor_data.csv") else pd.DataFrame()
            appointments = pd.read_csv("appointments.csv") if os.path.exists("appointments.csv") else pd.DataFrame()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Users", len(credentials_df))
            with col2:
                st.metric("Patients", len(patient_data))
            with col3:
                st.metric("Doctors", len(doctor_data))
            with col4:
                st.metric("Appointments", len(appointments))
            
            # Additional metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Admins", len(credentials_df[credentials_df["category"] == "admin"]))
            with col2:
                st.metric("Pharmacy Staff", len(credentials_df[credentials_df["category"] == "pharmassist"]))
            with col3:
                today_appts = len(appointments[appointments["Date"] == str(datetime.date.today())]) if not appointments.empty else 0
                st.metric("Today's Appointments", today_appts)
            with col4:
                if BIOMETRIC_AVAILABLE:
                    try:
                        biometric_data = pd.read_csv("biometric_data.csv")
                        st.metric("Biometric Users", len(biometric_data))
                    except FileNotFoundError:
                        st.metric("Biometric Users", 0)
                else:
                    st.metric("Biometric Users", "N/A")
            
            # System health indicators
            st.subheader("🔍 System Health")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.success("🟢 Database Connection: Active")
            with col2:
                if BIOMETRIC_AVAILABLE:
                    st.success("🟢 Biometric System: Online")
                else:
                    st.warning("🟡 Biometric System: Offline")
            with col3:
                st.success("🟢 Authentication: Secure")
                
        except Exception as e:
            st.error(f"Error loading system statistics: {e}")
    
    with tab2:
        st.subheader("👥 User Management")
        
        try:
            credentials_df = load_credentials()
            
            # Display current users
            st.write("**Current System Users:**")
            display_df = credentials_df.copy()
            display_df["password"] = "***HIDDEN***"  # Hide passwords for security
            st.dataframe(display_df, use_container_width=True)
            
            # Add new user section
            st.subheader("➕ Add New User")
            
            with st.form("add_user"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_user_id = st.text_input("User ID*")
                    new_password = st.text_input("Password*", type="password")
                    new_category = st.selectbox("User Category", ["admin", "doctor", "user", "pharmassist"])
                
                with col2:
                    confirm_password = st.text_input("Confirm Password*", type="password")
                    st.write("**Categories:**")
                    st.caption("• admin: Full system access")
                    st.caption("• doctor: Medical records access")
                    st.caption("• user: Patient portal access")
                    st.caption("• pharmassist: Pharmacy management")
                
                if st.form_submit_button("➕ Add User", use_container_width=True):
                    if new_user_id and new_password and confirm_password:
                        if new_password == confirm_password:
                            if new_user_id not in credentials_df["ID"].values:
                                hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
                                new_row = pd.DataFrame({
                                    "ID": [new_user_id],
                                    "category": [new_category],
                                    "password": [hashed_password]
                                })
                                credentials_df = pd.concat([credentials_df, new_row], ignore_index=True)
                                credentials_df.to_csv("credentials.csv", index=False)
                                log_activity(st.session_state.user_id, f"Added new user: {new_user_id} ({new_category})")
                                st.success(f"✅ User {new_user_id} added successfully!")
                                st.rerun()
                            else:
                                st.error("❌ User ID already exists")
                        else:
                            st.error("❌ Passwords do not match")
                    else:
                        st.error("❌ Please fill in all required fields")
            
            # Delete user section
            st.subheader("🗑️ Remove User")
            user_to_delete = st.selectbox("Select User to Remove", 
                                        [uid for uid in credentials_df["ID"].values if uid != st.session_state.user_id])
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🗑️ Remove User", type="secondary"):
                    if user_to_delete:
                        credentials_df = credentials_df[credentials_df["ID"] != user_to_delete]
                        credentials_df.to_csv("credentials.csv", index=False)
                        log_activity(st.session_state.user_id, f"Removed user: {user_to_delete}")
                        st.success(f"✅ User {user_to_delete} removed successfully!")
                        st.rerun()
            with col2:
                st.caption("⚠️ You cannot remove your own account")
                
        except Exception as e:
            st.error(f"Error managing users: {e}")
    
    with tab3:
        st.subheader("📋 Activity Logs")
        
        try:
            # Read log file
            if os.path.exists("log.txt"):
                with open("log.txt", "r", encoding='utf-8') as log_file:
                    logs = log_file.readlines()
                
                if logs:
                    # Display recent logs
                    st.write(f"**Recent Activities ({len(logs)} total entries):**")
                    
                    # Show last 20 entries
                    recent_logs = logs[-20:] if len(logs) > 20 else logs
                    
                    for log_entry in reversed(recent_logs):
                        log_entry = log_entry.strip()
                        if log_entry:
                            # Parse log entry
                            parts = log_entry.split(" - ")
                            if len(parts) >= 2:
                                timestamp = parts[0]
                                activity = " - ".join(parts[1:])
                                st.text(f"{timestamp} | {activity}")
                    
                    # Clear logs option
                    st.subheader("🧹 Log Management")
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        if st.button("🗑️ Clear All Logs", type="secondary"):
                            with open("log.txt", "w", encoding='utf-8') as log_file:
                                log_file.write("")
                            log_activity(st.session_state.user_id, "Cleared all system logs")
                            st.success("✅ All logs cleared!")
                            st.rerun()
                    
                    with col2:
                        st.caption("⚠️ This action cannot be undone")
                        
                else:
                    st.info("No activity logs found")
            else:
                st.info("Log file not found")
                
        except Exception as e:
            st.error(f"Error reading logs: {e}")
    
    with tab4:
        st.subheader("👆 Biometric System Setup")
        
        if BIOMETRIC_AVAILABLE:
            try:
                # Scanner status
                scanner_connected, scanner_status = get_scanner_status()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if scanner_connected:
                        st.success(f"🟢 Scanner Status: {scanner_status}")
                    else:
                        st.warning(f"🟡 Scanner Status: {scanner_status}")
                
                with col2:
                    st.info("ℹ️ System running in demo mode for testing")
                
                # Biometric users overview
                st.subheader("📊 Biometric Users Overview")
                
                try:
                    biometric_data = pd.read_csv("biometric_data.csv")
                    if not biometric_data.empty:
                        st.write(f"**Registered Users:** {len(biometric_data)}")
                        
                        # Display biometric user data (without sensitive info)
                        display_biometric = biometric_data[["user_id", "registration_date", "last_used"]].copy()
                        st.dataframe(display_biometric, use_container_width=True)
                        
                        # Bulk operations
                        st.subheader("🔧 Bulk Operations")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("🔄 Reset All Biometric Data", type="secondary"):
                                # Clear biometric data file
                                empty_df = pd.DataFrame(columns=["user_id", "fingerprint_data", "registration_date", "last_used", "quality_score"])
                                empty_df.to_csv("biometric_data.csv", index=False)
                                log_activity(st.session_state.user_id, "Reset all biometric data")
                                st.success("✅ All biometric data cleared!")
                                st.rerun()
                        
                        with col2:
                            st.caption("⚠️ This will remove all fingerprint registrations")
                            
                    else:
                        st.info("No biometric users registered yet")
                        
                except FileNotFoundError:
                    st.info("No biometric data file found")
                    
                    # Initialize biometric system
                    if st.button("🚀 Initialize Biometric System"):
                        try:
                            success, message = setup_scanner_demo_data()
                            if success:
                                st.success(f"✅ {message}")
                                log_activity(st.session_state.user_id, "Initialized biometric system")
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        except Exception as e:
                            st.error(f"Initialization error: {e}")
                
                # System configuration
                st.subheader("⚙️ Biometric Configuration")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Security Settings:**")
                    security_level = st.selectbox("Security Level", ["Standard", "High", "Maximum"])
                    require_pin = st.checkbox("Require PIN with Fingerprint")
                    max_attempts = st.number_input("Max Failed Attempts", min_value=1, max_value=10, value=3)
                
                with col2:
                    st.write("**Performance Settings:**")
                    scan_timeout = st.number_input("Scan Timeout (seconds)", min_value=5, max_value=30, value=10)
                    quality_threshold = st.slider("Quality Threshold", min_value=0.5, max_value=1.0, value=0.8, step=0.1)
                    enable_logging = st.checkbox("Enable Detailed Logging", value=True)
                
                if st.button("💾 Save Configuration"):
                    # Save configuration (in real implementation, this would save to config file)
                    config = {
                        "security_level": security_level,
                        "require_pin": require_pin,
                        "max_attempts": max_attempts,
                        "scan_timeout": scan_timeout,
                        "quality_threshold": quality_threshold,
                        "enable_logging": enable_logging
                    }
                    log_activity(st.session_state.user_id, f"Updated biometric configuration: {config}")
                    st.success("✅ Configuration saved!")
                    
            except Exception as e:
                st.error(f"Biometric system error: {e}")
        else:
            st.warning("⚠️ Biometric authentication system is not available")
            st.info("To enable biometric features, install the required biometric_auth module")
    
    with tab5:
        st.subheader("🔧 System Settings")
        
        # System maintenance
        st.write("**System Maintenance:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Data Files"):
                create_required_files()
                st.success("✅ Data files refreshed!")
        
        with col2:
            if st.button("📊 Generate Reports"):
                st.info("📋 Report generation feature coming soon")
        
        with col3:
            if st.button("🔐 Security Audit"):
                st.info("🔍 Security audit feature coming soon")
        
        # Database management
        st.subheader("🗄️ Database Management")
        
        file_status = {
            "credentials.csv": os.path.exists("credentials.csv"),
            "patient_data.csv": os.path.exists("patient_data.csv"),
            "doctor_data.csv": os.path.exists("doctor_data.csv"),
            "appointments.csv": os.path.exists("appointments.csv"),
            "inventory.csv": os.path.exists("inventory.csv"),
            "biometric_data.csv": os.path.exists("biometric_data.csv"),
            "log.txt": os.path.exists("log.txt")
        }
        
        st.write("**File Status:**")
        for filename, exists in file_status.items():
            status = "✅ Exists" if exists else "❌ Missing"
            st.write(f"• {filename}: {status}")
        
        # System information
        st.subheader("ℹ️ System Information")
        
        system_info = {
            "Application Version": "2.0.0",
            "Python Version": "3.8+",
            "Streamlit Version": st.__version__,
            "Biometric Support": "Enabled" if BIOMETRIC_AVAILABLE else "Disabled",
            "Database Type": "CSV Files",
            "Security": "SHA-256 Hashing"
        }
        
        for key, value in system_info.items():
            st.write(f"**{key}:** {value}")

    with tab6:
        st.title("🤖 Chatbot")
        chat_bot()

def show_pharmacy_dashboard():
    """Complete pharmacy assistant dashboard"""
    st.title("💊 Pharmacy Dashboard")
    st.write(f"Welcome, {st.session_state.user_id}!")
    
    try:
        inventory_data = pd.read_csv("inventory.csv")

        tab1, tab2, tab3, tab4 ,tab5 = st.tabs(["Inventory Overview", "Stock Management", "Add Medication", "Reports", "PHARMA ASSISTANT"])

        with tab1:
            st.subheader("📦 Current Inventory")
            
            # Quick stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Medications", len(inventory_data))
            with col2:
                total_stock = inventory_data["Stock"].sum()
                st.metric("Total Stock Units", total_stock)
            with col3:
                low_stock = len(inventory_data[inventory_data["Stock"] <= inventory_data["MinStock"]])
                st.metric("Low Stock Items", low_stock, delta="Critical" if low_stock > 0 else "Good")
            with col4:
                total_value = (inventory_data["Stock"] * inventory_data["Price"]).sum()
                st.metric("Inventory Value", f"${total_value:,.2f}")
            
            # Display inventory
            st.dataframe(inventory_data, use_container_width=True)
            
            # Low stock alerts
            low_stock_items = inventory_data[inventory_data["Stock"] <= inventory_data["MinStock"]]
            if not low_stock_items.empty:
                st.subheader("⚠️ Low Stock Alerts")
                st.dataframe(low_stock_items[["Name", "Stock", "MinStock", "Supplier"]], use_container_width=True)
            
            # Expiry alerts (within 30 days)
            today = datetime.date.today()
            inventory_data["ExpiryDate"] = pd.to_datetime(inventory_data["ExpiryDate"])
            expiring_soon = inventory_data[
                (inventory_data["ExpiryDate"] - pd.Timestamp(today)).dt.days <= 30
            ]
            
            if not expiring_soon.empty:
                st.subheader("📅 Expiring Soon (Within 30 Days)")
                st.dataframe(expiring_soon[["Name", "Stock", "ExpiryDate", "Supplier"]], use_container_width=True)
        
        with tab2:
            st.subheader("📋 Stock Management")
            
            # Update stock levels
            selected_med = st.selectbox("Select Medication", inventory_data["Name"].tolist())
            
            if selected_med:
                med_info = inventory_data[inventory_data["Name"] == selected_med].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Current Stock:** {med_info['Stock']}")
                    st.write(f"**Minimum Stock:** {med_info['MinStock']}")
                    st.write(f"**Price:** ${med_info['Price']}")
                
                with col2:
                    st.write(f"**Expiry Date:** {med_info['ExpiryDate']}")
                    st.write(f"**Supplier:** {med_info['Supplier']}")
                
                # Stock adjustment
                st.subheader("📊 Adjust Stock")
                
                with st.form("adjust_stock"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        adjustment_type = st.radio("Adjustment Type", ["Add Stock", "Remove Stock", "Set Stock"])
                        adjustment_amount = st.number_input("Amount", min_value=0, value=0)
                    
                    with col2:
                        reason = st.text_area("Reason for Adjustment")
                        st.write("**Common Reasons:**")
                        st.caption("• New delivery received")
                        st.caption("• Medication dispensed")
                        st.caption("• Expired stock removed")
                        st.caption("• Inventory correction")
                    
                    if st.form_submit_button("💾 Update Stock"):
                        current_stock = med_info['Stock']
                        
                        if adjustment_type == "Add Stock":
                            new_stock = current_stock + adjustment_amount
                        elif adjustment_type == "Remove Stock":
                            new_stock = max(0, current_stock - adjustment_amount)
                        else:  # Set Stock
                            new_stock = adjustment_amount
                        
                        # Update inventory
                        inventory_data.loc[inventory_data["Name"] == selected_med, "Stock"] = new_stock
                        inventory_data.to_csv("inventory.csv", index=False)
                        
                        log_activity(st.session_state.user_id, 
                                   f"Stock adjustment for {selected_med}: {current_stock} → {new_stock} ({reason})")
                        
                        st.success(f"✅ Stock updated! {selected_med}: {current_stock} → {new_stock}")
                        st.rerun()
        
        with tab3:
            st.subheader("➕ Add New Medication")
            
            with st.form("add_medication"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_med_id = st.text_input("Medication ID*")
                    new_med_name = st.text_input("Medication Name*")
                    new_stock = st.number_input("Initial Stock", min_value=0, value=0)
                    new_min_stock = st.number_input("Minimum Stock Level", min_value=0, value=10)
                
                with col2:
                    new_price = st.number_input("Price per Unit ($)", min_value=0.0, value=0.0, step=0.01)
                    new_expiry = st.date_input("Expiry Date", value=datetime.date.today() + datetime.timedelta(days=365))
                    new_supplier = st.text_input("Supplier")
                
                if st.form_submit_button("➕ Add Medication", use_container_width=True):
                    if new_med_id and new_med_name:
                        if new_med_id not in inventory_data["MedicationID"].values:
                            new_row = pd.DataFrame({
                                "MedicationID": [new_med_id],
                                "Name": [new_med_name],
                                "Stock": [new_stock],
                                "MinStock": [new_min_stock],
                                "Price": [new_price],
                                "ExpiryDate": [str(new_expiry)],
                                "Supplier": [new_supplier]
                            })
                            inventory_data = pd.concat([inventory_data, new_row], ignore_index=True)
                            inventory_data.to_csv("inventory.csv", index=False)
                            
                            log_activity(st.session_state.user_id, f"Added new medication: {new_med_name} ({new_med_id})")
                            st.success(f"✅ Medication {new_med_name} added successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Medication ID already exists")
                    else:
                        st.error("❌ Please fill in Medication ID and Name")
        
        with tab4:
            st.subheader("📊 Pharmacy Reports")
            
            # Sales summary (mock data)
            st.subheader("💰 Sales Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Today's Sales", "$1,250.00", delta="12%")
            with col2:
                st.metric("This Week", "$8,750.00", delta="8%")
            with col3:
                st.metric("This Month", "$35,200.00", delta="15%")
            
            # Top medications
            st.subheader("🏆 Top Medications by Value")
            inventory_data["Total_Value"] = inventory_data["Stock"] * inventory_data["Price"]
            top_meds = inventory_data.nlargest(5, "Total_Value")[["Name", "Stock", "Price", "Total_Value"]]
            st.dataframe(top_meds, use_container_width=True)
            
            # Generate reports
            st.subheader("📋 Generate Reports")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Inventory Report", use_container_width=True):
                    st.info("📄 Inventory report generated (feature coming soon)")
            
            with col2:
                if st.button("💊 Dispensing Report", use_container_width=True):
                    st.info("📄 Dispensing report generated (feature coming soon)")

        with tab5:
            st.subheader("🤖 Pharmacy Chatbot")
            chat_bot()
                        
    except FileNotFoundError:
        st.error("❌ Inventory data not found. Creating default inventory...")
        create_required_files()
        st.rerun()
    except Exception as e:
        st.error(f"Error loading pharmacy data: {e}")

def main():
    """Main application function"""
    st.set_page_config(
        page_title="UMID - Medical Information System",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "user_category" not in st.session_state:
        st.session_state.user_category = None
    if "login_method" not in st.session_state:
        st.session_state.login_method = None
    
    # Create required files on startup
    create_required_files()
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1e3a8a 0%, #3730a3 100%); padding: 1rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; text-align: center; margin: 0;">
            🏥 UMID - UNIVERSAL MEDICAL IDENTITY
        </h1>
        <p style="color: #e0e7ff; text-align: center; margin: 0;">
            Secure Medical Records Management with Biometric Authentication
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main application logic
    if not st.session_state.logged_in:
        # Login page
        credentials_df = load_credentials()

        # Login tabs
        tab1, tab2, tab3 = st.tabs(["🔑 Credential Login", "👆 Fingerprint Login", "🤖 GENERAL Q&A"])
        
        with tab1:
            show_traditional_login(credentials_df)
        
        with tab2:
            show_fingerprint_login(credentials_df)
        
        with tab3:
            st.title("🤖 GENERAL HEALTHCARE ASSISTANT")
            chat_bot()
    
    else:
        # Logged in - show appropriate dashboard
        
        # Sidebar with user info and logout
        with st.sidebar:
            st.success(f"✅ Logged in as: **{st.session_state.user_id}**")
            st.info(f"👤 Role: **{st.session_state.user_category.title()}**")
            st.info(f"🔐 Method: **{st.session_state.login_method.title()}**")
            
            if st.button("🚪 Logout", use_container_width=True):
                log_activity(st.session_state.user_id, "Logged out")
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.user_category = None
                st.session_state.login_method = None
                st.rerun()
            
            st.markdown("---")
            st.markdown("### 🔧 Quick Actions")
            
            if st.session_state.user_category in ["admin", "doctor", "user"]:
                if st.button("👆 Manage Fingerprint", use_container_width=True):
                    st.session_state.show_biometric_reg = True
            
            st.markdown("---")
            st.markdown("### ℹ️ System Status")
            st.success("🟢 System Online")
            if BIOMETRIC_AVAILABLE:
                st.success("🟢 Biometric Ready")
            else:
                st.warning("🟡 Biometric Offline")
        
        # Show fingerprint registration if requested
        if st.session_state.get('show_biometric_reg', False):
            show_fingerprint_registration()
            if st.button("← Back to Dashboard"):
                st.session_state.show_biometric_reg = False
                st.rerun()
        else:
            # Show appropriate dashboard based on user category
            if st.session_state.user_category == "admin":
                show_admin_dashboard()
            elif st.session_state.user_category == "doctor":
                show_doctor_dashboard()
            elif st.session_state.user_category == "user":
                show_patient_dashboard()
            elif st.session_state.user_category == "pharmassist":
                show_pharmacy_dashboard()
            else:
                st.error("❌ Unknown user category")

if __name__ == "__main__":
    main()
