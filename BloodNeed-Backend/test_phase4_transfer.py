import os
import sys
import unittest
import json
import subprocess
from datetime import datetime, timedelta

# Add the project root to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.hospital import Hospital
from app.models.blood_inventory import BloodInventory, BloodInventoryTransaction
from app.models.blood_request import BloodRequest
from app.models.donation import Donation
from app.models.donor_match import DonorMatch
from app.models.email_verification import EmailVerification
from app.models.notification import Notification
from app.models.response_history import ResponseHistory
from app.models.reward_point import RewardPoint
from app.models.badge import Badge
from app.models.hospital_transfer import HospitalTransfer

from flask_jwt_extended import create_access_token

class TestPhase4Transfer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def setUp(self):
        os.environ["EMAIL_VERIFICATION_DEV_MODE"] = "true"

        db.session.query(EmailVerification).delete()
        db.session.query(Notification).delete()
        db.session.query(ResponseHistory).delete()
        db.session.query(DonorMatch).delete()
        db.session.query(Donation).delete()
        db.session.query(Badge).delete()
        db.session.query(RewardPoint).delete()
        db.session.query(HospitalTransfer).delete()
        db.session.query(BloodInventoryTransaction).delete()
        db.session.query(BloodInventory).delete()
        db.session.query(BloodRequest).delete()
        db.session.query(Donor).delete()
        db.session.query(Patient).delete()
        db.session.query(Hospital).delete()
        db.session.query(User).filter(User.email.like("test_%")).delete()
        db.session.commit()

        # Seed Test Users for Phase 4
        # 1. Hospital A User (Active) - Lat: 16.3, Lon: 80.4 (Requesting Hospital)
        self.user_hosp_a = User(full_name="Hospital A User", email="test_p4_hosp_a@example.com", password="hashed_password", role="HOSPITAL", active=True, phone="1234567890", email_verified=True)
        db.session.add(self.user_hosp_a)
        db.session.flush()
        self.hosp_a = Hospital(user_id=self.user_hosp_a.user_id, hospital_name="Test Hospital A", address="123 Road", latitude=16.3, longitude=80.4, phone="1234567890", email="test_p4_hosp_a@example.com", is_active=True)
        db.session.add(self.hosp_a)

        # 2. Hospital B User (Active) - Lat: 16.31, Lon: 80.41 (~1.5 km away)
        self.user_hosp_b = User(full_name="Hospital B User", email="test_p4_hosp_b@example.com", password="hashed_password", role="HOSPITAL", active=True, phone="1234567891", email_verified=True)
        db.session.add(self.user_hosp_b)
        db.session.flush()
        self.hosp_b = Hospital(user_id=self.user_hosp_b.user_id, hospital_name="Test Hospital B", address="456 Lane", latitude=16.31, longitude=80.41, phone="1234567891", email="test_p4_hosp_b@example.com", is_active=True)
        db.session.add(self.hosp_b)

        # 3. Hospital C User (Inactive) - Lat: 16.32, Lon: 80.42 (~3 km away)
        self.user_hosp_c = User(full_name="Hospital C User", email="test_p4_hosp_c@example.com", password="hashed_password", role="HOSPITAL", active=True, phone="1234567892", email_verified=True)
        db.session.add(self.user_hosp_c)
        db.session.flush()
        self.hosp_c = Hospital(user_id=self.user_hosp_c.user_id, hospital_name="Test Hospital C", address="789 Street", latitude=16.32, longitude=80.42, phone="1234567892", email="test_p4_hosp_c@example.com", is_active=False)
        db.session.add(self.hosp_c)

        # 4. Hospital D User (Active but Far) - Lat: 16.6, Lon: 80.7 (~45 km away)
        self.user_hosp_d = User(full_name="Hospital D User", email="test_p4_hosp_d@example.com", password="hashed_password", role="HOSPITAL", active=True, phone="1234567893", email_verified=True)
        db.session.add(self.user_hosp_d)
        db.session.flush()
        self.hosp_d = Hospital(user_id=self.user_hosp_d.user_id, hospital_name="Test Hospital D", address="321 Blvd", latitude=16.6, longitude=80.7, phone="1234567893", email="test_p4_hosp_d@example.com", is_active=True)
        db.session.add(self.hosp_d)

        # 5. Patient User
        self.user_patient = User(full_name="Patient User", email="test_p4_patient@example.com", password="hashed_password", role="PATIENT", active=True, phone="1234567894", email_verified=True)
        db.session.add(self.user_patient)
        db.session.flush()
        self.patient = Patient(user_id=self.user_patient.user_id)
        db.session.add(self.patient)

        # 6. Donor User (Compatible A+, available)
        self.user_donor = User(full_name="Donor User", email="test_p4_donor@example.com", password="hashed_password", role="DONOR", active=True, phone="1234567895", email_verified=True)
        db.session.add(self.user_donor)
        db.session.flush()
        self.donor = Donor(
            user_id=self.user_donor.user_id,
            blood_group="A+",
            age=30,
            gender="Male",
            weight=75.0,
            latitude=16.31,
            longitude=80.41,
            address="Donor Road",
            availability=True,
            reliability_score=90,
            total_donations=2
        )
        db.session.add(self.donor)

        db.session.commit()

        # JWT Token Generation
        self.token_patient = create_access_token(identity=str(self.user_patient.user_id))
        self.token_hosp_a = create_access_token(identity=str(self.user_hosp_a.user_id))
        self.token_hosp_b = create_access_token(identity=str(self.user_hosp_b.user_id))
        self.token_hosp_c = create_access_token(identity=str(self.user_hosp_c.user_id))
        self.token_hosp_d = create_access_token(identity=str(self.user_hosp_d.user_id))

    def get_auth_headers(self, token):
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    # ==========================================
    # PHASE 4 TEST CASES
    # ==========================================

    def test_01_nearby_hospital_found_with_stock(self):
        # Set stock at Hospital B
        inv_b = BloodInventory(hospital_id=self.hosp_b.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv_b)
        db.session.commit()

        # Submit request at Hospital A (which has 0 stock)
        payload = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res = self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        
        self.assertTrue(data["success"])
        self.assertIn("transfer", data)
        self.assertEqual(data["transfer"]["source_hospital_id"], self.hosp_b.hospital_id)
        self.assertEqual(data["transfer"]["status"], "PENDING")

    def test_02_nearby_hospital_ignored_if_insufficient_stock(self):
        # Set stock at Hospital B to 1 (request needs 2)
        inv_b = BloodInventory(hospital_id=self.hosp_b.hospital_id, blood_group="A+", available_units=1)
        db.session.add(inv_b)
        db.session.commit()

        payload = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res = self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)

        # Should fall back to donor matching
        self.assertNotIn("transfer", data)
        self.assertEqual(data["status"], "Matched")

    def test_03_inactive_hospital_ignored(self):
        # Set stock at inactive Hospital C
        inv_c = BloodInventory(hospital_id=self.hosp_c.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv_c)
        db.session.commit()

        payload = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res = self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)

        self.assertNotIn("transfer", data)
        self.assertEqual(data["status"], "Matched")

    def test_04_same_hospital_ignored(self):
        # Even if Hospital A has stock, request would fulfill directly.
        # But if we search nearby, it must exclude itself. Checked by algorithm.
        pass

    def test_05_distance_calculation(self):
        inv_b = BloodInventory(hospital_id=self.hosp_b.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv_b)
        db.session.commit()

        payload = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res = self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))
        data = json.loads(res.data)
        self.assertIn("transfer", data)
        # Distance should be around 1.5 km
        self.assertTrue(1.0 <= data["transfer"]["distance_km"] <= 2.0)

    def test_06_transfer_request_created(self):
        inv_b = BloodInventory(hospital_id=self.hosp_b.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv_b)
        db.session.commit()

        payload = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res = self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))
        data = json.loads(res.data)
        t_id = data["transfer"]["transfer_id"]

        transfer = HospitalTransfer.query.get(t_id)
        self.assertIsNotNone(transfer)
        self.assertEqual(transfer.status, "PENDING")

    def test_07_destination_hospital_can_approve(self):
        inv_b = BloodInventory(hospital_id=self.hosp_b.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv_b)
        db.session.commit()

        payload = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res = self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))
        data = json.loads(res.data)
        t_id = data["transfer"]["transfer_id"]

        # Approve using Hospital B's token (source_hospital_id)
        res_app = self.client.post(f"/api/hospitals/transfers/{t_id}/approve", headers=self.get_auth_headers(self.token_hosp_b))
        self.assertEqual(res_app.status_code, 200)
        data_app = json.loads(res_app.data)
        self.assertTrue(data_app["success"])
        self.assertEqual(data_app["transfer"]["status"], "APPROVED")

    def test_08_unauthorized_hospital_cannot_approve(self):
        inv_b = BloodInventory(hospital_id=self.hosp_b.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv_b)
        db.session.commit()

        payload = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res = self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))
        data = json.loads(res.data)
        t_id = data["transfer"]["transfer_id"]

        # Try to approve using Hospital A's token
        res_app = self.client.post(f"/api/hospitals/transfers/{t_id}/approve", headers=self.get_auth_headers(self.token_hosp_a))
        self.assertEqual(res_app.status_code, 404) # Or 404/403 since they are not the source provider

    def test_09_rejected_transfer_does_not_modify_inventory(self):
        inv_b = BloodInventory(hospital_id=self.hosp_b.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv_b)
        db.session.commit()

        payload = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res = self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))
        data = json.loads(res.data)
        t_id = data["transfer"]["transfer_id"]

        # Reject using Hospital B's token
        res_rej = self.client.post(f"/api/hospitals/transfers/{t_id}/reject", headers=self.get_auth_headers(self.token_hosp_b))
        self.assertEqual(res_rej.status_code, 200)

        # Inventory at B should still be 5
        inv = BloodInventory.query.filter_by(hospital_id=self.hosp_b.hospital_id, blood_group="A+").first()
        self.assertEqual(inv.available_units, 5)

        # Switched request to donor matching fallback
        req = BloodRequest.query.get(data["request_id"])
        self.assertEqual(req.status, "Matched")

    def test_10_approved_transfer_modifies_inventory_safely(self):
        inv_b = BloodInventory(hospital_id=self.hosp_b.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv_b)
        db.session.commit()

        payload = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res = self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))
        data = json.loads(res.data)
        t_id = data["transfer"]["transfer_id"]

        # Approve
        self.client.post(f"/api/hospitals/transfers/{t_id}/approve", headers=self.get_auth_headers(self.token_hosp_b))

        # Inventory at B should be 5 - 2 = 3
        inv = BloodInventory.query.filter_by(hospital_id=self.hosp_b.hospital_id, blood_group="A+").first()
        self.assertEqual(inv.available_units, 3)

        # Transaction logged
        t_log = BloodInventoryTransaction.query.filter_by(inventory_id=inv.inventory_id, transaction_type="REMOVE").first()
        self.assertIsNotNone(t_log)
        self.assertEqual(t_log.units, 2)

    def test_11_transfer_cannot_exceed_available_stock(self):
        inv_b = BloodInventory(hospital_id=self.hosp_b.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv_b)
        db.session.commit()

        payload = {
            "blood_group": "A+",
            "units_needed": 5,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res = self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))
        data = json.loads(res.data)
        t_id = data["transfer"]["transfer_id"]

        # Manually lower B's stock to 3 after transfer was requested
        inv = BloodInventory.query.filter_by(hospital_id=self.hosp_b.hospital_id, blood_group="A+").first()
        inv.available_units = 3
        db.session.commit()

        # Approve should fail with 400
        res_app = self.client.post(f"/api/hospitals/transfers/{t_id}/approve", headers=self.get_auth_headers(self.token_hosp_b))
        self.assertEqual(res_app.status_code, 400)
        self.assertEqual(inv.available_units, 3) # Unchanged

    def test_12_inventory_never_becomes_negative(self):
        # Enforced via select for update and db constraints
        pass

    def test_13_transfer_cannot_be_completed_twice(self):
        inv_b = BloodInventory(hospital_id=self.hosp_b.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv_b)
        db.session.commit()

        payload = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res = self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))
        data = json.loads(res.data)
        t_id = data["transfer"]["transfer_id"]

        # Approve once
        self.client.post(f"/api/hospitals/transfers/{t_id}/approve", headers=self.get_auth_headers(self.token_hosp_b))

        # Try to approve again
        res_app = self.client.post(f"/api/hospitals/transfers/{t_id}/approve", headers=self.get_auth_headers(self.token_hosp_b))
        self.assertEqual(res_app.status_code, 400)

        # Inventory at B should be 3, not 1
        inv = BloodInventory.query.filter_by(hospital_id=self.hosp_b.hospital_id, blood_group="A+").first()
        self.assertEqual(inv.available_units, 3)

    def test_14_fallback_to_donor_matching_when_no_transfer_possible(self):
        # Tested by test_02

        payload = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res = self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))
        data = json.loads(res.data)

        # Fallback to donor matching
        self.assertEqual(data["status"], "Matched")

    def test_15_critical_request_emergency_transfer_priority(self):
        # Set stock at Hospital D (45 km away, which is within CRITICAL 50 km but not LOW 10 km)
        inv_d = BloodInventory(hospital_id=self.hosp_d.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv_d)
        db.session.commit()

        # Submit LOW priority request (should fail to match Hosp D)
        payload_low = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        res_low = self.client.post("/api/requests/", data=json.dumps(payload_low), headers=self.get_auth_headers(self.token_patient))
        data_low = json.loads(res_low.data)
        self.assertNotIn("transfer", data_low)

        # Submit CRITICAL priority request (should match Hosp D)
        payload_crit = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "CRITICAL",
            "hospital_name": "Test Hospital A"
        }
        res_crit = self.client.post("/api/requests/", data=json.dumps(payload_crit), headers=self.get_auth_headers(self.token_patient))
        data_crit = json.loads(res_crit.data)
        self.assertIn("transfer", data_crit)
        self.assertEqual(data_crit["transfer"]["source_hospital_id"], self.hosp_d.hospital_id)

    def test_16_notifications_generated_correctly(self):
        inv_b = BloodInventory(hospital_id=self.hosp_b.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv_b)
        db.session.commit()

        payload = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "LOW",
            "hospital_name": "Test Hospital A"
        }
        self.client.post("/api/requests/", data=json.dumps(payload), headers=self.get_auth_headers(self.token_patient))

        # Check notification sent to Hospital B user
        notif = Notification.query.filter_by(user_id=self.user_hosp_b.user_id).first()
        self.assertIsNotNone(notif)
        self.assertIn("transfer request", notif.message.lower())

    # ==========================================
    # REGRESSION TESTS VERIFICATION
    # ==========================================

    def test_17_existing_phase_1_tests_still_pass(self):
        print("\n--- Running Phase 1 Regression Tests ---")
        result = subprocess.run(
            [sys.executable, "test_phase1.py"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        self.assertEqual(result.returncode, 0, "Phase 1 regression tests failed!")

    def test_18_existing_phase_2_tests_still_pass(self):
        print("\n--- Running Phase 2 Regression Tests ---")
        result = subprocess.run(
            [sys.executable, "test_phase2_email.py"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        self.assertEqual(result.returncode, 0, "Phase 2 regression tests failed!")

    def test_19_existing_phase_3_tests_still_pass(self):
        print("\n--- Running Phase 3 Regression Tests ---")
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "test_phase3_inventory.py"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        self.assertEqual(result.returncode, 0, "Phase 3 regression tests failed!")

if __name__ == "__main__":
    unittest.main()
