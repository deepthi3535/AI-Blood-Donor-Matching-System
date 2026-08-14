from datetime import date, datetime, timedelta
from re import match

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.badge import Badge
from app.models.blood_request import BloodRequest
from app.models.donation import Donation
from app.models.donor import Donor
from app.models.donor_match import DonorMatch
from app.models.patient import Patient
from app.models.reward_point import RewardPoint
from app.notifications.services import create_notification
from app.response_history.services import create_history
from app.schemas.donor_schema import validate_donor
from app.models.user import User
from app.donor.services import (
    create_donor,
    delete_donor,
    get_all_donors,
    get_donor,
    update_donor,
)
from app.utils.security import role_required


donor_bp = Blueprint(
    "donor",
    __name__,
    url_prefix="/api/donors",
)


# NOTE: The following logic was previously placed at module level and caused
# syntax/runtime errors (e.g. 'return' outside function). Ensure request
# response handling code is defined inside the appropriate view functions.
@donor_bp.route("/", methods=["GET"])
@jwt_required()
@role_required("ADMIN")
def donors():

    donors = get_all_donors()

    return jsonify([
        donor.to_dict()
        for donor in donors
    ]), 200


# ====================================================
# GET DONOR BY ID
# ====================================================

@donor_bp.route("/<int:donor_id>", methods=["GET"])
@jwt_required()
@role_required("ADMIN", "DONOR", "PATIENT")
def donor_details(donor_id):

    donor = get_donor(donor_id)

    if donor is None:

        return jsonify({
            "message": "Donor not found"
        }), 404

    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    show_contact = False
    if user.role == "ADMIN":
        show_contact = True
    elif user.role == "DONOR" and donor.user_id == user.user_id:
        show_contact = True
    elif user.role == "PATIENT":
        patient = Patient.query.filter_by(user_id=user.user_id).first()
        if patient:
            from app.models.blood_request import BloodRequest
            accepted_match = DonorMatch.query.join(BloodRequest).filter(
                DonorMatch.donor_id == donor.donor_id,
                DonorMatch.donor_response == "Accepted",
                BloodRequest.patient_id == patient.patient_id
            ).first()
            if accepted_match:
                show_contact = True

    return jsonify(
        donor.to_dict(show_contact=show_contact)
    ), 200


# ====================================================
# CREATE DONOR PROFILE
# ====================================================
# ====================================================
# CREATE DONOR
# ====================================================

@donor_bp.route(
    "/",
    methods=["POST"],
)
@jwt_required()
def add_donor():

    # 1. Get logged-in user's ID from JWT token
    user_id = get_jwt_identity()

    # 2. Get donor data from Postman
    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Donor data is required"
        }), 400

    # 3. Add user_id automatically
    data["user_id"] = user_id

    # 4. Validate donor data
    valid, message = validate_donor(data)

    if not valid:
        return jsonify({
            "message": message
        }), 400

    # 5. Create donor profile
    donor = create_donor(data, user_id)

    if donor is None:
        return jsonify({
            "message": "Donor profile already exists or user not found"
        }), 400

    return jsonify({
        "message": "Donor profile created successfully",
        "donor": donor.to_dict(),
    }), 201


# ====================================================
# UPDATE DONOR
# ====================================================

@donor_bp.route("/<int:donor_id>", methods=["PUT"])
@jwt_required()
def edit_donor(donor_id):

    donor = get_donor(donor_id)

    if donor is None:

        return jsonify({
            "message": "Donor not found"
        }), 404

    user_id = get_jwt_identity()

    if donor.user_id != user_id:

        return jsonify({
            "message": "Unauthorized"
        }), 403

    data = request.get_json()

    if not data:

        return jsonify({
            "message": "Update data is required"
        }), 400

    donor = update_donor(
        donor,
        data
    )

    return jsonify(
        donor.to_dict(show_contact=True)
    ), 200


# ====================================================
# DELETE DONOR
# ====================================================

