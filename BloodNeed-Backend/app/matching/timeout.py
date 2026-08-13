from datetime import datetime, timedelta

from app import db

from app.models.donor import Donor
from app.models.donor_match import DonorMatch
from app.models.blood_request import BloodRequest

from app.response_history.services import create_history
from app.notifications.services import create_notification

from app.matching.services import (
    is_donor_eligible,
    get_response_window
)


# ==========================================
# PROCESS EXPIRED DONOR MATCHES
# ==========================================

def process_expired_matches():
    now = datetime.utcnow()

    expired_matches = DonorMatch.query.filter(
        DonorMatch.donor_response == "Pending",
        DonorMatch.response_deadline <= now
    ).all()

    processed = []

    for match in expired_matches:
        # Get blood request
        blood_request = BloodRequest.query.get(match.request_id)
        if blood_request is None:
            continue

        # Mark current donor as Missed
        match.donor_response = "Missed"

        create_history({
            "donor_id": match.donor_id,
            "request_id": match.request_id,
            "response_status": "Missed",
            "response_time_seconds": 0,
            "ai_score": match.ranking_score
        })

        # Find and notify next eligible donor in queue
        next_donor_found = False
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
                next_match.response_deadline = now + timedelta(minutes=response_minutes)

                create_notification({
                    "user_id": donor.user_id,
                    "title": "New Blood Request",
                    "message": (
                        f"{blood_request.emergency_level} blood request for "
                        f"{blood_request.blood_group}. "
                        f"Please respond within {response_minutes} minutes."
                    ),
                    "notification_type": "INFO",
                    "related_request_id": blood_request.request_id
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
            patient = blood_request.patient
            if patient:
                create_notification({
                    "user_id": patient.user_id,
                    "title": "Searching Next Donor",
                    "message": "No other eligible donor is currently available.",
                    "notification_type": "WARNING",
                    "related_request_id": blood_request.request_id
                })

        processed.append(match.match_id)

    db.session.commit()

    return processed


# ==========================================
# PROCESS EXPIRED TRANSFERS
# ==========================================

def process_expired_transfers():
    from app.models.hospital_transfer import HospitalTransfer
    from app.matching.services import find_matching_donors
    
    now = datetime.utcnow()
    pending_transfers = HospitalTransfer.query.filter_by(status="PENDING").all()
    
    for transfer in pending_transfers:
        blood_request = transfer.blood_request
        if not blood_request:
            continue
        
        limit_minutes = 5 if blood_request.emergency_level == "CRITICAL" else 15
        if now - transfer.created_at >= timedelta(minutes=limit_minutes):
            transfer.status = "REJECTED"
            
            # Notify patient
            create_notification({
                "user_id": blood_request.patient.user_id,
                "message": f"Nearby hospital transfer request timed out. Sourcing compatible donors...",
                "type": "WARNING",
                "is_read": False,
                "related_request_id": blood_request.request_id
            })
            
            # Notify source hospital
            create_notification({
                "user_id": transfer.source_hospital.user.user_id,
                "message": f"Transfer request for {transfer.blood_group} to {blood_request.hospital_name} expired.",
                "type": "WARNING",
                "is_read": False,
                "related_request_id": blood_request.request_id
            })
            
            # Fallback to donor matching
            matches = find_matching_donors(blood_request)
            if matches:
                blood_request.status = "Matched"
            else:
                blood_request.status = "Pending"
                
    db.session.commit()