import sys
from app import create_app, db

# Import all models to ensure SQLAlchemy binds them
from app.models.user import User
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.hospital import Hospital
from app.models.blood_request import BloodRequest
from app.models.donor_match import DonorMatch
from app.models.donation import Donation
from app.models.badge import Badge
from app.models.reward_point import RewardPoint
from app.models.feedback import Feedback
from app.models.notification import Notification
from app.models.password_reset import PasswordReset
from app.models.response_history import ResponseHistory
from app.models.email_verification import EmailVerification
from app.models.blood_inventory import BloodInventory, BloodInventoryTransaction
from app.models.hospital_transfer import HospitalTransfer

app = create_app()
with app.app_context():
    print("Resetting database...")
    
    # Disable foreign key checks for clean truncation under MySQL/SQLite
    db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0;"))
    
    # Delete all rows
    db.session.query(DonorMatch).delete()
    db.session.query(Donation).delete()
    db.session.query(ResponseHistory).delete()
    db.session.query(BloodRequest).delete()
    db.session.query(Notification).delete()
    db.session.query(EmailVerification).delete()
    db.session.query(PasswordReset).delete()
    db.session.query(Feedback).delete()
    db.session.query(HospitalTransfer).delete()
    db.session.query(BloodInventoryTransaction).delete()
    db.session.query(BloodInventory).delete()
    db.session.query(RewardPoint).delete()
    db.session.query(Badge).delete()
    db.session.query(Donor).delete()
    db.session.query(Patient).delete()
    db.session.query(Hospital).delete()
    db.session.query(User).delete()
    
    db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1;"))
    db.session.commit()
    print("Database has been reset successfully!")
