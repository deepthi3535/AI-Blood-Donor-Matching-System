import os
from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from datetime import datetime, timedelta
from app.auth.services import (
    register_user,
    login_user,
    reset_password as reset_password_service,
)

from app.models.user import User
from app.models.email_verification import EmailVerification

from app import db

from app.auth.utils import (
    hash_password,
    verify_password
)
from app.utils.email_service import generate_secure_otp, send_otp_email


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


# ====================================================
# REGISTER USER
# ====================================================

@auth_bp.route(
    "/register",
    methods=["POST"]
)
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Registration data is required"
        }), 400

    result = register_user(data)

    if result["success"]:
        return jsonify(result), 201

    return jsonify(result), 400


# ====================================================
# LOGIN USER
# ====================================================

@auth_bp.route(
    "/login",
    methods=["POST"]
)
def login():

    data = request.get_json()

    if not data:

        return jsonify({

            "message":
                "Login data is required"

        }), 400


    result = login_user(data)


    if result["success"]:

        return jsonify(result), 200


    return jsonify(result), 401


# ====================================================
# GET LOGGED-IN USER PROFILE
# ====================================================

@auth_bp.route(
    "/profile",
    methods=["GET"]
)
@jwt_required()
def profile():

    user_id = get_jwt_identity()


    user = User.query.get(
        user_id
    )


    if user is None:

        return jsonify({

            "message":
                "User not found"

        }), 404


    return jsonify(

        user.to_dict()

    ), 200


# ====================================================
# CHANGE PASSWORD
# ====================================================

@auth_bp.route(
    "/change-password",
    methods=["PUT"]
)
@jwt_required()
def change_password():

    user_id = get_jwt_identity()


    user = User.query.get(
        user_id
    )


    if user is None:

        return jsonify({

            "message":
                "User not found"

        }), 404


    data = request.get_json()


    if not data:

        return jsonify({

            "message":
                "Password data is required"

        }), 400


    current_password = data.get(
        "current_password"
    )


    new_password = data.get(
        "new_password"
    )


    if not current_password or not new_password:

        return jsonify({

            "message":
                "Current password and new password are required"

        }), 400


    if not verify_password(

        current_password,

        user.password

    ):

        return jsonify({

            "message":
                "Current password is incorrect"

        }), 400


    if len(new_password) < 6:

        return jsonify({

            "message":
                "New password must contain at least 6 characters"

        }), 400


    user.password = hash_password(

        new_password

    )


    db.session.commit()


    return jsonify({

        "message":
            "Password changed successfully"

    }), 200


# ====================================================
# RESET PASSWORD
# ====================================================

@auth_bp.route(
    "/reset-password",
    methods=["PUT"]
)
def reset_password():

    data = request.get_json()


    if not data:

        return jsonify({

            "message":
                "Reset password data is required"

        }), 400


    result = reset_password_service(data)

    status_code = result.get(
        "status_code",
        200 if result.get("success") else 400
    )

    return jsonify(result), status_code


# ====================================================
# RESET DONOR PASSWORD
# ====================================================

@auth_bp.route(
    "/reset-donor-password",
    methods=["POST"]
)
def reset_donor_password():

    data = request.get_json()


    if not data:

        return jsonify({

            "message":
                "Reset password data is required"

        }), 400


    email = data.get(
        "email"
    )


    new_password = data.get(
        "new_password"
    )


    if not email or not new_password:

        return jsonify({

            "message":
                "Email and new password are required"

        }), 400


    if len(new_password) < 6:

        return jsonify({

            "message":
                "New password must contain at least 6 characters"

        }), 400


    user = User.query.filter_by(

        email=email,

        role="DONOR"

    ).first()


    if user is None:

        return jsonify({

            "message":
                "Donor not found"

        }), 404


    user.password = hash_password(

        new_password

    )


    db.session.commit()


    return jsonify({

        "message":
            "Donor password reset successfully"

    }), 200
