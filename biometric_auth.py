# biometric_auth.py
import streamlit as st
import cv2
import numpy as np
import pandas as pd
import base64
import os
import hashlib
import datetime
from pathlib import Path
import face_recognition
import pickle
from PIL import Image
import io

class BiometricAuth:
    def __init__(self):
        self.face_encodings_file = "face_encodings.pkl"
        self.biometric_data_file = "biometric_data.csv"
        self.ensure_biometric_files()
    
    def ensure_biometric_files(self):
        """Create biometric data files if they don't exist"""
        if not os.path.exists(self.biometric_data_file):
            biometric_df = pd.DataFrame(columns=[
                "ID", "face_encoding", "fingerprint_hash", "registration_date"
            ])
            biometric_df.to_csv(self.biometric_data_file, index=False)
        
        if not os.path.exists(self.face_encodings_file):
            with open(self.face_encodings_file, 'wb') as f:
                pickle.dump({}, f)
    
    def capture_face_image(self):
        """Capture face image using webcam"""
        st.subheader("📷 Face Recognition Setup")
        
        # Option 1: Use webcam
        if st.button("📸 Capture Face Image"):
            # Create a placeholder for the camera feed
            camera_placeholder = st.empty()
            
            # Initialize webcam
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                st.error("❌ Could not access webcam")
                return None
            
            st.info("📹 Position your face in the camera and press 'c' to capture, 'q' to quit")
            
            # Create buttons for capture control
            col1, col2 = st.columns(2)
            with col1:
                capture_btn = st.button("📷 Capture")
            with col2:
                stop_btn = st.button("⏹️ Stop Camera")
            
            captured_image = None
            
            # Camera loop
            while True:
                ret, frame = cap.read()
                if not ret:
                    st.error("❌ Failed to capture image")
                    break
                
                # Convert BGR to RGB for display
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Display the frame
                camera_placeholder.image(rgb_frame, channels="RGB", use_column_width=True)
                
                # Check for capture or stop
                if capture_btn or cv2.waitKey(1) & 0xFF == ord('c'):
                    captured_image = rgb_frame
                    break
                
                if stop_btn or cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
            if captured_image is not None:
                st.success("✅ Face image captured successfully!")
                st.image(captured_image, caption="Captured Face Image", use_column_width=True)
                return captured_image
        
        # Option 2: Upload image file
        st.write("**Or upload a face image:**")
        uploaded_file = st.file_uploader(
            "Choose a face image", 
            type=['jpg', 'jpeg', 'png'],
            help="Upload a clear front-facing photo"
        )
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            image_array = np.array(image)
            st.image(image, caption="Uploaded Face Image", use_column_width=True)
            return image_array
        
        return None
    
    def capture_fingerprint_simulation(self):
        """Simulate fingerprint capture (for demo purposes)"""
        st.subheader("👆 Fingerprint Registration")
        st.info("🔄 In a real implementation, this would interface with a fingerprint scanner")
        
        # Simulate fingerprint patterns
        fingerprint_patterns = [
            "WHORL_PATTERN_A1B2C3",
            "LOOP_PATTERN_D4E5F6", 
            "ARCH_PATTERN_G7H8I9",
            "COMPOSITE_PATTERN_J1K2L3"
        ]
        
        if st.button("👆 Simulate Fingerprint Capture"):
            with st.spinner("🔄 Scanning fingerprint..."):
                import time
                time.sleep(2)  # Simulate scanning time
                
                # Generate a unique fingerprint hash based on user info and timestamp
                timestamp = str(datetime.datetime.now().timestamp())
                fingerprint_data = f"{timestamp}_{np.random.choice(fingerprint_patterns)}"
                fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
                
                st.success("✅ Fingerprint captured successfully!")
                st.code(f"Fingerprint ID: {fingerprint_hash[:16]}...")
                
                return fingerprint_hash
        
        return None
    
    def encode_face(self, image):
        """Generate face encoding from image"""
        try:
            # Find faces in the image
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) == 0:
                st.error("❌ No face detected in the image. Please try again with a clearer image.")
                return None
            
            if len(face_locations) > 1:
                st.warning("⚠️ Multiple faces detected. Using the first detected face.")
            
            # Generate face encoding
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if len(face_encodings) > 0:
                return face_encodings[0]
            else:
                st.error("❌ Could not generate face encoding. Please try again.")
                return None
                
        except Exception as e:
            st.error(f"❌ Error processing face image: {str(e)}")
            return None
    
    def register_biometric_data(self, user_id, face_image=None, fingerprint_hash=None):
        """Register biometric data for a user"""
        biometric_data = pd.read_csv(self.biometric_data_file)
        
        # Check if user already has biometric data
        if user_id in biometric_data["ID"].values:
            st.warning("⚠️ Biometric data already exists for this user. Updating...")
            biometric_data = biometric_data[biometric_data["ID"] != user_id]
        
        face_encoding_str = None
        if face_image is not None:
            face_encoding = self.encode_face(face_image)
            if face_encoding is not None:
                # Convert face encoding to string for storage
                face_encoding_str = base64.b64encode(face_encoding.tobytes()).decode('utf-8')
                
                # Store in face encodings file
                face_encodings = {}
                try:
                    with open(self.face_encodings_file, 'rb') as f:
                        face_encodings = pickle.load(f)
                except:
                    pass
                
                face_encodings[user_id] = face_encoding
                
                with open(self.face_encodings_file, 'wb') as f:
                    pickle.dump(face_encodings, f)
        
        # Add new biometric record
        new_record = pd.DataFrame({
            "ID": [user_id],
            "face_encoding": [face_encoding_str],
            "fingerprint_hash": [fingerprint_hash],
            "registration_date": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        
        biometric_data = pd.concat([biometric_data, new_record], ignore_index=True)
        biometric_data.to_csv(self.biometric_data_file, index=False)
        
        return True
    
    def authenticate_face(self, image):
        """Authenticate user using face recognition"""
        try:
            # Load stored face encodings
            with open(self.face_encodings_file, 'rb') as f:
                stored_encodings = pickle.load(f)
            
            if not stored_encodings:
                return None, "No registered faces found"
            
            # Get face encoding from input image
            face_encoding = self.encode_face(image)
            if face_encoding is None:
                return None, "Could not detect face in image"
            
            # Compare with stored encodings
            for user_id, stored_encoding in stored_encodings.items():
                matches = face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.6)
                
                if matches[0]:
                    # Calculate face distance for confidence
                    distance = face_recognition.face_distance([stored_encoding], face_encoding)[0]
                    confidence = (1 - distance) * 100
                    
                    return user_id, f"Face match found with {confidence:.1f}% confidence"
            
            return None, "No matching face found"
            
        except Exception as e:
            return None, f"Authentication error: {str(e)}"
    
    def authenticate_fingerprint(self, fingerprint_hash):
        """Authenticate user using fingerprint"""
        try:
            biometric_data = pd.read_csv(self.biometric_data_file)
            
            matching_users = biometric_data[biometric_data["fingerprint_hash"] == fingerprint_hash]
            
            if not matching_users.empty:
                user_id = matching_users.iloc[0]["ID"]
                return user_id, "Fingerprint match found"
            else:
                return None, "No matching fingerprint found"
                
        except Exception as e:
            return None, f"Fingerprint authentication error: {str(e)}"
    
    def biometric_login_interface(self):
        """Create biometric login interface"""
        st.subheader("🔐 Biometric Authentication")
        
        auth_method = st.radio(
            "Choose authentication method:",
            ["👆 Fingerprint", "📷 Face Recognition"]
        )
        
        if auth_method == "👆 Fingerprint":
            st.info("🔄 Place your finger on the scanner")
            
            if st.button("👆 Scan Fingerprint"):
                # Simulate fingerprint scan
                with st.spinner("🔄 Scanning fingerprint..."):
                    import time
                    time.sleep(2)
                    
                    # For demo: use a known fingerprint hash
                    # In real implementation, this would come from the scanner
                    biometric_data = pd.read_csv(self.biometric_data_file)
                    if not biometric_data.empty:
                        # Use the first registered fingerprint for demo
                        demo_fingerprint = biometric_data.iloc[0]["fingerprint_hash"]
                        user_id, message = self.authenticate_fingerprint(demo_fingerprint)
                        
                        if user_id:
                            st.success(f"✅ {message}")
                            return user_id
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ No registered fingerprints found")
        
        elif auth_method == "📷 Face Recognition":
            st.info("📷 Look at the camera for face recognition")
            
            face_image = self.capture_face_image()
            
            if face_image is not None:
                if st.button("🔍 Authenticate Face"):
                    with st.spinner("🔄 Processing face recognition..."):
                        user_id, message = self.authenticate_face(face_image)
                        
                        if user_id:
                            st.success(f"✅ {message}")
                            return user_id
                        else:
                            st.error(f"❌ {message}")
        
        return None
    
    def display_user_records(self, user_id):
        """Display patient records for authenticated user"""
        try:
            patient_data = pd.read_csv("patient_data.csv")
            user_data = patient_data[patient_data["ID"] == user_id]
            
            if not user_data.empty:
                user_info = user_data.iloc[0]
                
                st.success(f"🎉 Welcome back, {user_info['Name']}!")
                
                # Display patient information
                with st.expander("📋 Your Medical Records", expanded=True):
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
                    
                    st.subheader("Doctor's Notes")
                    st.write(user_info['DoctorNotes'])
                
                return True
            else:
                st.warning(f"⚠️ No medical records found for user: {user_id}")
                return False
                
        except Exception as e:
            st.error(f"❌ Error loading records: {str(e)}")
            return False

# Usage example and integration functions
def integrate_biometric_registration():
    """Function to integrate biometric registration into user creation"""
    st.subheader("🔐 Biometric Registration")
    st.info("📝 Complete biometric setup for enhanced security")
    
    biometric_auth = BiometricAuth()
    
    # Face registration
    st.write("**Step 1: Face Recognition Setup**")
    face_image = biometric_auth.capture_face_image()
    
    st.write("**Step 2: Fingerprint Registration**")
    fingerprint_hash = biometric_auth.capture_fingerprint_simulation()
    
    return face_image, fingerprint_hash, biometric_auth

def create_biometric_login_page():
    """Create a standalone biometric login page"""
    st.title("🔐 UMID Biometric Access")
    st.markdown("---")
    
    biometric_auth = BiometricAuth()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        ### 🚀 Quick Access
        Use your biometric credentials to instantly access your medical records
        """)
        
        authenticated_user = biometric_auth.biometric_login_interface()
        
        if authenticated_user:
            st.session_state['biometric_user'] = authenticated_user
    
    with col2:
        st.markdown("""
        ### ℹ️ Biometric Features
        - **👆 Fingerprint Authentication**: Instant access with your fingerprint
        - **📷 Face Recognition**: Secure facial recognition login
        - **🔒 Enhanced Security**: Multi-factor biometric protection
        - **⚡ Quick Access**: No need to remember passwords
        """)
    
    # Display records if user is authenticated
    if 'biometric_user' in st.session_state:
        st.markdown("---")
        biometric_auth.display_user_records(st.session_state['biometric_user'])
        
        if st.button("🚪 Logout"):
            del st.session_state['biometric_user']
            st.rerun()

if __name__ == "__main__":
    # Standalone biometric demo
    create_biometric_login_page()