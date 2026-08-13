import os
import sys
import hashlib
from datetime import datetime, timedelta

# Add the project root to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.email_verification import EmailVerification
from app.models.donor_match import DonorMatch
from app.models.response_history import ResponseHistory
from app.models.notification import Notification
from app.models.donation import Donation
from app.models.badge import Badge
from app.models.reward_point import RewardPoint
from app.models.blood_request import BloodRequest
from app.auth.utils import verify_password
from app.utils.security import role_required

app = create_app()

def setup_test_data():
    print("Setting up Phase 2 test database...")
    # Clean previous test entries in correct foreign key order
    db.session.query(EmailVerification).delete()
    db.session.query(Notification).delete()
    db.session.query(ResponseHistory).delete()
    db.session.query(DonorMatch).delete()
    db.session.query(Donation).delete()
    db.session.query(Badge).delete()
    db.session.query(RewardPoint).delete()
    db.session.query(BloodRequest).delete()
    db.session.query(Donor).delete()
    db.session.query(Patient).delete()
    db.session.query(User).filter(User.email.like("test_p2_%")).delete()
    db.session.commit()

def test_phase2_flow():
    with app.app_context():
        setup_test_data()

        # Set DEV mode environment variables
        os.environ["EMAIL_VERIFICATION_DEV_MODE"] = "true"

        # ==========================================
        # TEST 1: Register donor (unverified)
        # ==========================================
        print("\n--- TEST 1: Register Donor (Unverified) ---")
        from app.auth.services import register_user
        donor_data = {
            "full_name": "Test Donor P2",
            "email": "test_p2_donor@example.com",
            "phone": "5555555551",
            "password": "password123",
            "role": "DONOR",
            "blood_group": "A+",
            "age": 25,
            "gender": "Male",
            "weight": 70.0,
            "latitude": 16.2,
            "longitude": 80.5,
            "address": "Donor Place"
        }
        res_donor = register_user(donor_data)
        if not res_donor.get("success"):
            print("FAILED REGISTER USER RESPONSE:", res_donor)
        assert res_donor["success"] is True, f"Donor registration failed: {res_donor.get('message')}"
        assert res_donor["message"] == "Registration successful. Please verify your email."
        
        user_donor = User.query.filter_by(email="test_p2_donor@example.com").first()
        assert user_donor is not None
        assert user_donor.email_verified is False, "Donor should be unverified"
        assert user_donor.active is True, "Donor should be active (design choice)"
        
        ver_donor = EmailVerification.query.filter_by(user_id=user_donor.user_id).first()
        assert ver_donor is not None, "Verification record not created"
        assert ver_donor.verified is False, "Verification status should be False"
        print("PASS: Donor registered as unverified and verification record initiated.")

        # ==========================================
        # TEST 2: Register patient (unverified)
        # ==========================================
        print("\n--- TEST 2: Register Patient (Unverified) ---")
        patient_data = {
            "full_name": "Test Patient P2",
            "email": "test_p2_patient@example.com",
            "phone": "5555555552",
            "password": "password123",
            "role": "PATIENT"
        }
        res_patient = register_user(patient_data)
        assert res_patient["success"] is True, "Patient registration failed"
        assert res_patient["message"] == "Registration successful. Please verify your email."
        
        user_patient = User.query.filter_by(email="test_p2_patient@example.com").first()
        assert user_patient is not None
        assert user_patient.email_verified is False, "Patient should be unverified"
        print("PASS: Patient registered as unverified and verification record initiated.")

        # ==========================================
        # TEST 10: Login before email verification
        # ==========================================
        print("\n--- TEST 10: Login Before Verification ---")
        from app.auth.services import login_user
        res_login_unverified = login_user({
            "email": "test_p2_donor@example.com",
            "password": "password123"
        })
        assert res_login_unverified["success"] is False
        assert res_login_unverified["message"] == "Please verify your email before logging in."
        assert "token" not in res_login_unverified, "Should not issue JWT for unverified user"
        print("PASS: Login rejected and JWT withheld for unverified donor.")

        # ==========================================
        # TEST 4: Incorrect OTP
        # ==========================================
        print("\n--- TEST 4: Incorrect OTP ---")
        # We need to simulate verify-email route logic
        # Find latest verification for test_p2_donor@example.com
        ver = EmailVerification.query.filter_by(email="test_p2_donor@example.com").order_by(EmailVerification.created_at.desc()).first()
        assert ver is not None
        
        # Check attempts starts at 0
        assert ver.attempts == 0
        
        # Call verification endpoint manually with incorrect OTP
        from app.auth.routes import verify_email
        # We will mock request context
        with app.test_request_context(json={"email": "test_p2_donor@example.com", "otp": "999999"}):
            resp, status_code = verify_email()
            assert status_code == 400
            assert resp.get_json()["success"] is False
            assert resp.get_json()["message"] == "Invalid OTP."
            
        db.session.refresh(ver)
        assert ver.attempts == 1, "Attempt counter should increment"
        print("PASS: Invalid OTP rejected and attempts counter incremented to 1.")

        # ==========================================
        # TEST 7: More than maximum OTP attempts
        # ==========================================
        print("\n--- TEST 7: Max OTP Attempts Limit ---")
        ver.attempts = 5
        db.session.commit()
        
        with app.test_request_context(json={"email": "test_p2_donor@example.com", "otp": "999999"}):
            resp, status_code = verify_email()
            assert status_code == 400
            assert resp.get_json()["success"] is False
            assert resp.get_json()["message"] == "Maximum verification attempts exceeded."
        print("PASS: Verification blocked after 5 failed attempts.")

        # Restore attempts for subsequent tests
        ver.attempts = 0
        db.session.commit()

        # ==========================================
        # TEST 5: Expired OTP
        # ==========================================
        print("\n--- TEST 5: Expired OTP ---")
        # Set expiry to past
        ver.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()
        
        with app.test_request_context(json={"email": "test_p2_donor@example.com", "otp": "123456"}):
            resp, status_code = verify_email()
            assert status_code == 400
            assert resp.get_json()["success"] is False
            assert resp.get_json()["message"] == "OTP has expired."
        print("PASS: Expired OTP rejected.")

        # ==========================================
        # TEST 8 & 9: Resend OTP cooldown and replacement
        # ==========================================
        print("\n--- TEST 8: Resend OTP Cooldown ---")
        # Restore expiry
        ver.expires_at = datetime.utcnow() + timedelta(minutes=5)
        # Attempt to resend OTP immediately (last_resend_at is null but created_at is current)
        from app.auth.routes import resend_otp
        with app.test_request_context(json={"email": "test_p2_donor@example.com"}):
            resp, status_code = resend_otp()
            assert status_code == 429
            assert resp.get_json()["success"] is False
            assert "wait" in resp.get_json()["message"]
        print("PASS: Resend rejected before 60-second cooldown.")

        print("\n--- TEST 9: Resend OTP After Cooldown ---")
        # Simulate cooldown passage
        ver.created_at = datetime.utcnow() - timedelta(seconds=61)
        db.session.commit()
        
        with app.test_request_context(json={"email": "test_p2_donor@example.com"}):
            resp, status_code = resend_otp()
            assert status_code == 200
            assert resp.get_json()["success"] is True
            
        # Get the new verification record
        new_ver = EmailVerification.query.filter_by(email="test_p2_donor@example.com").order_by(EmailVerification.created_at.desc()).first()
        assert new_ver.verification_id != ver.verification_id, "New verification record should have been created"
        
        # Verify previous OTP is invalidated
        db.session.refresh(ver)
        print("DEBUG PREVIOUS EXPIRES_AT:", ver.expires_at)
        print("DEBUG CURRENT UTCNOW:", datetime.utcnow())
        assert ver.expires_at <= datetime.utcnow() + timedelta(seconds=2), "Previous OTP should be expired/invalidated"
        print("PASS: Resend after cooldown succeeded. New OTP generated, previous invalidated.")

        # ==========================================
        # TEST 3: Correct OTP Verification
        # ==========================================
        print("\n--- TEST 3: Correct OTP ---")
        # Since we are in DEV mode, the OTP is printed to stdout. But in python tests, how do we get the OTP?
        # We cannot read stdout easily, but we can verify it because we have access to the DB!
        # Wait, since the OTP is hashed, how do we know the plain OTP?
        # Let's bypass it by extracting the generated OTP or mock check_password_hash?
        # No, in our service, the OTP is generated by generate_secure_otp() and stored as a hash.
        # For testing purposes, let's write a backdoor or mock it, OR we can generate a known OTP for test:
        # Let's update new_ver's otp_hash with a known hashed value!
        # Let's hash "123456" using hash_password and save it in new_ver!
        from app.auth.utils import hash_password
        new_ver.otp_hash = hash_password("123456")
        db.session.commit()
        
        # Now verify with correct OTP "123456"
        with app.test_request_context(json={"email": "test_p2_donor@example.com", "otp": "123456"}):
            resp, status_code = verify_email()
            assert status_code == 200
            assert resp.get_json()["success"] is True
            assert resp.get_json()["message"] == "Email verified successfully."
            
        # Check user is verified
        db.session.refresh(user_donor)
        assert user_donor.email_verified is True, "User should be verified"
        
        # Check verification record is marked verified
        db.session.refresh(new_ver)
        assert new_ver.verified is True
        print("PASS: Verified user using correct OTP, email_verified updated to True.")

        # ==========================================
        # TEST 6: Reuse verified OTP
        # ==========================================
        print("\n--- TEST 6: Reuse Verified OTP ---")
        with app.test_request_context(json={"email": "test_p2_donor@example.com", "otp": "123456"}):
            ret = verify_email()
            print("REUSE OTP RETURN VALUE:", ret)
            if isinstance(ret, tuple):
                resp, status_code = ret
            else:
                resp = ret
                status_code = ret.status_code if hasattr(ret, 'status_code') else 200
            
            # Print body
            if hasattr(resp, 'get_json'):
                print("REUSE OTP BODY:", resp.get_json())
            else:
                print("REUSE OTP BODY:", resp)
                
            assert status_code == 200
            if hasattr(resp, 'get_json'):
                assert resp.get_json()["success"] is True
                assert resp.get_json()["message"] == "Email already verified."
            else:
                assert resp["success"] is True
                assert resp["message"] == "Email already verified."
        print("PASS: Verified OTP cannot be reused to verify again (bypassed with already verified message).")

        # ==========================================
        # TEST 11: Login after verification
        # ==========================================
        print("\n--- TEST 11: Login After Verification ---")
        res_login_verified = login_user({
            "email": "test_p2_donor@example.com",
            "password": "password123"
        })
        assert res_login_verified["success"] is True
        assert res_login_verified["message"] == "Login Successful."
        assert "token" in res_login_verified, "Should issue JWT token"
        print("PASS: Login successful and JWT issued after email verification.")

        # ==========================================
        # TEST 13: Development Mode Check
        # ==========================================
        print("\n--- TEST 13: Development Mode Check ---")
        from app.utils.email_service import send_otp_email
        # When dev mode is true, send_otp_email returns True and prints to stdout without raising SMTP errors
        assert send_otp_email("test_p2_dev@example.com", "654321") is True, "Dev mode sending failed"
        print("PASS: Development mode handles email sending gracefully without SMTP configuration.")

        print("\nAll Phase 2 test cases executed successfully!")

if __name__ == "__main__":
    test_phase2_flow()
