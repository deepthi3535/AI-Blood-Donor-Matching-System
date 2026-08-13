from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.models.blood_request import BloodRequest
from app.models.donor_match import DonorMatch


matching_bp = Blueprint(
    "matching",
    __name__,
    url_prefix="/api/matching"
)


@matching_bp.route("/<int:request_id>", methods=["GET"])
@jwt_required()
def get_matches(request_id):
    from flask_jwt_extended import get_jwt_identity
    from app.models.patient import Patient
    from app.models.user import User

    blood_request = BloodRequest.query.get(request_id)

    if blood_request is None:
        return jsonify({
            "message": "Blood request not found"
        }), 404

    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    is_authorized = False
    patient = None
    if user.role == "ADMIN":
        is_authorized = True
    elif user.role == "PATIENT":
        patient = Patient.query.filter_by(user_id=user.user_id).first()
        if patient and blood_request.patient_id == patient.patient_id:
            is_authorized = True

    if not is_authorized:
        return jsonify({
            "message": "Forbidden: Access is denied"
        }), 403

    matches = DonorMatch.query.filter_by(
        request_id=request_id
    ).order_by(
        DonorMatch.ranking_score.desc()
    ).all()

    if not matches:

        return jsonify({
            "message": "No matching donors found"
        }), 404

    return jsonify({
    "request_id": blood_request.request_id,
    "blood_group": blood_request.blood_group,

    "hospital_name": blood_request.hospital_name,
    "hospital_latitude": blood_request.hospital_latitude,
    "hospital_longitude": blood_request.hospital_longitude,
    "emergency_level": blood_request.emergency_level,
    "status": blood_request.status,

    "total_matches": len(matches),

    "matched_donors": [
        {
            "donor": match.donor.to_dict(show_contact=(match.donor_response == "Accepted")),
            "distance_km": match.distance_km,
            "response_probability": match.response_probability,
            "ai_score": round(match.ranking_score, 2),
            "donor_response": match.donor_response,
            "response_deadline": match.response_deadline.strftime("%Y-%m-%d %H:%M:%S") if match.response_deadline else None,
            "match_id": match.match_id
        }
        for match in matches
    ]
}), 200