from datetime import datetime, timedelta, date

from app import db
from app.models.donor import Donor
from app.models.donor_match import DonorMatch
from app.models.response_history import ResponseHistory
from app.models.blood_request import BloodRequest
from app.models.donation import Donation
from app.models.reward_point import RewardPoint
from app.models.badge import Badge

from app.notifications.services import create_notification

from app.matching.services import get_response_window



# ==========================================
# GET MATCH
# ==========================================

def get_match(match_id, user_id):

    return (
        DonorMatch.query
        .join(Donor)
        .filter(
            DonorMatch.match_id == match_id,
            Donor.user_id == user_id
        )
        .first()
    )

# ==========================================
# SAVE RESPONSE HISTORY
# ==========================================

def save_history(match, status, response_time_seconds=0):

    history = ResponseHistory(

        donor_id=match.donor_id,

        request_id=match.request_id,

        response_status=status,

        response_time_seconds=response_time_seconds,

        ai_score=match.ranking_score

    )

    db.session.add(history)


# ==========================================
# ACCEPT REQUEST
# ==========================================

def accept_request(match_id, user_id):

    match = get_match(match_id, user_id)

    if match is None:

        return None


    # Check deadline

    if (

        match.response_deadline

        and datetime.utcnow()

        > match.response_deadline

    ):

        return None


    # Only pending match can be accepted

    if match.donor_response != "Pending":

        return None


    # Accept current donor

    match.donor_response = "Accepted"
    donor = match.donor

    # Update donor statistics
    donor.total_donations += 1

    # Last donation date
    donor.last_donation_date = date.today()

    # Reliability score
    donor.reliability_score = min(
        donor.reliability_score + 5,
        100
    )

    # -----------------------------
    # Donation History
    # -----------------------------
    donation = Donation(
        donor_id=donor.donor_id,
        request_id=match.request_id,
        donation_date=date.today(),
        units_donated=1
    )

    db.session.add(donation)

    # -----------------------------
    # Reward Points
    # -----------------------------
    reward = RewardPoint(
        donor_id=donor.donor_id,
        points=50,
        reason="Blood Donation"
    )

    db.session.add(reward)

    # -----------------------------
    # First Donation Badge
    # -----------------------------
    badge_exists = Badge.query.filter_by(
        donor_id=donor.donor_id,
        badge_name="First Donation"
    ).first()

    if badge_exists is None:

        badge = Badge(
            donor_id=donor.donor_id,
            badge_name="First Donation",
            badge_description="Completed first blood donation"
        )

        db.session.add(badge)

    # Reliability score
    donor.reliability_score = min(
        donor.reliability_score + 5,
        100
    )

    blood_request = (

        BloodRequest.query.get(

            match.request_id

        )

    )

    if blood_request:

        blood_request.status = "Accepted"
        patient = blood_request.patient

        if patient:

            create_notification({

                "user_id": patient.user_id,

                "title": "Blood Donor Accepted",

                "message":
                    f"A donor has accepted your blood request "
                    f"for {blood_request.blood_group}.",

                "notification_type": "SUCCESS",

                "related_request_id": blood_request.request_id

            })


    # Reject all other pending donors

    other_matches = DonorMatch.query.filter(

        DonorMatch.request_id

        == match.request_id,

        DonorMatch.match_id

        != match.match_id,

        DonorMatch.donor_response

        == "Pending"

    ).all()


    for other_match in other_matches:

        other_match.donor_response = "Rejected"


    # Save history

    save_history(

        match,

        "Accepted"

    )


    db.session.commit()


    return match


# ==========================================
# REJECT REQUEST
# ==========================================

def reject_request(match_id, user_id):

    match = get_match(match_id, user_id)

    if match is None:

        return None


    if match.donor_response != "Pending":

        return None


    match.donor_response = "Rejected"


    save_history(

        match,

        "Rejected"

    )


    # Find and notify next donor

    next_match = notify_next_donor(match)


    db.session.commit()


    return match


# ==========================================
# NOTIFY NEXT DONOR
# ==========================================

def notify_next_donor(current_match):

    next_match = (

        DonorMatch.query.filter(

            DonorMatch.request_id

            == current_match.request_id,

            DonorMatch.donor_response

            == "Pending",

            DonorMatch.match_id

            != current_match.match_id

        )

        .order_by(

            DonorMatch.ranking_score.desc()

        )

        .first()

    )


    if next_match is None:

        return None


    blood_request = (

        BloodRequest.query.get(

            current_match.request_id

        )

    )


    if blood_request is None:

        return None


    response_minutes = (

        get_response_window(

            blood_request.emergency_level

        )

    )


    next_match.response_deadline = (

        datetime.utcnow()

        + timedelta(

            minutes=response_minutes

        )

    )


    donor = next_match.donor


    if donor:

        create_notification({

    "user_id": donor.user_id,

    "title": "New Blood Request",

    "message":
        f"{blood_request.emergency_level} blood request for "
        f"{blood_request.blood_group}. "
        f"Please respond within {response_minutes} minutes.",

    "notification_type": "INFO",

    

})


    return next_match


# ==========================================
# PROCESS EXPIRED MATCHES
# ==========================================

def process_expired_matches():

    now = datetime.utcnow()


    expired_matches = (

        DonorMatch.query.filter(

            DonorMatch.donor_response

            == "Pending",

            DonorMatch.response_deadline

            <= now

        )

        .order_by(

            DonorMatch.ranking_score.desc()

        )

        .all()

    )


    processed = []


    for match in expired_matches:

        # Mark as missed

        match.donor_response = "Missed"


        # Save valid enum value

        save_history(

            match,

            "Missed"

        )


        # Move to next donor

        next_match = notify_next_donor(match)
        blood_request = BloodRequest.query.get(match.request_id)

        if blood_request:

            patient = blood_request.patient

            if patient:

                create_notification({

                    "user_id": patient.user_id,

                    "title": "Searching Next Donor",

                    "message":
                        "The previous donor declined your request. "
                        "AI is notifying the next best donor.",

                    "notification_type": "INFO",

                    "related_request_id": blood_request.request_id

                })


                processed.append({

                    "expired_match_id":

                        match.match_id,

                    "next_match_id":

                        next_match.match_id

                        if next_match

                        else None

                })

    db.session.commit()

    return processed