@donor_bp.route("/<int:donor_id>", methods=["DELETE"])
@jwt_required()
def remove_donor(donor_id):

    donor = get_donor(donor_id)

    if donor is None:

        return jsonify({
            "message": "Donor not found"
        }), 404

    user_id = get_jwt_identity()

    if donor.user_id != user_id:

        return jsonify({
            "message": "Unauthorized"
        }), 403

    delete_donor(donor)

    return jsonify({
        "message": "Donor deleted successfully"
    }), 200


# ====================================================
# UPDATE DONOR AVAILABILITY
# ====================================================

@donor_bp.route("/availability", methods=["PATCH"])
@jwt_required()
@role_required("DONOR")
def update_availability():

    user_id = get_jwt_identity()

    donor = Donor.query.filter_by(
        user_id=user_id
    ).first()

    if donor is None:

        return jsonify({
            "message": "Donor profile not found"
        }), 404

    data = request.get_json()

    if not data or "availability" not in data:

        return jsonify({
            "message": "Availability is required"
        }), 400

    availability = data.get(
        "availability"
    )

    if not isinstance(
        availability,
        bool
    ):

        return jsonify({
            "message": "Availability must be true or false"
        }), 400

    donor.availability = availability

    db.session.commit()

    return jsonify({

        "message":
            "Availability updated successfully",

        "availability":
            donor.availability

    }), 200


# ====================================================
# DONOR DASHBOARD
# ====================================================

@donor_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@role_required("DONOR")
def donor_dashboard():

    user_id = get_jwt_identity()

    donor = Donor.query.filter_by(
        user_id=user_id
    ).first()

    if donor is None:

        return jsonify({
            "message": "Donor profile not found"
        }), 404

    if donor.next_eligible_date and date.today() >= donor.next_eligible_date:

        donor.availability = True

        db.session.commit()

    total_donations = Donation.query.filter_by(
        donor_id=donor.donor_id
    ).count()

    total_requests = DonorMatch.query.filter_by(
        donor_id=donor.donor_id
    ).count()

    accepted_requests = DonorMatch.query.filter_by(
        donor_id=donor.donor_id,
        donor_response="Accepted"
    ).count()

    rejected_requests = DonorMatch.query.filter_by(
        donor_id=donor.donor_id,
        donor_response="Rejected"
    ).count()

    missed_requests = DonorMatch.query.filter_by(
        donor_id=donor.donor_id,
        donor_response="Missed"
    ).count()

    if total_requests > 0:

        acceptance_rate = round(
            (
                accepted_requests /
                total_requests
            ) * 100,
            2
        )

    else:

        acceptance_rate = 0

    rewards = RewardPoint.query.filter_by(
        donor_id=donor.donor_id
    ).all()

    total_points = sum(
        reward.points
        for reward in rewards
    )

    badges = Badge.query.filter_by(
        donor_id=donor.donor_id
    ).count()

    recent_donations = Donation.query.filter_by(
        donor_id=donor.donor_id
    ).order_by(
        Donation.donation_date.desc()
    ).limit(5).all()

    return jsonify({

        "donor":
            donor.to_dict(show_contact=True),

        "total_donations":
            total_donations,

        "reward_points":
            total_points,

        "badges":
            badges,

        "reliability_score":
            donor.reliability_score,

        "availability":
            donor.availability,

        "last_donation_date":
            str(
                donor.last_donation_date
            )
            if donor.last_donation_date
            else None,

        "total_requests":
            total_requests,

        "accepted_requests":
            accepted_requests,

        "rejected_requests":
            rejected_requests,

        "missed_requests":
            missed_requests,

        "acceptance_rate":
            acceptance_rate,
        "recent_donations": [
            donation.to_dict()
            for donation in recent_donations
        ],

    }), 200


# ====================================================
# DONOR REWARD POINTS
# ====================================================

@donor_bp.route("/reward-points", methods=["GET"])
@jwt_required()
@role_required("DONOR")
def donor_reward_points():

    user_id = get_jwt_identity()

    donor = Donor.query.filter_by(
        user_id=user_id
    ).first()

    if donor is None:

        return jsonify({
            "message": "Donor profile not found"
        }), 404

    rewards = RewardPoint.query.filter_by(
        donor_id=donor.donor_id
    ).all()

    return jsonify([
        reward.to_dict()
        for reward in rewards
    ]), 200


