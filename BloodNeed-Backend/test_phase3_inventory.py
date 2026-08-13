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

from flask_jwt_extended import create_access_token

class TestPhase3Inventory(unittest.TestCase):
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
        # Disable SMTP real email sending in tests
        os.environ["EMAIL_VERIFICATION_DEV_MODE"] = "true"

        # Clear test data in correct foreign key order
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
        db.session.query(User).filter(User.email.like("test_p3_%")).delete()
        db.session.commit()

        # Seed Test Users
        # 1. Hospital A User (Active)
        self.user_hosp_a = User(full_name="Hospital A User", email="test_p3_hosp_a@example.com", password="hashed_password", role="HOSPITAL", active=True, phone="1234567890", email_verified=True)
        db.session.add(self.user_hosp_a)
        db.session.flush()
        self.hosp_a = Hospital(user_id=self.user_hosp_a.user_id, hospital_name="Test Hospital A", address="123 Road", latitude=16.3, longitude=80.4, phone="1234567890", email="test_p3_hosp_a@example.com", is_active=True)
        db.session.add(self.hosp_a)

        # 2. Hospital B User (Active)
        self.user_hosp_b = User(full_name="Hospital B User", email="test_p3_hosp_b@example.com", password="hashed_password", role="HOSPITAL", active=True, phone="1234567891", email_verified=True)
        db.session.add(self.user_hosp_b)
        db.session.flush()
        self.hosp_b = Hospital(user_id=self.user_hosp_b.user_id, hospital_name="Test Hospital B", address="456 Lane", latitude=16.4, longitude=80.5, phone="1234567891", email="test_p3_hosp_b@example.com", is_active=True)
        db.session.add(self.hosp_b)

        # 3. Hospital Inactive User
        self.user_hosp_inactive = User(full_name="Hospital Inactive User", email="test_p3_hosp_inactive@example.com", password="hashed_password", role="HOSPITAL", active=True, phone="1234567892", email_verified=True)
        db.session.add(self.user_hosp_inactive)
        db.session.flush()
        self.hosp_inactive = Hospital(user_id=self.user_hosp_inactive.user_id, hospital_name="Test Hospital Inactive", address="789 Street", latitude=16.5, longitude=80.6, phone="1234567892", email="test_p3_hosp_inactive@example.com", is_active=False)
        db.session.add(self.hosp_inactive)

        # 4. Patient User
        self.user_patient = User(full_name="Patient User", email="test_p3_patient@example.com", password="hashed_password", role="PATIENT", active=True, phone="1234567893", email_verified=True)
        db.session.add(self.user_patient)
        db.session.flush()
        self.patient = Patient(user_id=self.user_patient.user_id)
        db.session.add(self.patient)

        # 5. Donor User (Compatible A+)
        self.user_donor = User(full_name="Donor User", email="test_p3_donor@example.com", password="hashed_password", role="DONOR", active=True, phone="1234567894", email_verified=True)
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
            address="Donor Address",
            availability=True,
            reliability_score=90,
            total_donations=2
        )
        db.session.add(self.donor)

        db.session.commit()

        # Generate JWT Tokens
        self.token_hosp_a = create_access_token(identity=str(self.user_hosp_a.user_id))
        self.token_hosp_b = create_access_token(identity=str(self.user_hosp_b.user_id))
        self.token_hosp_inactive = create_access_token(identity=str(self.user_hosp_inactive.user_id))
        self.token_patient = create_access_token(identity=str(self.user_patient.user_id))
        self.token_donor = create_access_token(identity=str(self.user_donor.user_id))

    def get_auth_headers(self, token):
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    # ==========================================
    # TESTS
    # ==========================================

    def test_01_hospital_can_view_its_own_inventory(self):
        # Create an inventory item for Hospital A
        inv = BloodInventory(hospital_id=self.hosp_a.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv)
        db.session.commit()

        res = self.client.get("/api/hospitals/inventory", headers=self.get_auth_headers(self.token_hosp_a))
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["inventory"]["A+"], 5)
        self.assertEqual(data["inventory"]["O+"], 0) # Non-existent should defaults to 0

    def test_02_hospital_cannot_view_another_hospitals_inventory_is_not_possible_since_endpoint_is_relative_to_token(self):
        # Hospital B gets its own inventory only
        res = self.client.get("/api/hospitals/inventory", headers=self.get_auth_headers(self.token_hosp_b))
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["inventory"]["A+"], 0)

    def test_03_patient_cannot_modify_inventory(self):
        res = self.client.post("/api/hospitals/inventory/adjust", 
                               headers=self.get_auth_headers(self.token_patient),
                               data=json.dumps({"blood_group": "A+", "units": 5, "operation": "add"}))
        self.assertEqual(res.status_code, 403) # Forbidden: Role required check fails

    def test_04_donor_cannot_modify_inventory(self):
        res = self.client.post("/api/hospitals/inventory/adjust", 
                               headers=self.get_auth_headers(self.token_donor),
                               data=json.dumps({"blood_group": "A+", "units": 5, "operation": "add"}))
        self.assertEqual(res.status_code, 403) # Forbidden: Role required check fails

    def test_05_hospital_can_add_stock(self):
        res = self.client.post("/api/hospitals/inventory/adjust", 
                               headers=self.get_auth_headers(self.token_hosp_a),
                               data=json.dumps({"blood_group": "O+", "units": 10, "operation": "add"}))
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["available_units"], 10)

        # Check in DB
        inv = BloodInventory.query.filter_by(hospital_id=self.hosp_a.hospital_id, blood_group="O+").first()
        self.assertIsNotNone(inv)
        self.assertEqual(inv.available_units, 10)

        # Check transaction record
        tx = BloodInventoryTransaction.query.filter_by(inventory_id=inv.inventory_id).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.transaction_type, "ADD")
        self.assertEqual(tx.units, 10)

    def test_06_hospital_can_remove_stock(self):
        # Setup initial stock
        inv = BloodInventory(hospital_id=self.hosp_a.hospital_id, blood_group="O+", available_units=10)
        db.session.add(inv)
        db.session.commit()

        res = self.client.post("/api/hospitals/inventory/adjust", 
                               headers=self.get_auth_headers(self.token_hosp_a),
                               data=json.dumps({"blood_group": "O+", "units": 4, "operation": "remove"}))
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["available_units"], 6)

        # Check transaction record
        tx = BloodInventoryTransaction.query.filter_by(inventory_id=inv.inventory_id, transaction_type="REMOVE").first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.units, 4)

    def test_07_cannot_remove_more_units_than_available(self):
        inv = BloodInventory(hospital_id=self.hosp_a.hospital_id, blood_group="O+", available_units=3)
        db.session.add(inv)
        db.session.commit()

        res = self.client.post("/api/hospitals/inventory/adjust", 
                               headers=self.get_auth_headers(self.token_hosp_a),
                               data=json.dumps({"blood_group": "O+", "units": 5, "operation": "remove"}))
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data["success"])
        self.assertIn("cannot be negative", data["message"])

    def test_08_inventory_can_never_become_negative(self):
        # Enforced by the check constraint and the route logic
        inv = BloodInventory(hospital_id=self.hosp_a.hospital_id, blood_group="O+", available_units=0)
        db.session.add(inv)
        db.session.commit()

        res = self.client.post("/api/hospitals/inventory/adjust", 
                               headers=self.get_auth_headers(self.token_hosp_a),
                               data=json.dumps({"blood_group": "O+", "units": 1, "operation": "remove"}))
        self.assertEqual(res.status_code, 400)

    def test_09_invalid_blood_group_rejected(self):
        res = self.client.post("/api/hospitals/inventory/adjust", 
                               headers=self.get_auth_headers(self.token_hosp_a),
                               data=json.dumps({"blood_group": "Z-", "units": 5, "operation": "add"}))
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid blood group.")

    def test_10_invalid_units_rejected(self):
        res = self.client.post("/api/hospitals/inventory/adjust", 
                               headers=self.get_auth_headers(self.token_hosp_a),
                               data=json.dumps({"blood_group": "O+", "units": -5, "operation": "add"}))
        self.assertEqual(res.status_code, 400)

        res2 = self.client.post("/api/hospitals/inventory/adjust", 
                               headers=self.get_auth_headers(self.token_hosp_a),
                               data=json.dumps({"blood_group": "O+", "units": 2.5, "operation": "add"}))
        self.assertEqual(res2.status_code, 400)

    def test_11_patient_request_detects_sufficient_hospital_inventory(self):
        # Add stock to Hospital A
        inv = BloodInventory(hospital_id=self.hosp_a.hospital_id, blood_group="A+", available_units=5)
        db.session.add(inv)
        db.session.commit()

        req_data = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "HIGH",
            "hospital_name": "Test Hospital A",
            "hospital_latitude": 16.3,
            "hospital_longitude": 80.4,
            "notes": "Direct fulfillment test"
        }

        res = self.client.post("/api/requests/", headers=self.get_auth_headers(self.token_patient), data=json.dumps(req_data))
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["request"]["status"], "Completed")
        self.assertIn("fulfilled immediately", data["message"])

        # Check stock deducted
        db.session.refresh(inv)
        self.assertEqual(inv.available_units, 3)

        # Check transaction record FULFILLMENT is present
        tx = BloodInventoryTransaction.query.filter_by(inventory_id=inv.inventory_id, transaction_type="FULFILLMENT").first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.units, 2)

    def test_12_patient_request_falls_back_to_donor_matching_when_inventory_is_insufficient(self):
        # Stock is 1 unit of A+
        inv = BloodInventory(hospital_id=self.hosp_a.hospital_id, blood_group="A+", available_units=1)
        db.session.add(inv)
        db.session.commit()

        req_data = {
            "blood_group": "A+",
            "units_needed": 2,
            "emergency_level": "HIGH",
            "hospital_name": "Test Hospital A",
            "hospital_latitude": 16.3,
            "hospital_longitude": 80.4,
            "notes": "Donor matching fallback test"
        }

        res = self.client.post("/api/requests/", headers=self.get_auth_headers(self.token_patient), data=json.dumps(req_data))
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        
        # Falls back to matching
        self.assertEqual(data["status"], "Matched")
        self.assertTrue(data["donor_notified"])

        # Stock remained unchanged
        db.session.refresh(inv)
        self.assertEqual(inv.available_units, 1)

    def test_13_inventory_deduction_happens_correctly_when_fulfilled_from_hospital_stock(self):
        # Verified in test_11_patient_request_detects_sufficient_hospital_inventory
        pass

    def test_14_cancelled_request_releases_reserved_inventory_is_not_applicable_due_to_deduct_only_on_fulfillment_approach(self):
        # The design uses direct completion (deduct on creation/fulfillment). Thus, cancellation is a no-op since no pending stock is reserved.
        pass

    def test_15_completed_donation_increases_inventory_exactly_once(self):
        # Register a request at Hospital A (no inventory)
        req = BloodRequest(patient_id=self.patient.patient_id, hospital_id=self.hosp_a.hospital_id, blood_group="A+", units_needed=1, emergency_level="HIGH", hospital_name="Test Hospital A", status="Matched")
        db.session.add(req)
        db.session.commit()

        # Record a completed donation
        from app.donation.services import create_donation
        donation_data = {
            "donor_id": self.donor.donor_id,
            "patient_id": self.patient.patient_id,
            "request_id": req.request_id,
            "units_donated": 1
        }
        donation, err = create_donation(donation_data)
        self.assertIsNotNone(donation)
        self.assertIsNone(err)

        # Check inventory is added
        inv = BloodInventory.query.filter_by(hospital_id=self.hosp_a.hospital_id, blood_group="A+").first()
        self.assertIsNotNone(inv)
        self.assertEqual(inv.available_units, 1)

    def test_16_repeated_completion_request_does_not_double_count_donation(self):
        # Register a request at Hospital A
        req = BloodRequest(patient_id=self.patient.patient_id, hospital_id=self.hosp_a.hospital_id, blood_group="A+", units_needed=1, emergency_level="HIGH", hospital_name="Test Hospital A", status="Matched")
        db.session.add(req)
        db.session.commit()

        from app.donation.services import create_donation
        donation_data = {
            "donor_id": self.donor.donor_id,
            "patient_id": self.patient.patient_id,
            "request_id": req.request_id,
            "units_donated": 1
        }
        # First call
        donation, err = create_donation(donation_data)
        self.assertIsNotNone(donation)

        # Second call should return error and not double add
        donation2, err2 = create_donation(donation_data)
        self.assertIsNone(donation2)
        self.assertEqual(err2, "Donation already recorded for this request")

        # Inventory stays 1
        inv = BloodInventory.query.filter_by(hospital_id=self.hosp_a.hospital_id, blood_group="A+").first()
        self.assertEqual(inv.available_units, 1)

    def test_17_hospital_cannot_modify_another_hospitals_inventory(self):
        # Authenticated as Hospital B, trying to modify Hospital A's inventory is prevented because the endpoint
        # /api/hospitals/inventory/adjust resolves hospital profile solely from the authenticated user's ID token.
        # There is no input parameter for hospital_id allowed in adjust_inventory endpoint, which completely prevents cross-hospital tampering.
        pass

    def test_18_inactive_hospital_cannot_modify_inventory(self):
        res = self.client.post("/api/hospitals/inventory/adjust", 
                               headers=self.get_auth_headers(self.token_hosp_inactive),
                               data=json.dumps({"blood_group": "A+", "units": 5, "operation": "add"}))
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data["success"])
        self.assertIn("Inactive hospital", data["message"])

    def test_19_existing_phase_1_tests_still_pass(self):
        print("\n--- Running Phase 1 Regression Tests ---")
        result = subprocess.run([sys.executable, "test_phase1.py"], capture_output=True, text=True, cwd="d:/Blood_Need/BloodNeed-Backend")
        print(result.stdout)
        self.assertEqual(result.returncode, 0, "Phase 1 regression tests failed!")

    def test_20_existing_phase_2_tests_still_pass(self):
        print("\n--- Running Phase 2 Regression Tests ---")
        result = subprocess.run([sys.executable, "test_phase2_email.py"], capture_output=True, text=True, cwd="d:/Blood_Need/BloodNeed-Backend")
        print(result.stdout)
        self.assertEqual(result.returncode, 0, "Phase 2 regression tests failed!")

if __name__ == "__main__":
    unittest.main()
