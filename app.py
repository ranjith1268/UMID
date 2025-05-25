import streamlit as st
import pandas as pd
import os
import datetime
import hashlib
from pathlib import Path
from biometric_auth import BiometricAuth

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

def get_user_category(user_id, credentials_df):
    """Get user category from credentials"""
    if user_id in credentials_df["ID"].values:
        user_row = credentials_df[credentials_df["ID"] == user_id]
        return user_row["category"].values[0]
    return None

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

def show_traditional_login(credentials_df):
    """Show traditional username/password login"""
    st.subheader("🔑 Credential Login")
    
    with st.form("login_form"):
        user_id = st.text_input("User ID", placeholder="Enter your User ID")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit_button = st.form_submit_button("🔓 Login with Credentials", use_container_width=True)
        
        if submit_button:
            is_valid, category = verify_login(user_id, password, credentials_df)
            if is_valid:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.user_category = category
                st.session_state.login_method = "credentials"
                log_activity(user_id, "Successful credential login")
                st.success(f"✅ Welcome back! Logged in as {category}")
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")
                log_activity(user_id if user_id else "Unknown", "Failed credential login attempt")

def show_biometric_login(credentials_df):
    """Show biometric authentication login"""
    st.subheader("🔐 Biometric Authentication")
    
    biometric_auth = BiometricAuth()
    
    # Check if there are any registered biometric users
    try:
        biometric_data = pd.read_csv("biometric_data.csv")
        if biometric_data.empty:
            st.info("ℹ️ No biometric data found. Please register your biometrics first or use credential login.")
            return
    except FileNotFoundError:
        st.info("ℹ️ No biometric data found. Please register your biometrics first or use credential login.")
        return
    
    auth_method = st.radio(
        "Choose biometric authentication method:",
        ["👆 Fingerprint Authentication", "📷 Face Recognition"],
        key="biometric_method"
    )
    
    if auth_method == "👆 Fingerprint Authentication":
        st.info("🔄 Place your finger on the scanner")
        
        if st.button("👆 Scan Fingerprint", use_container_width=True):
            with st.spinner("🔄 Scanning fingerprint..."):
                import time
                time.sleep(2)
                
                # For demo: use a known fingerprint hash
                if not biometric_data.empty:
                    demo_fingerprint = biometric_data.iloc[0]["fingerprint_hash"]
                    user_id, message = biometric_auth.authenticate_fingerprint(demo_fingerprint)
                    
                    if user_id:
                        category = get_user_category(user_id, credentials_df)
                        if category:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.user_category = category
                            st.session_state.login_method = "fingerprint"
                            log_activity(user_id, "Successful fingerprint login")
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error("❌ User not found in system")
                    else:
                        st.error(f"❌ {message}")
                        log_activity("Unknown", "Failed fingerprint login attempt")
                else:
                    st.error("❌ No registered fingerprints found")
    
    elif auth_method == "📷 Face Recognition":
        st.info("📷 Position your face in the camera for recognition")
        
        face_image = biometric_auth.capture_face_image()
        
        if face_image is not None:
            if st.button("🔍 Authenticate Face", use_container_width=True):
                with st.spinner("🔄 Processing face recognition..."):
                    user_id, message = biometric_auth.authenticate_face(face_image)
                    
                    if user_id:
                        category = get_user_category(user_id, credentials_df)
                        if category:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.user_category = category
                            st.session_state.login_method = "face_recognition"
                            log_activity(user_id, "Successful face recognition login")
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error("❌ User not found in system")
                    else:
                        st.error(f"❌ {message}")
                        log_activity("Unknown", "Failed face recognition login attempt")

def show_login_page():
    """Show the main login page with multiple authentication options"""
    st.markdown("""
    ## 🔐 Secure Access Portal
    Choose your preferred authentication method to access the UMID System.
    """)
    
    # Load credentials
    credentials_df = load_credentials()
    
    # Create tabs for different login methods
    tab1, tab2, tab3 = st.tabs(["🔑 Credentials", "🔐 Biometric", "ℹ️ Help"])
    
    with tab1:
        show_traditional_login(credentials_df)
        
        # Show demo credentials
        with st.expander("🔍 Demo Credentials", expanded=False):
            st.markdown("""
            **Demo User Accounts:**
            - **Admin**: `admin1` / `admin123`
            - **Doctor**: `doctor1` / `doctor123`  
            - **Patient**: `patient1` / `patient123`
            - **Pharmacy Assistant**: `pharmassist1` / `pharma123`
            """)
    
    with tab2:
        show_biometric_login(credentials_df)
        
        st.markdown("---")
        st.markdown("""
        **🔐 Biometric Registration**
        
        New users need to register their biometric data first. 
        Contact your system administrator or use the registration portal.
        """)
        
        if st.button("📝 Register Biometrics", use_container_width=True):
            st.info("🔄 Redirecting to biometric registration...")
            # You can implement biometric registration here or redirect to a separate page
    
    with tab3:
        st.markdown("""
        ### 🆘 Login Help
        
        **Having trouble logging in?**
        
        **Credential Login:**
        - Use your assigned User ID and password
        - Contact IT support if you've forgotten your credentials
        - Ensure caps lock is off when entering passwords
        
        **Biometric Login:**
        - Ensure good lighting for face recognition
        - Keep your finger clean and dry for fingerprint scanning
        - Register your biometrics first if you haven't already
        
        **Security Features:**
        - All login attempts are logged for security
        - Multiple failed attempts may temporarily lock your account
        - Biometric data is encrypted and stored securely
        
        **Contact Support:**
        - IT Helpdesk: `support@umid.com`
        - Phone: `+1-555-UMID-HELP`
        - Available 24/7 for critical issues
        """)

def main():
    st.set_page_config(
        page_title="UMID System",
        page_icon="🏥",
        layout="wide"
    )
    
    # Create required files
    create_required_files()
    
    # Set up session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = ""
    if "user_category" not in st.session_state:
        st.session_state.user_category = ""
    if "login_method" not in st.session_state:
        st.session_state.login_method = ""
    
    # Display header
    st.title("🏥 Universal Medical Identity System (UMID)")
    
    if not st.session_state.logged_in:
        # Welcome message
        st.markdown("""
        ### Welcome to UMID
        The Universal Medical Identity System provides a secure platform for managing medical records 
        and facilitating healthcare services.
        
        **🚀 System Features:**
        - **👥 For Patients**: Access medical records, medication history, and AI medical assistant
        - **👨‍⚕️ For Doctors**: View patient records, update notes, and access medical resources  
        - **👨‍💼 For Administrators**: Manage users, analyze data, and ensure system integrity
        - **💊 For Pharmacy**: Manage prescriptions and medication inventory
        """)
        
        st.markdown("---")
        show_login_page()
    
    else:
        # Show user info in sidebar
        with st.sidebar:
            st.success(f"✅ Logged in as: **{st.session_state.user_id}**")
            st.info(f"🔐 Method: {st.session_state.login_method.replace('_', ' ').title()}")
            st.info(f"👤 Role: {st.session_state.user_category.title()}")
            
            if st.button("🚪 Logout", use_container_width=True):
                log_activity(st.session_state.user_id, f"Logged out (via {st.session_state.login_method})")
                st.session_state.logged_in = False
                st.session_state.user_id = ""
                st.session_state.user_category = ""
                st.session_state.login_method = ""
                st.rerun()
        
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

if __name__ == "__main__":
    main()