# ====================================================
# DONOR BADGES
# ====================================================

@donor_bp.route("/badges", methods=["GET"])
@jwt_required()
@role_required("DONOR")
def donor_badges():

    user_id = get_jwt_identity()

    donor = Donor.query.filter_by(
        user_id=user_id
    ).first()

    if donor is None:

        return jsonify({
            "message": "Donor profile not found"
        }), 404

    badges = Badge.query.filter_by(
        donor_id=donor.donor_id
    ).all()

    return jsonify([
        badge.to_dict()
        for badge in badges
    ]), 200


# ====================================================
# DONOR DONATIONS
# ====================================================

@donor_bp.route("/donations", methods=["GET"])
@jwt_required()
@role_required("DONOR")
def donor_donations():

    user_id = get_jwt_identity()

    donor = Donor.query.filter_by(
        user_id=user_id
    ).first()

    if donor is None:

        return jsonify({
            "message": "Donor profile not found"
        }), 404

    donations = Donation.query.filter_by(
        donor_id=donor.donor_id
    ).order_by(
        Donation.donation_date.desc()
    ).all()

    return jsonify([
        donation.to_dict()
        for donation in donations
    ]), 200


# ====================================================
# DONOR INCOMING BLOOD REQUESTS
# ====================================================

@donor_bp.route("/requests", methods=["GET"])
@jwt_required()
@role_required("DONOR")
def donor_requests():

    user_id = get_jwt_identity()

    donor = Donor.query.filter_by(
        user_id=user_id
    ).first()


    if donor is None:

        return jsonify({
            "message": "Donor profile not found"
        }), 404

    matches = DonorMatch.query.filter_by(
        donor_id=donor.donor_id
    ).all()

    result = []

    for match in matches:

        blood_request = BloodRequest.query.get(
            match.request_id
        )

        if blood_request is None:
            continue

        patient = Patient.query.get(blood_request.patient_id)
        user = User.query.get(patient.user_id) if patient else None

        result.append({
            "patient_name": user.full_name if user else None,

"patient_phone": user.phone if (user and match.donor_response == "Accepted") else None,
            "match_id": match.match_id,
            "request_id": blood_request.request_id,
            "blood_group": blood_request.blood_group,
            "units_needed": blood_request.units_needed,
            "emergency_level": blood_request.emergency_level,
            "hospital_name": blood_request.hospital_name,
            "hospital_latitude": blood_request.hospital_latitude,
            "hospital_longitude": blood_request.hospital_longitude,
            "distance_km": round(match.distance_km, 2)
                if match.distance_km is not None
                else None,
            "ranking_score": round(match.ranking_score, 2)
                if match.ranking_score is not None
                else 0,
            "response_probability": round(match.response_probability, 2)
                if match.response_probability is not None
                else 0,
            "donor_response": match.donor_response,
            "response_deadline": match.response_deadline.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if match.response_deadline
                else None,
            "request_status": blood_request.status,
            "request_time": blood_request.request_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if blood_request.request_time
                else None
        })

    return jsonify(result), 200


# ====================================================
# DONOR ACCEPT / REJECT REQUEST
# ====================================================

