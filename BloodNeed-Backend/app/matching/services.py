from datetime import date, datetime, timedelta
from turtle import distance

from app import db

from app.models.donor import Donor
from app.models.donor_match import DonorMatch
from app.models.patient import Patient
from app.models.user import User

from app.notifications.services import create_notification

from app.ai.ranking import (
    calculate_score,
    calculate_distance,
    allowed_radius
)


# ==========================================
# DONATION COOLDOWN
# ==========================================

DONATION_COOLDOWN_DAYS = 90


# ==========================================
# RESPONSE TIME BASED ON EMERGENCY
# ==========================================
def get_response_window(emergency_level):

    if emergency_level == "CRITICAL":
        return 15

    elif emergency_level == "HIGH":
        return 30

    elif emergency_level == "MEDIUM":
        return 60

    else:
        return 120



# ==========================================
# CHECK DONOR ELIGIBILITY
# ==========================================

def is_donor_eligible(donor):
    # Donor must be available
    if donor.availability is not True:
        return False

    # Check User account status
    user = User.query.get(donor.user_id)
    if not user or not user.active:
        return False

    # Valid location coordinates
    if donor.latitude is None or donor.longitude is None:
        return False

    # Donor cooldown period (90 days)
    if donor.last_donation_date:
        eligible_date = (
            donor.last_donation_date
            + timedelta(
                days=DONATION_COOLDOWN_DAYS
            )
        )
        if date.today() < eligible_date:
            return False

    # Donor next eligible date check
    if donor.next_eligible_date:
        if date.today() < donor.next_eligible_date:
            return False

    # Check for active conflicting pending match
    active_match = DonorMatch.query.filter(
        DonorMatch.donor_id == donor.donor_id,
        DonorMatch.donor_response == "Pending",
        DonorMatch.response_deadline.isnot(None),
        DonorMatch.response_deadline > datetime.utcnow()
    ).first()
    if active_match:
        return False

    return True


# ==========================================
# FIND MATCHING DONORS
# ==========================================

def find_matching_donors(blood_request):
    print("Request Blood:", blood_request.blood_group)
    print("Hospital Lat:", blood_request.hospital_latitude)
    print("Hospital Lon:", blood_request.hospital_longitude)

    # --------------------------------------
    # Remove old matches
    # --------------------------------------

    DonorMatch.query.filter_by(
        request_id=blood_request.request_id
    ).delete(
        synchronize_session=False
    )

    db.session.commit()


    # --------------------------------------
    # Get all donors
    # --------------------------------------

    donors = Donor.query.all()

    matched = []


    # --------------------------------------
    # Filter and rank donors
    # --------------------------------------

    for donor in donors:
        print("--------------------------------")
        print("Donor:", donor.donor_id)
        print("Blood:", donor.blood_group)
        print("Available:", donor.availability)
        print("Lat:", donor.latitude)
        print("Lon:", donor.longitude)

        score = calculate_score(blood_request, donor)

        print("Score:", score)

        if not is_donor_eligible(donor):
            continue

        score = calculate_score(
            blood_request,
            donor
        )


        if score <= 0:
            continue

        # Distance calculation only if both donor and hospital coordinates exist
        if (
            donor.latitude is not None
            and donor.longitude is not None
            and blood_request.hospital_latitude is not None
            and blood_request.hospital_longitude is not None
        ):

            distance = calculate_distance(
                donor.latitude,
                donor.longitude,
                blood_request.hospital_latitude,
                blood_request.hospital_longitude
            )

            MAX_DISTANCE_KM = allowed_radius(blood_request.emergency_level)

            if distance > MAX_DISTANCE_KM:
                continue

        else:
            # Coordinates unavailable
            distance = 0

        response_probability = round(
            min(
                100,
                (donor.reliability_score * 0.7)
                + (donor.total_donations * 3)
            ),
            2
        )

        matched.append({
            "donor": donor,
            "score": score,
            "distance": distance,
            "probability": response_probability
        })

    # --------------------------------------
    # Sort donors by ranking score
    # --------------------------------------

    matched.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    # No eligible donors
    if not matched:
        return []

    # --------------------------------------
    # Response time based on emergency
    # --------------------------------------

    response_minutes = get_response_window(
        blood_request.emergency_level
    )

    now = datetime.utcnow()

    # ==========================================
    # CREATE MATCH RECORDS FOR ALL DONORS
    # ==========================================

    matched = matched[:10]

    for index, item in enumerate(matched):
        donor = item["donor"]

        # Only first donor gets active timer
        if index == 0:
            response_deadline = (
                now + timedelta(minutes=response_minutes)
            )
        else:
            # Future donors are waiting
            response_deadline = None

        match = DonorMatch(
            request_id=blood_request.request_id,
            donor_id=donor.donor_id,
            distance_km=item["distance"],
            response_probability=item["probability"],
            ranking_score=item["score"],
            donor_response="Pending",
            response_deadline=response_deadline
        )

        db.session.add(match)

        # --------------------------------------
        # Notify ONLY first-ranked donor
        # --------------------------------------
        if index == 0:
            patient = Patient.query.get(blood_request.patient_id)
            user = User.query.get(patient.user_id) if patient else None

            if user:
                create_notification({
                    "user_id": donor.user_id,
                    "title": "New Blood Request",
                    "message": (
                        f"{user.full_name} needs "
                        f"{blood_request.blood_group} blood at "
                        f"{blood_request.hospital_name}. "
                        f"Please respond within "
                        f"{response_minutes} minutes."
                    ),
                    "notification_type": "INFO",
                    "is_read": False
                })

    db.session.commit()

    return matched