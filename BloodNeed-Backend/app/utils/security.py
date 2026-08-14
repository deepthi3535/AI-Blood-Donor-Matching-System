from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import User
from app import db

def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Ensure JWT is valid in the request
            verify_jwt_in_request()
            
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user or not user.active or user.role not in roles:
                return jsonify({"message": "Forbidden: Access is denied"}), 403
            
            # Dynamic Self-Healing: Recreate missing profile rows if they were deleted
            if user.role == "DONOR":
                from app.models.donor import Donor
                donor = Donor.query.filter_by(user_id=user.user_id).first()
                if not donor:
                    donor = Donor(
                        user_id=user.user_id,
                        blood_group="A+",
                        age=30,
                        gender="Male",
                        weight=70.0,
                        latitude=16.3067,
                        longitude=80.4365,
                        address="Default Donor Address",
                        availability=True,
                        total_donations=0,
                        reliability_score=100,
                        reward_points=0,
                        badge="New Donor"
                    )
                    db.session.add(donor)
                    db.session.commit()
            elif user.role == "PATIENT":
                from app.models.patient import Patient
                patient = Patient.query.filter_by(user_id=user.user_id).first()
                if not patient:
                    patient = Patient(user_id=user.user_id)
                    db.session.add(patient)
                    db.session.commit()
            elif user.role == "HOSPITAL":
                from app.models.hospital import Hospital
                hospital = Hospital.query.filter_by(user_id=user.user_id).first()
                if not hospital:
                    hospital = Hospital(
                        user_id=user.user_id,
                        hospital_name=user.full_name or "Recovered Hospital",
                        address="Default Hospital Address",
                        latitude=16.3067,
                        longitude=80.4365,
                        phone=user.phone or "1234567890",
                        email=user.email,
                        is_active=True
                    )
                    db.session.add(hospital)
                    db.session.commit()
                
            return fn(*args, **kwargs)
        return wrapper
    return decorator