@donor_bp.route(
    "/requests/<int:match_id>/respond",
    methods=["PATCH"]
)
@jwt_required()
@role_required("DONOR")
def respond_to_request(match_id):

    # --------------------------------------------
    # GET LOGGED-IN DONOR
    # --------------------------------------------

    user_id = get_jwt_identity()

    donor = Donor.query.filter_by(
        user_id=user_id
    ).first()

    if donor is None:

        return jsonify({
            "message": "Donor profile not found"
        }), 404

    # --------------------------------------------
    # FIND DONOR'S MATCH
    # --------------------------------------------

    match = DonorMatch.query.filter_by(

        match_id=match_id,

        donor_id=donor.donor_id

    ).first()

    if match is None:

        return jsonify({
            "message": "Matching request not found"
        }), 404

    # --------------------------------------------
    # GET BLOOD REQUEST
    # --------------------------------------------

    blood_request = BloodRequest.query.get(
        match.request_id
    )

    if blood_request is None:

        return jsonify({
            "message": "Blood request not found"
        }), 404

    # --------------------------------------------
    # CHECK REQUEST STATUS
    # --------------------------------------------

    if blood_request.status in [

        "Accepted",

        "Completed",

        "Cancelled"

    ]:

        return jsonify({
            "message":
                "This blood request is no longer active"
        }), 400

    # --------------------------------------------
    # CHECK EXISTING RESPONSE
    # --------------------------------------------

    if match.donor_response != "Pending":

        return jsonify({
            "message":
                "You have already responded to this request"
        }), 400

    # --------------------------------------------
    # CHECK DEADLINE
    # --------------------------------------------

    if (

        match.response_deadline

        and

        datetime.utcnow()
        >
        match.response_deadline

    ):

        match.donor_response = "Rejected"

        create_history({

            "donor_id":
                donor.donor_id,

            "request_id":
                match.request_id,

            "response_status":
                "Missed",

            "response_time_seconds":
                0,

            "ai_score":
                match.ranking_score

        })

        db.session.commit()

        return jsonify({
            "message":
                "Response time has expired"
        }), 400

    # --------------------------------------------
    # READ RESPONSE
    # --------------------------------------------

    data = request.get_json()

    if not data:

        return jsonify({
            "message": "Response data is required"
        }), 400

    response = data.get(
        "response"
    )

    if response not in [

        "Accepted",

        "Rejected"

    ]:

        return jsonify({
            "message":
                "Response must be Accepted or Rejected"
        }), 400

    # --------------------------------------------
    # RESPONSE TIME
    # --------------------------------------------

    response_time_seconds = 0

    if blood_request.request_time:

        response_time_seconds = int(

            (

                datetime.utcnow()

                -

                blood_request.request_time

            ).total_seconds()

        )

    # --------------------------------------------
    # UPDATE MATCH
    # --------------------------------------------

    match.donor_response = response

    # --------------------------------------------
    # RESPONSE HISTORY
    # --------------------------------------------

    create_history({

        "donor_id":
            donor.donor_id,

        "request_id":
            match.request_id,

        "response_status":
            response,

        "response_time_seconds":
            response_time_seconds,

        "ai_score":
            match.ranking_score

    })

    # --------------------------------------------
    # GET PATIENT
    # --------------------------------------------

    patient = Patient.query.get(
        blood_request.patient_id
    )

    # --------------------------------------------
    # ACCEPTED
    # --------------------------------------------
    if response == "Accepted":

        donor.total_donations += 1
        donor.reward_points += 50

        donor.last_donation_date = date.today()
        donor.next_eligible_date = date.today() + timedelta(days=90)
        donor.availability = False
        print("LAST:", donor.last_donation_date)
        print("NEXT:", donor.next_eligible_date)
        db.session.commit()
        if donor.total_donations >= 20:
            donor.badge = "Diamond Donor"
        elif donor.total_donations >= 10:
            donor.badge = "Gold Donor"
        elif donor.total_donations >= 5:
            donor.badge = "Silver Donor"
        else:
            donor.badge = "Bronze Donor"

        donation = Donation(
            donor_id=donor.donor_id,
            patient_id=blood_request.patient_id,
            request_id=blood_request.request_id,
            donation_date=date.today(),
            units_donated=blood_request.units_needed
        )
        db.session.add(donation)

        reward = RewardPoint(
            donor_id=donor.donor_id,
            points=50,
            reason="Blood Donation"
        )
        db.session.add(reward)

        existing_badge = Badge.query.filter_by(
            donor_id=donor.donor_id,
            badge_name="First Donation"
        ).first()

        if existing_badge is None:
            db.session.add(
                Badge(
                    donor_id=donor.donor_id,
                    badge_name="First Donation",
                    badge_description="Completed first blood donation",
                    badge_icon="first_donation.png"
                )
            )

        blood_request.status = "Accepted"
        blood_request.updated_at = datetime.utcnow()
        blood_request.accepted_donor_id = donor.donor_id

        DonorMatch.query.filter(
            DonorMatch.request_id == match.request_id,
            DonorMatch.donor_response == "Pending",
            DonorMatch.match_id != match.match_id
        ).update(
    {"donor_response": "Rejected"},
            synchronize_session=False
        )

        if patient:
            create_notification({
                "user_id": patient.user_id,
                "message": f"A donor accepted your {blood_request.blood_group} blood request.",
                "type": "SUCCESS",
                "is_read": False,
                "related_request_id": blood_request.request_id,
                "related_match_id": match.match_id
            })
        create_notification({
    "user_id": donor.user_id,
    "message": "You accepted the blood request successfully.",
    "type": "SUCCESS",
    "is_read": False,
    "related_request_id": blood_request.request_id,
    "related_match_id": match.match_id
})

    # --------------------------------------------
    # REJECTED
    # --------------------------------------------
    elif response == "Rejected":

        if patient:

            create_notification({
                "user_id":
                    patient.user_id,
                "message":
                    (
                        "The selected donor rejected "
                        "your blood request. "
                        "The system is searching for "
                        "the next available donor."
                    ),
                "type":
                    "WARNING",
                "is_read":
                    False,
                "related_request_id":
                    blood_request.request_id,
                "related_match_id":
                    match.match_id
            })

        # Find and notify next eligible donor in queue
        next_donor_found = False
        from app.matching.services import is_donor_eligible, get_response_window

        while not next_donor_found:
            next_match = DonorMatch.query.filter(
                DonorMatch.request_id == match.request_id,
                DonorMatch.donor_response == "Pending",
                DonorMatch.response_deadline.is_(None)
            ).order_by(
                DonorMatch.ranking_score.desc()
            ).first()

            if next_match is None:
                break

            # Re-check current eligibility of next donor
            donor = next_match.donor
            if donor and is_donor_eligible(donor):
                # Eligible! Assign response window and notify
                response_minutes = get_response_window(blood_request.emergency_level)
                next_match.response_deadline = datetime.utcnow() + timedelta(minutes=response_minutes)

                create_notification({
                    "user_id": donor.user_id,
                    "message": (
                        f"New {blood_request.emergency_level} "
                        f"blood request for {blood_request.blood_group}. "
                        f"Please respond within {response_minutes} minutes."
                    ),
                    "type": "INFO",
                    "is_read": False,
                    "related_request_id": blood_request.request_id,
                    "related_match_id": next_match.match_id
                })
                next_donor_found = True
            else:
                # Not eligible anymore! Mark as Missed and continue loop to next pre-calculated match
                next_match.donor_response = "Missed"
                create_history({
                    "donor_id": next_match.donor_id,
                    "request_id": next_match.request_id,
                    "response_status": "Missed",
                    "response_time_seconds": 0,
                    "ai_score": next_match.ranking_score
                })

        if not next_donor_found:
            # No eligible donors left in queue
            blood_request.status = "Pending"
            # In case updated_at does not exist in request table, set it safely
            if hasattr(blood_request, 'updated_at'):
                blood_request.updated_at = datetime.utcnow()

            if patient:
                create_notification({
                    "user_id":
                        patient.user_id,
                    "message":
                        (
                            "No other eligible donor "
                            "is currently available."
                        ),
                    "type":
                        "WARNING",
                    "is_read":
                        False,
                    "related_request_id":
                        blood_request.request_id
                })
                    

    # --------------------------------------------
    # UPDATE RELIABILITY SCORE
    # --------------------------------------------

    current_score = (
        donor.reliability_score
        or 0
    )

    if response == "Accepted":

        if response_time_seconds <= 3600:

            current_score += 5

        else:

            current_score += 2

    elif response == "Rejected":

        current_score -= 5

    donor.reliability_score = max(

        0,

        min(

            100,

            current_score

        )

    )

    # --------------------------------------------
    # SAVE ALL CHANGES
    # --------------------------------------------

    db.session.commit()

    return jsonify({

        "message":
            f"Request {response.lower()} successfully",

        "match_id":
            match.match_id,

        "donor_response":
            match.donor_response,

        "request_status":
            blood_request.status,

        "reliability_score":
            donor.reliability_score

    }), 200