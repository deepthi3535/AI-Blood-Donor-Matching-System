from flask import jsonify
from werkzeug.security import generate_password_hash

from app import db
from app.auth.utils import hash_password, verify_password, generate_token
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.user import User


def register_user(data):
    required_fields = [
        "full_name",
        "email",
        "phone",
        "password"
    ]

    for field in required_fields:
        if not data.get(field):
            return {
                "success": False,
                "message": f"{field} is required."
            }

    role = data.get("role", "PATIENT").upper()

    if role not in ["ADMIN", "DONOR", "PATIENT"]:
        return {
            "success": False,
            "message": "Invalid role."
        }

    if User.query.filter_by(email=data["email"]).first():
        return {
            "success": False,
            "message": "Email already exists."
        }

    if User.query.filter_by(phone=data["phone"]).first():
        return {
            "success": False,
            "message": "Phone number already exists."
        }

    try:

        # ---------------- USER ----------------

        user = User(
            full_name=data["full_name"],
            email=data["email"],
            phone=data["phone"],
            password=hash_password(data["password"]),
            role=role,
            active=True
        )

        db.session.add(user)
        db.session.flush()

        # ---------------- DONOR ----------------

        if role == "DONOR":

            donor = Donor(
                user_id=user.user_id,
                blood_group=data.get("blood_group"),
                age=data.get("age"),
                gender=data.get("gender"),
                weight=data.get("weight"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                address=data.get("address"),
                availability=True,
                total_donations=0,
                reliability_score=0,
                reward_points=0,
                badge="New Donor"
            )

            db.session.add(donor)

        # ---------------- PATIENT ----------------

        if role == "PATIENT":

            patient = Patient(
                user_id=user.user_id
            )

            db.session.add(patient)

        db.session.commit()

        return {
            "success": True,
            "message": "Registration Successful."
        }
    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "message": str(e)
        }


def login_user(data):

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {
            "success": False,
            "message": "Email and Password are required."
        }

    user = User.query.filter_by(
        email=email
    ).first()

    if user is None:
        return {
            "success": False,
            "message": "Invalid Email."
        }

    if not verify_password(
        password,
        user.password
    ):
        return {
            "success": False,
            "message": "Invalid Password."
        }

    token = generate_token(user)

    return {
        "success": True,
        "message": "Login Successful.",
        "token": token,
        "user": user.to_dict()
    }


def reset_donor_password(email, new_password):
    user = User.query.filter_by(email=email, role="DONOR").first()

    if not user:
        return False

    user.password = hash_password(new_password)
    db.session.commit()
    return True


def reset_password(data):
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify({"message": "Email not found"}), 404

    user.password = generate_password_hash(password)
    db.session.commit()

    return jsonify({"message": "Password Updated Successfully"}), 200