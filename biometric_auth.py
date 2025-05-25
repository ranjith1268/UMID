import pandas as pd
import hashlib
import os
import time
import json
import random
from datetime import datetime
import numpy as np

# For real fingerprint scanner integration
try:
    import pyfingerprint  # For ZFM/R30X series scanners
    FINGERPRINT_AVAILABLE = True
except ImportError:
    pyfingerprint = None
    FINGERPRINT_AVAILABLE = False

try:
    import serial  # For serial communication with scanners
    SERIAL_AVAILABLE = True
except ImportError:
    serial = None
    SERIAL_AVAILABLE = False

class BiometricAuth:
    """
    Enhanced Biometric Authentication System for UMID
    Supports both real fingerprint scanner integration and demo mode
    """
    
    def __init__(self, scanner_port=None, scanner_baudrate=57600):
        self.biometric_file = "biometric_data.csv"
        self.scanner_port = scanner_port or self._get_default_port()
        self.scanner_baudrate = scanner_baudrate
        self.scanner = None
        self.demo_mode = False
        
        # Initialize storage and scanner
        self.init_biometric_storage()
        self.init_scanner_connection()
    
    def _get_default_port(self):
        """Get default scanner port based on OS"""
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            return "COM3"  # Common Windows COM port
        elif system == "linux":
            return "/dev/ttyUSB0"  # Common Linux USB port
        elif system == "darwin":  # macOS
            return "/dev/tty.usbserial"
        else:
            return "/dev/ttyUSB0"
    
    def init_biometric_storage(self):
        """Initialize biometric data storage file"""
        if not os.path.exists(self.biometric_file):
            biometric_df = pd.DataFrame(columns=[
                "user_id", "fingerprint_hash", "template_data", 
                "registration_date", "last_used", "quality_score", 
                "scanner_position", "usage_count"
            ])
            biometric_df.to_csv(self.biometric_file, index=False)
    
    def init_scanner_connection(self):
        """Initialize connection to fingerprint scanner"""
        if not FINGERPRINT_AVAILABLE:
            print("pyfingerprint library not available. Running in demo mode.")
            self.demo_mode = True
            return False, "Demo mode: Fingerprint scanner library not installed"
        
        try:
            # Try to connect to fingerprint scanner
            self.scanner = pyfingerprint.PyFingerprint(
                self.scanner_port, 
                self.scanner_baudrate, 
                0xFFFFFFFF, 
                0x00000000
            )
            
            if not self.scanner.verifyPassword():
                raise ValueError('Invalid fingerprint sensor password')
            
            template_count = self.scanner.getTemplateCount()
            storage_capacity = self.scanner.getStorageCapacity()
            
            print(f'Scanner connected! Templates: {template_count}/{storage_capacity}')
            return True, f"Scanner connected successfully ({template_count}/{storage_capacity} templates)"
            
        except Exception as e:
            print(f"Scanner connection failed: {str(e)}. Running in demo mode.")
            self.scanner = None
            self.demo_mode = True
            return False, f"Demo mode: {str(e)}"
    
    def capture_fingerprint_data(self):
        """
        Capture fingerprint data from hardware scanner
        Returns tuple: (success, data, message)
        """
        if self.demo_mode or self.scanner is None:
            return self._demo_capture_fingerprint()
        
        try:
            print('Place your finger on the scanner...')
            
            # Wait for finger placement (with timeout)
            timeout = 30  # 30 seconds timeout
            start_time = time.time()
            
            while not self.scanner.readImage():
                if time.time() - start_time > timeout:
                    return False, None, "Timeout: No finger detected"
                time.sleep(0.1)
            
            print('Processing fingerprint...')
            
            # Convert image to characteristics
            self.scanner.convertImage(0x01)
            
            # Download characteristics for processing
            characteristics = self.scanner.downloadCharacteristics(0x01)
            
            # Generate hash from characteristics
            fingerprint_hash = hashlib.sha256(str(characteristics).encode()).hexdigest()
            
            # Calculate quality score (simplified)
            quality_score = self._calculate_quality_score(characteristics)
            
            fingerprint_data = {
                'characteristics': characteristics,
                'hash': fingerprint_hash,
                'quality_score': quality_score,
                'timestamp': datetime.now().isoformat()
            }
            
            return True, fingerprint_data, "Fingerprint captured successfully"
            
        except Exception as e:
            return False, None, f"Fingerprint capture failed: {str(e)}"
    
    def _demo_capture_fingerprint(self):
        """Demo fingerprint capture for testing"""
        # Simulate fingerprint capture
        time.sleep(2)  # Simulate processing time
        
        # Generate demo fingerprint data
        demo_characteristics = [random.randint(1, 255) for _ in range(512)]
        fingerprint_hash = hashlib.sha256(str(demo_characteristics).encode()).hexdigest()
        
        fingerprint_data = {
            'characteristics': demo_characteristics,
            'hash': fingerprint_hash,
            'quality_score': random.randint(75, 95),
            'timestamp': datetime.now().isoformat()
        }
        
        return True, fingerprint_data, "Demo fingerprint captured"
    
    def _calculate_quality_score(self, characteristics):
        """Calculate fingerprint quality score"""
        try:
            # Simple quality calculation based on characteristics
            # In a real system, this would be more sophisticated
            if isinstance(characteristics, (list, tuple)):
                non_zero_count = sum(1 for x in characteristics if x != 0)
                quality = min(100, (non_zero_count / len(characteristics)) * 100)
                return int(quality)
            return 80  # Default quality score
        except:
            return 80
    
    def register_fingerprint(self, user_id):
        """
        Register a new fingerprint for a user
        """
        try:
            # Load existing biometric data
            biometric_df = pd.read_csv(self.biometric_file)
            
            # Check if user already has a fingerprint registered
            existing_registration = biometric_df[biometric_df["user_id"] == user_id]
            
            if not existing_registration.empty:
                return False, f"Fingerprint already registered for user {user_id}. Remove existing fingerprint first."
            
            print(f'Starting fingerprint registration for user: {user_id}')
            
            # First capture
            print('First scan: Place your finger on the scanner...')
            success1, data1, message1 = self.capture_fingerprint_data()
            
            if not success1:
                return False, f"First scan failed: {message1}"
            
            print('Remove your finger and place it again for verification...')
            time.sleep(2)
            
            # Second capture for verification
            print('Second scan: Place the same finger again...')
            success2, data2, message2 = self.capture_fingerprint_data()
            
            if not success2:
                return False, f"Second scan failed: {message2}"
            
            # Compare the two captures for similarity
            if not self._verify_fingerprint_match(data1, data2):
                return False, "Fingerprints don't match. Please try again with the same finger."
            
            # Use the better quality scan
            final_data = data1 if data1['quality_score'] >= data2['quality_score'] else data2
            
            # Store in scanner memory if hardware is available
            scanner_position = None
            if not self.demo_mode and self.scanner is not None:
                try:
                    # Create template in scanner
                    self.scanner.loadCharacteristics(0x01, final_data['characteristics'])
                    scanner_position = self.scanner.storeTemplate()
                    print(f'Template stored at position {scanner_position}')
                except Exception as e:
                    print(f'Warning: Could not store in scanner memory: {e}')
            
            # Add registration to database
            new_registration = pd.DataFrame({
                "user_id": [user_id],
                "fingerprint_hash": [final_data['hash']],
                "template_data": [json.dumps(final_data['characteristics'])],
                "registration_date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                "last_used": ["Never"],
                "quality_score": [final_data['quality_score']],
                "scanner_position": [scanner_position],
                "usage_count": [0]
            })
            
            updated_df = pd.concat([biometric_df, new_registration], ignore_index=True)
            updated_df.to_csv(self.biometric_file, index=False)
            
            mode_text = "demo mode" if self.demo_mode else "hardware scanner"
            return True, f"Fingerprint registered successfully for {user_id} using {mode_text} (Quality: {final_data['quality_score']}%)"
            
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def _verify_fingerprint_match(self, data1, data2, threshold=0.7):
        """Verify that two fingerprint captures match"""
        try:
            if self.demo_mode:
                # In demo mode, assume they match if quality is good
                return data1['quality_score'] > 70 and data2['quality_score'] > 70
            
            # Simple comparison - in production, use proper biometric matching
            chars1 = data1['characteristics']
            chars2 = data2['characteristics']
            
            if len(chars1) != len(chars2):
                return False
            
            # Calculate similarity
            matches = sum(1 for a, b in zip(chars1, chars2) if abs(a - b) <= 10)
            similarity = matches / len(chars1)
            
            return similarity >= threshold
            
        except Exception as e:
            print(f"Match verification error: {e}")
            return False
    
    def authenticate_fingerprint(self, captured_hash=None):
        """
        Authenticate fingerprint against registered users
        """
        try:
            # Load biometric data
            biometric_df = pd.read_csv(self.biometric_file)
            
            if biometric_df.empty:
                return None, "No registered fingerprints found in system"
            
            print(f'Authentication mode: {"Demo" if self.demo_mode else "Hardware Scanner"}')
            
            # Capture fingerprint for authentication
            if captured_hash:
                # Use provided hash (for demo/testing)
                auth_hash = captured_hash
                quality_score = 85
            else:
                print('Place your finger on the scanner for authentication...')
                success, fingerprint_data, message = self.capture_fingerprint_data()
                
                if not success:
                    return None, f"Authentication failed: {message}"
                
                auth_hash = fingerprint_data['hash']
                quality_score = fingerprint_data['quality_score']
            
            # Search for matching fingerprint in database
            best_match = None
            best_match_score = 0
            
            for _, row in biometric_df.iterrows():
                stored_hash = row["fingerprint_hash"]
                
                # In demo mode or for exact matches
                if auth_hash == stored_hash:
                    best_match = row
                    best_match_score = 100
                    break
                
                # For partial matching (in real scenarios)
                match_score = self._calculate_match_score(auth_hash, stored_hash)
                if match_score > best_match_score and match_score >= 80:
                    best_match = row
                    best_match_score = match_score
            
            if best_match is not None:
                user_id = best_match["user_id"]
                
                # Update usage statistics
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                usage_count = int(best_match.get("usage_count", 0)) + 1
                
                biometric_df.loc[biometric_df["user_id"] == user_id, "last_used"] = current_time
                biometric_df.loc[biometric_df["user_id"] == user_id, "usage_count"] = usage_count
                biometric_df.to_csv(self.biometric_file, index=False)
                
                return user_id, f"Authentication successful! Welcome {user_id} (Match: {best_match_score}%, Quality: {quality_score}%)"
            else:
                return None, f"Fingerprint not recognized. Access denied. (Quality: {quality_score}%)"
                
        except Exception as e:
            return None, f"Authentication error: {str(e)}"
    
    def _calculate_match_score(self, hash1, hash2):
        """Calculate similarity score between two fingerprint hashes"""
        try:
            # Simple hash comparison - in production, use proper biometric algorithms
            if hash1 == hash2:
                return 100
            
            # Calculate Hamming distance for partial matching
            min_len = min(len(hash1), len(hash2))
            matches = sum(1 for i in range(min_len) if hash1[i] == hash2[i])
            
            return int((matches / min_len) * 100)
            
        except Exception as e:
            return 0
    
    def get_user_fingerprints(self, user_id):
        """Get fingerprint information for a specific user"""
        try:
            biometric_df = pd.read_csv(self.biometric_file)
            user_fingerprints = biometric_df[biometric_df["user_id"] == user_id]
            
            if user_fingerprints.empty:
                return []
            
            fingerprint_info = []
            for _, row in user_fingerprints.iterrows():
                fingerprint_info.append({
                    "registration_date": row.get("registration_date", "Unknown"),
                    "last_used": row.get("last_used", "Never"),
                    "quality_score": row.get("quality_score", "N/A"),
                    "usage_count": row.get("usage_count", 0),
                    "scanner_position": row.get("scanner_position", "N/A")
                })
            
            return fingerprint_info
            
        except Exception as e:
            print(f"Error getting user fingerprints: {e}")
            return []
    
    def remove_fingerprint(self, user_id):
        """Remove a registered fingerprint"""
        try:
            biometric_df = pd.read_csv(self.biometric_file)
            user_data = biometric_df[biometric_df["user_id"] == user_id]
            
            if user_data.empty:
                return False, f"No fingerprint found for user {user_id}"
            
            # Remove from scanner memory if hardware is available
            if not self.demo_mode and self.scanner is not None:
                try:
                    scanner_position = user_data.iloc[0].get("scanner_position")
                    if scanner_position and scanner_position != "N/A":
                        self.scanner.deleteTemplate(int(scanner_position))
                        print(f'Removed template from scanner position {scanner_position}')
                except Exception as e:
                    print(f'Warning: Could not remove from scanner memory: {e}')
            
            # Remove from database
            biometric_df = biometric_df[biometric_df["user_id"] != user_id]
            biometric_df.to_csv(self.biometric_file, index=False)
            
            return True, f"Fingerprint removed successfully for {user_id}"
            
        except Exception as e:
            return False, f"Failed to remove fingerprint: {str(e)}"
    
    def get_biometric_stats(self):
        """Get comprehensive biometric system statistics"""
        try:
            biometric_df = pd.read_csv(self.biometric_file)
            
            # Calculate statistics
            total_registrations = len(biometric_df)
            unique_users = len(biometric_df["user_id"].unique()) if not biometric_df.empty else 0
            
            # Recent registrations (last 7 days)
            recent_registrations = 0
            if not biometric_df.empty:
                recent_date = (datetime.now() - pd.Timedelta(days=7))
                biometric_df['reg_date'] = pd.to_datetime(biometric_df["registration_date"], errors='coerce')
                recent_registrations = len(biometric_df[biometric_df['reg_date'] >= recent_date])
            
            # Average quality score
            avg_quality = 0
            if not biometric_df.empty:
                quality_scores = pd.to_numeric(biometric_df["quality_score"], errors='coerce')
                avg_quality = quality_scores.mean()
            
            # Usage statistics
            total_usage = biometric_df["usage_count"].sum() if not biometric_df.empty else 0
            
            stats = {
                "total_registrations": total_registrations,
                "unique_users": unique_users,
                "recent_registrations": recent_registrations,
                "avg_quality_score": round(avg_quality, 1),
                "total_authentications": int(total_usage),
                "scanner_connected": not self.demo_mode and self.scanner is not None,
                "demo_mode": self.demo_mode,
                "scanner_info": self._get_scanner_info()
            }
            
            return stats
            
        except Exception as e:
            return {
                "total_registrations": 0,
                "unique_users": 0,
                "recent_registrations": 0,
                "avg_quality_score": 0,
                "total_authentications": 0,
                "scanner_connected": False,
                "demo_mode": True,
                "scanner_info": f"Error: {str(e)}"
            }
    
    def _get_scanner_info(self):
        """Get detailed scanner information"""
        if self.demo_mode or self.scanner is None:
            return "Demo Mode - No Hardware Scanner"
        
        try:
            template_count = self.scanner.getTemplateCount()
            storage_capacity = self.scanner.getStorageCapacity()
            return f"Connected - Templates: {template_count}/{storage_capacity}"
        except Exception as e:
            return f"Scanner Error: {str(e)}"
    
    def get_registered_users(self):
        """Get list of users with registered fingerprints"""
        try:
            biometric_df = pd.read_csv(self.biometric_file)
            if biometric_df.empty:
                return []
            
            # Return list of dictionaries with user info
            users = []
            for user_id in biometric_df["user_id"].unique():
                user_data = biometric_df[biometric_df["user_id"] == user_id].iloc[0]
                users.append({
                    "user_id": user_id,
                    "registration_date": user_data.get("registration_date", "Unknown"),
                    "last_used": user_data.get("last_used", "Never"),
                    "usage_count": user_data.get("usage_count", 0),
                    "quality_score": user_data.get("quality_score", "N/A")
                })
            
            return users
            
        except Exception as e:
            print(f"Error getting registered users: {e}")
            return []

