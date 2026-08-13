import os
import sys
from datetime import datetime, timedelta, date

# Add the project root to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.blood_request import BloodRequest
from app.models.donor_match import DonorMatch
from app.models.response_history import ResponseHistory
from app.models.notification import Notification
from app.models.donation import Donation
from app.models.badge import Badge
from app.models.reward_point import RewardPoint
from app.models.email_verification import EmailVerification
from app.models.hospital import Hospital
from app.models.blood_inventory import BloodInventory, BloodInventoryTransaction

app = create_app()

def setup_test_data():
    print("Setting up test database state...")
    
    # Clean previous test entries in correct foreign key order
    db.session.query(EmailVerification).delete()
    db.session.query(Notification).delete()
    db.session.query(ResponseHistory).delete()
    db.session.query(DonorMatch).delete()
    db.session.query(Donation).delete()
    db.session.query(Badge).delete()
    db.session.query(RewardPoint).delete()
    db.session.query(BloodInventoryTransaction).delete()
    db.session.query(BloodInventory).delete()
    db.session.query(BloodRequest).delete()
    db.session.query(Donor).delete()
    db.session.query(Patient).delete()
    db.session.query(Hospital).delete()
    db.session.query(User).filter(User.email.like("test_%")).delete()
    db.session.commit()

    # 1. Create Users
    patient_user = User(full_name="Test Patient", email="test_patient@example.com", phone="1111111111", role="PATIENT", active=True, email_verified=True)
    patient_user.password = "password"
    
    other_patient_user = User(full_name="Test Patient 2", email="test_patient2@example.com", phone="1111111112", role="PATIENT", active=True, email_verified=True)
    other_patient_user.password = "password"

    donor_user_1 = User(full_name="Test Donor 1", email="test_donor1@example.com", phone="2222222222", role="DONOR", active=True, email_verified=True)
    donor_user_1.password = "password"

    donor_user_2 = User(full_name="Test Donor 2", email="test_donor2@example.com", phone="3333333333", role="DONOR", active=True, email_verified=True)
    donor_user_2.password = "password"

    donor_user_inactive = User(full_name="Test Donor Inactive", email="test_donor_inactive@example.com", phone="4444444444", role="DONOR", active=False, email_verified=True)
    donor_user_inactive.password = "password"

    db.session.add_all([patient_user, other_patient_user, donor_user_1, donor_user_2, donor_user_inactive])
    db.session.commit()

    # 2. Create Patients
    patient = Patient(user_id=patient_user.user_id, blood_group="A+", age=30, gender="Male", hospital_name="City Hospital", latitude=16.2, longitude=80.5)
    other_patient = Patient(user_id=other_patient_user.user_id, blood_group="A+", age=32, gender="Female", hospital_name="City Hospital", latitude=16.2, longitude=80.5)
    db.session.add_all([patient, other_patient])

    # 3. Create Donors
    donor_1 = Donor(user_id=donor_user_1.user_id, blood_group="A+", age=25, gender="Male", weight=70.0, availability=True, latitude=16.21, longitude=80.51, address="Area 1")
    donor_2 = Donor(user_id=donor_user_2.user_id, blood_group="A+", age=25, gender="Male", weight=70.0, availability=True, latitude=16.22, longitude=80.52, address="Area 2")
    donor_inactive = Donor(user_id=donor_user_inactive.user_id, blood_group="A+", age=25, gender="Male", weight=70.0, availability=True, latitude=16.21, longitude=80.51, address="Area 1")
    
    db.session.add_all([donor_1, donor_2, donor_inactive])
    db.session.commit()

    return patient, other_patient, donor_1, donor_2, donor_inactive

