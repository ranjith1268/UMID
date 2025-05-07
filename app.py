import streamlit as st
import pandas as pd
import os
import datetime
import hashlib
from pathlib import Path

def log_activity(user_id, action):
    """Log user activities to log file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a") as log_file:
        log_file.write(f"{timestamp} - User {user_id}: {action}\n")

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
    if user_id in credentials_df["ID"].values:
        user_row = credentials_df[credentials_df["ID"] == user_id]
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if user_row["password"].values[0] == hashed_password:
            return True, user_row["category"].values[0]
    return False, None

def create_required_files():
    """Create required CSV files if they don't exist"""
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
        patient_data.loc[0] = [
            "patient1", "John Doe", 35, "Male", "O+", 
            "Hypertension", "Lisinopril", "None", 
            "2024-12-15", "Regular checkup; BP slightly elevated"
        ]
        patient_data.to_csv("patient_data.csv", index=False)
    
    # Create doctor_data.csv
    if not os.path.exists("doctor_data.csv"):
        doctor_data = pd.DataFrame(columns=[
            "ID", "Name", "Specialization", "Experience", "Email", "Phone"
        ])
        doctor_data.loc[0] = [
            "doctor1", "Dr. Jane Smith", "Cardiologist", "15 years", 
            "dr.jane@umid.com", "+1-555-123-4567"
        ]
        doctor_data.to_csv("doctor_data.csv", index=False)
    
    # Create log file
    log_file = Path("log.txt")
    if not log_file.exists():
        log_file.touch()

def main():
    st.set_page_config(
        page_title="UMID System",
        page_icon="🏥",
        layout="wide"
    )
    
    # Create required files
    create_required_files()
    
    # Load credentials
    credentials_df = load_credentials()
    
    # Set up session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = ""
    if "user_category" not in st.session_state:
        st.session_state.user_category = ""
    
    # Display header
    st.title("🏥 Universal Medical Identity System (UMID)")
    
    if not st.session_state.logged_in:
        st.markdown("""
        ## Welcome to UMID
        The Universal Medical Identity System provides a secure platform for managing medical records 
        and facilitating healthcare services. Please login to access your personalized dashboard.
        
        ### Features:
        - **For Patients**: Access your medical records, medication history, and chat with our medical bot
        - **For Doctors**: View patient records, update medical notes, and access advanced medical resources
        - **For Administrators**: Manage system users, analyze healthcare data, and ensure system integrity
        """)
        
        # Login form
        with st.form("login_form"):
            user_id = st.text_input("User ID")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                is_valid, category = verify_login(user_id, password, credentials_df)
                if is_valid:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.user_category = category
                    log_activity(user_id, "Successful login")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
                    log_activity(user_id if user_id else "Unknown", "Failed login attempt")
    
    else:
        # Handle redirection based on user category
        if st.session_state.user_category == "user":
            import patient
            patient.show_patient_page(st.session_state.user_id)
        elif st.session_state.user_category == "doctor":
            import doctor
            doctor.show_doctor_page(st.session_state.user_id)
        elif st.session_state.user_category == "admin":
            import admin
            admin.show_admin_page()
        elif st.session_state.user_category == "pharmassist":
            import pharmassist
            pharmassist.show_pharmassist_page(st.session_state.user_id)
    
        if st.sidebar.button("Logout"):
            log_activity(st.session_state.user_id, "Logged out")
            st.session_state.logged_in = False
            st.session_state.user_id = ""
            st.session_state.user_category = ""
            st.rerun()

if __name__ == "__main__":
    main()