# Utility functions for integration

def integrate_biometric_registration():
    """
    Integration function for biometric registration
    Returns a registration interface function
    """
    def registration_interface(user_id):
        """Interface for biometric registration"""
        biometric_auth = BiometricAuth()
        
        print(f"Starting biometric registration for user: {user_id}")
        print(f"Mode: {'Demo' if biometric_auth.demo_mode else 'Hardware Scanner'}")
        
        # Attempt registration
        success, message = biometric_auth.register_fingerprint(user_id)
        
        return success, message
    
    return registration_interface

def get_scanner_status():
    """Get current scanner connection status"""
    try:
        biometric_auth = BiometricAuth()
        
        if biometric_auth.demo_mode:
            return False, "Demo Mode - No hardware scanner connected"
        
        if biometric_auth.scanner is not None:
            info = biometric_auth._get_scanner_info()
            return True, info
        else:
            return False, "Scanner initialization failed"
            
    except Exception as e:
        return False, f"Scanner status check failed: {str(e)}"

def setup_scanner_demo_data():
    """
    Setup demo fingerprint data for testing when hardware scanner is not available
    """
    try:
        biometric_file = "biometric_data.csv"
        
        # Check if demo data already exists
        if os.path.exists(biometric_file):
            existing_df = pd.read_csv(biometric_file)
            if not existing_df.empty:
                return True, f"Demo data already exists with {len(existing_df)} registrations"
        
        # Create demo fingerprint data for testing
        demo_users = [
            {"user_id": "patient1", "name": "John Doe"},
            {"user_id": "doctor1", "name": "Dr. Jane Smith"},
            {"user_id": "admin1", "name": "Admin User"},
            {"user_id": "pharmassist1", "name": "Pharmacy Assistant"}
        ]
        
        biometric_df = pd.DataFrame(columns=[
            "user_id", "fingerprint_hash", "template_data", 
            "registration_date", "last_used", "quality_score",
            "scanner_position", "usage_count"
        ])
        
        for i, user in enumerate(demo_users):
            # Generate unique demo fingerprint data
            demo_data = f"demo_{user['user_id']}_fingerprint_{datetime.now().isoformat()}"
            fingerprint_hash = hashlib.sha256(demo_data.encode()).hexdigest()
            
            # Create demo template data
            demo_characteristics = [random.randint(1, 255) for _ in range(512)]
            
            new_registration = pd.DataFrame({
                "user_id": [user["user_id"]],
                "fingerprint_hash": [fingerprint_hash],
                "template_data": [json.dumps(demo_characteristics)],
                "registration_date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                "last_used": ["Never"],
                "quality_score": [random.randint(80, 95)],
                "scanner_position": [f"demo_{i}"],
                "usage_count": [0]
            })
            
            biometric_df = pd.concat([biometric_df, new_registration], ignore_index=True)
        
        biometric_df.to_csv(biometric_file, index=False)
        return True, f"Demo biometric data created for {len(demo_users)} users"
        
    except Exception as e:
        return False, f"Failed to setup demo data: {str(e)}"

# Test functions for development

def test_biometric_system():
    """Test the biometric system functionality"""
    print("Testing Enhanced Biometric Authentication System")
    print("=" * 50)
    
    # Initialize system
    biometric_auth = BiometricAuth()
    
    # Display system info
    stats = biometric_auth.get_biometric_stats()
    print(f"System Mode: {'Demo' if stats['demo_mode'] else 'Hardware'}")
    print(f"Scanner Status: {stats['scanner_info']}")
    print(f"Registered Users: {stats['unique_users']}")
    print(f"Total Registrations: {stats['total_registrations']}")
    
    # Test demo data setup
    success, message = setup_scanner_demo_data()
    print(f"\nDemo Data Setup: {message}")
    
    # Display registered users
    users = biometric_auth.get_registered_users()
    if users:
        print(f"\nRegistered Users:")
        for user in users:
            print(f"  - {user['user_id']}: Quality {user['quality_score']}%, Used {user['usage_count']} times")
    
    print("\nBiometric system test completed!")

if __name__ == "__main__":
    test_biometric_system()