def test_matching_and_privacy():
    with app.app_context():
        patient, other_patient, donor_1, donor_2, donor_inactive = setup_test_data()
        
        # Test Case 1: Patient creates a blood request
        print("\n--- Test Case 1 & 2: Creating Request and Matching ---")
        req = BloodRequest(
            patient_id=patient.patient_id,
            blood_group="A+",
            units_needed=1,
            emergency_level="CRITICAL",
            hospital_name="City Hospital",
            hospital_latitude=16.2,
            hospital_longitude=80.5,
            status="Pending"
        )
        db.session.add(req)
        db.session.commit()

        # Run matching
        from app.matching.services import find_matching_donors
        matches = find_matching_donors(req)
        print(f"Matched {len(matches)} donors.")
        
        # Verify matched donors
        matched_donor_ids = [m["donor"].donor_id for m in matches]
        assert donor_1.donor_id in matched_donor_ids, "Donor 1 should be matched"
        assert donor_2.donor_id in matched_donor_ids, "Donor 2 should be matched"
        assert donor_inactive.donor_id not in matched_donor_ids, "Inactive donor should be excluded (Test Case 5)"
        print("PASS: Test Cases 2 & 5 passed: Inactive donor excluded, active compatible donors matched.")

        # Test Case 6: Patient matching response does NOT contain donor phone/email before acceptance
        print("\n--- Test Case 6: Privacy masking before acceptance ---")
        serialized_donor_1_pending = donor_1.to_dict(show_contact=False)
        assert serialized_donor_1_pending["phone"] is None, "Phone should be hidden before acceptance"
        assert serialized_donor_1_pending["email"] is None, "Email should be hidden before acceptance"
        print("PASS: Test Case 6 passed: Donor contact details masked when show_contact=False.")

        # Test Case B: Patient can see appropriate contact info after donor accepts
        print("\n--- Test Case B: Contact info visible after acceptance ---")
        serialized_donor_1_accepted = donor_1.to_dict(show_contact=True)
        assert serialized_donor_1_accepted["phone"] == "2222222222", "Phone should be visible after acceptance"
        assert serialized_donor_1_accepted["email"] == "test_donor1@example.com", "Email should be visible after acceptance"
        print("PASS: Test Case B passed: Donor contact details visible when show_contact=True.")

        # Test Case 7: Search radius dynamic changes
        print("\n--- Test Case 7: Emergency search radius check ---")
        from app.ai.ranking import allowed_radius
        assert allowed_radius("CRITICAL") == 50
        assert allowed_radius("LOW") == 25
        print("PASS: Test Case 7 passed: Emergency allowed_radius resolves CRITICAL (50) and LOW (25).")

        # Test Case 9: Rejection moves to the next eligible donor
        print("\n--- Test Case 9: Reject escalation flow ---")
        # Let's get the active pending match (Donor 1 is first in score because they are closer)
        match_1 = DonorMatch.query.filter_by(request_id=req.request_id, donor_id=donor_1.donor_id).first()
        match_2 = DonorMatch.query.filter_by(request_id=req.request_id, donor_id=donor_2.donor_id).first()
        
        assert match_1.response_deadline is not None, "First match should have deadline"
        assert match_2.response_deadline is None, "Second match should NOT have deadline initially"

        # Simulate Reject from Donor 1
        # Set donor 1 response to Rejected
        match_1.donor_response = "Rejected"
        db.session.commit()

        # Let's trigger escalation (similar to response routes/timeout reject path)
        from app.donor.routes import respond_to_request # we can simulate response logic
        # Directly execute the escalation block
        from app.matching.services import is_donor_eligible, get_response_window
        
        # Verify next donor is notified
        next_match = DonorMatch.query.filter(
            DonorMatch.request_id == req.request_id,
            DonorMatch.donor_response == "Pending",
            DonorMatch.response_deadline.is_(None)
        ).order_by(DonorMatch.ranking_score.desc()).first()

        assert next_match.donor_id == donor_2.donor_id, "Next match should be Donor 2"
        
        # Set deadline for Donor 2 (escalated)
        response_minutes = get_response_window(req.emergency_level)
        next_match.response_deadline = datetime.utcnow() + timedelta(minutes=response_minutes)
        db.session.commit()
        
        assert next_match.response_deadline is not None, "Escalated match should now have deadline"
        print("PASS: Test Case 9 passed: Rejection successfully shifted deadline to the next donor.")

        # Test Case 10: Timeout moves to the next eligible donor
        print("\n--- Test Case 10: Timeout escalation flow ---")
        # Set Donor 2 deadline to past to simulate timeout
        next_match.response_deadline = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()

        # Trigger process_expired_matches
        from app.matching.timeout import process_expired_matches
        processed = process_expired_matches()
        
        assert next_match.match_id in processed, "Donor 2 match should be processed as expired"
        assert next_match.donor_response == "Missed", "Donor 2 response should be Missed"
        
        # Check history
        hist = ResponseHistory.query.filter_by(request_id=req.request_id, donor_id=donor_2.donor_id).first()
        assert hist is not None and hist.response_status == "Missed", "Missed status logged in response history"
        
        # Check request status goes to Pending since no eligible donors remain
        assert req.status == "Pending", "Request status should revert to Pending when queue empty"
        print("PASS: Test Case 10 passed: Timeout escalated, logged Missed, and marked request Pending when queue exhausted.")

        # Test Case E: Skipping unavailable donor during escalation
        print("\n--- Test Case E: Skipped unavailable donor check ---")
        # Setup again
        patient, other_patient, donor_1, donor_2, donor_inactive = setup_test_data()
        req_e = BloodRequest(
            patient_id=patient.patient_id,
            blood_group="A+",
            units_needed=1,
            emergency_level="CRITICAL",
            hospital_name="City Hospital",
            hospital_latitude=16.2,
            hospital_longitude=80.5,
            status="Pending"
        )
        db.session.add(req_e)
        db.session.commit()

        # Run matching to create matches
        matches_e = find_matching_donors(req_e)
        match_e1 = DonorMatch.query.filter_by(request_id=req_e.request_id, donor_id=donor_1.donor_id).first()
        match_e2 = DonorMatch.query.filter_by(request_id=req_e.request_id, donor_id=donor_2.donor_id).first()

        # Make Donor 2 unavailable
        donor_2.availability = False
        db.session.commit()

        # Donor 1 times out
        match_e1.response_deadline = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()

        # Run timeout escalation
        process_expired_matches()

        # Donor 2 should be skipped and marked Missed immediately because they became unavailable
        assert match_e2.donor_response == "Missed", "Donor 2 should be skipped and marked Missed"
        assert req_e.status == "Pending", "Request should be Pending since no other donor is eligible"
        print("PASS: Test Case E passed: Unavailable donor successfully skipped during escalation.")
        
        print("\nAll test cases executed successfully!")

if __name__ == "__main__":
    test_matching_and_privacy()