# ============================
# FORGOT PASSWORD
# ============================

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot():

    data = request.get_json()

    if not data:

        return jsonify({

            "message":
                "Reset password data is required"

        }), 400


    result = reset_password_service(data)

    status_code = result.get(
        "status_code",
        200 if result.get("success") else 400
    )

    return jsonify(result), status_code


# ==========================================
# VERIFY EMAIL OTP
# ==========================================

@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("otp"):
        return jsonify({
            "success": False,
            "message": "Email and OTP are required."
        }), 400

    email = data.get("email").strip()
    otp = data.get("otp").strip()

    # Check if already verified
    user = User.query.filter_by(email=email).first()
    if user and user.email_verified:
        return jsonify({
            "success": True,
            "message": "Email already verified."
        }), 200

    # Find the latest pending verification
    verification = EmailVerification.query.filter_by(
        email=email,
        verified=False
    ).order_by(EmailVerification.created_at.desc()).first()

    if not verification:
        return jsonify({
            "success": False,
            "message": "Verification record not found or already verified."
        }), 404

    if verification.expires_at < datetime.utcnow():
        return jsonify({
            "success": False,
            "message": "OTP has expired."
        }), 400

    if verification.attempts >= 5:
        return jsonify({
            "success": False,
            "message": "Maximum verification attempts exceeded."
        }), 400

    if not verify_password(otp, verification.otp_hash):
        verification.attempts += 1
        db.session.commit()
        return jsonify({
            "success": False,
            "message": "Invalid OTP."
        }), 400

    # Successful verification
    verification.verified = True
    verification.expires_at = datetime.utcnow() # Invalidate
    
    user = User.query.filter_by(email=email).first()
    if user:
        user.email_verified = True
    
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Email verified successfully."
    }), 200


# ==========================================
# RESEND OTP
# ==========================================

@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    data = request.get_json()
    if not data or not data.get("email"):
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    email = data.get("email").strip()

    user = User.query.filter_by(email=email).first()
    if not user:
        # Avoid revealing email existence
        return jsonify({
            "success": True,
            "message": "OTP resent successfully."
        }), 200

    # Find the latest verification
    verification = EmailVerification.query.filter_by(
        user_id=user.user_id
    ).order_by(EmailVerification.created_at.desc()).first()

    if verification:
        last_time = verification.last_resend_at or verification.created_at
        if last_time:
            diff = (datetime.utcnow() - last_time).total_seconds()
            if 0 <= diff < 60:
                return jsonify({
                    "success": False,
                    "message": "Please wait before requesting a new OTP."
                }), 429
        # Invalidate previous
        verification.expires_at = datetime.utcnow()

    # Generate new OTP
    otp = generate_secure_otp()
    otp_hash = hash_password(otp)

    new_verification = EmailVerification(
        user_id=user.user_id,
        email=user.email,
        otp_hash=otp_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        attempts=0,
        verified=False,
        last_resend_at=datetime.utcnow()
    )
    db.session.add(new_verification)
    send_otp_email(user.email, otp)
    db.session.commit()

    message = "OTP resent successfully."
    dev_mode = os.getenv("EMAIL_VERIFICATION_DEV_MODE", "false").lower() == "true" or not os.getenv("MAIL_SERVER") or not os.getenv("MAIL_USERNAME") or not os.getenv("MAIL_PASSWORD")
    if dev_mode:
        message += f" (Dev Mode OTP: {otp})"

    return jsonify({
        "success": True,
        "message": message
    }), 200


# ==========================================
# EMAIL VERIFICATION STATUS
# ==========================================

@auth_bp.route("/email-verification-status", methods=["GET"])
def email_verification_status():
    email = request.args.get("email")
    if not email:
        return jsonify({
            "success": False,
            "message": "Email parameter is required."
        }), 400

    user = User.query.filter_by(email=email.strip()).first()
    if not user:
        return jsonify({
            "success": False,
            "verified": False,
            "message": "User not found."
        }), 404

    return jsonify({
        "success": True,
        "verified": user.email_verified
    }), 200
