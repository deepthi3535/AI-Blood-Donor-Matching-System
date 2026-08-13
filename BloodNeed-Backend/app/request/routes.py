from urllib import response

from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from app import db

from app.models.patient import Patient
from app.models.donor_match import DonorMatch
from app.models.hospital import Hospital
from app.models.blood_inventory import BloodInventory, BloodInventoryTransaction

from app.matching.services import find_matching_donors

from app.request.services import (
    create_request,
    get_all_requests,
    get_request,
    update_request,
    delete_request,
    complete_request
)

from app.schemas.request_schema import validate_request
from app.utils.security import role_required


request_bp = Blueprint(
    "request",
    __name__,
    url_prefix="/api/requests"
)


# ====================================================
# GET MY BLOOD REQUESTS
# ====================================================

@request_bp.route("/", methods=["GET"])
@jwt_required()
@role_required("PATIENT")
def requests():

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:

        return jsonify({
            "message": "Patient profile not found"
        }), 404

    requests = get_all_requests()

    patient_requests = [

        req

        for req in requests

        if req.patient_id == patient.patient_id

    ]

    response = []

    for req in patient_requests:

        request_data = req.to_dict()

        matches = DonorMatch.query.filter_by(
            request_id=req.request_id
        ).all()

        request_data["matched_donors"] = [

            {
                "donor": match.donor.to_dict(show_contact=(match.donor_response == "Accepted")),
                "distance_km": match.distance_km,
                "response_probability": match.response_probability,
                "ai_score": match.ranking_score,
                "donor_response": match.donor_response
            }

            for match in matches

        ]

        response.append(request_data)

    return jsonify(response), 200


# ====================================================
# GET SINGLE BLOOD REQUEST
# ====================================================

@request_bp.route(
    "/<int:request_id>",
    methods=["GET"]
)
@jwt_required()
@role_required("PATIENT")
def request_details(request_id):

    req = get_request(request_id)

    if req is None:

        return jsonify({
            "message": "Blood request not found"
        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:

        return jsonify({
            "message": "Patient profile not found"
        }), 404

    if req.patient_id != patient.patient_id:

        return jsonify({
            "message": "Unauthorized"
        }), 403

    return jsonify(
        req.to_dict()
    ), 200


# ====================================================
# CREATE BLOOD REQUEST
# ====================================================

@request_bp.route("/", methods=["POST"])
@jwt_required()
@role_required("PATIENT")
def add_request():

    data = request.get_json()

    if not data:

        return jsonify({
            "message": "Request data is required"
        }), 400

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:

        return jsonify({
            "message": "Patient profile not found"
        }), 404

    # Automatically assign logged-in patient
    data["patient_id"] = patient.patient_id

    # Validate request data
    valid, message = validate_request(data)

    if not valid:

        return jsonify({
            "message": message
        }), 400

    # Create blood request
    req = create_request(data)

    if req is None:

        return jsonify({
            "message": "Failed to create blood request"
        }), 400

    # ====================================================
    # HOSPITAL BLOOD INVENTORY CHECK
    # ====================================================
    if req.hospital_id:
        inventory = BloodInventory.query.filter_by(
            hospital_id=req.hospital_id,
            blood_group=req.blood_group
        ).with_for_update().first()

        if inventory and inventory.available_units >= req.units_needed:
            # Atomic subtraction
            inventory.available_units -= req.units_needed
            
            # Save transaction
            transaction = BloodInventoryTransaction(
                inventory_id=inventory.inventory_id,
                request_id=req.request_id,
                transaction_type="FULFILLMENT",
                units=req.units_needed
            )
            db.session.add(transaction)

            # Mark request as Completed
            req.status = "Completed"
            db.session.commit()

            return jsonify({
                "message": f"Blood request fulfilled immediately from {req.hospital_name} stock!",
                "success": True,
                "request": req.to_dict()
            }), 201

    # ====================================================
    # FALLBACK: START AI MATCHING
    # ====================================================
    matches = find_matching_donors(req)

    if matches:

        req.status = "Matched"

        message = (
            "Blood request created successfully. "
            "Matching started and the top-ranked donor was notified."
        )

    else:

        req.status = "Pending"

        message = (
            "Blood request created successfully, "
            "but no eligible donor was found."
        )

    db.session.commit()

    response_data = req.to_dict()
    response_data["message"] = message
    response_data["donor_notified"] = len(matches) > 0

    return jsonify(response_data), 201


# ====================================================
# UPDATE BLOOD REQUEST
# ====================================================

@request_bp.route(
    "/<int:request_id>",
    methods=["PUT"]
)
@jwt_required()
@role_required("PATIENT")
def edit_request(request_id):

    req = get_request(request_id)

    if req is None:

        return jsonify({
            "message": "Blood request not found"
        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:

        return jsonify({
            "message": "Patient profile not found"
        }), 404

    if req.patient_id != patient.patient_id:

        return jsonify({
            "message": "Unauthorized"
        }), 403

    # Do not modify completed or accepted requests
    if req.status in [

        "Accepted",

        "Completed",

        "Cancelled"

    ]:

        return jsonify({

            "message":
                "This request cannot be modified now"

        }), 400

    data = request.get_json()

    if not data:

        return jsonify({

            "message":
                "Update data is required"

        }), 400

    # Validate updated data
    valid, message = validate_request({

        **data,

        "patient_id":
            patient.patient_id

    })

    if not valid:

        return jsonify({

            "message":
                message

        }), 400

    req = update_request(

        req,

        data

    )

    return jsonify(

        req.to_dict()

    ), 200


# ====================================================
# DELETE BLOOD REQUEST
# ====================================================

@request_bp.route(
    "/<int:request_id>",
    methods=["DELETE"]
)
@jwt_required()
@role_required("PATIENT")
def remove_request(request_id):

    req = get_request(request_id)

    if req is None:

        return jsonify({

            "message":
                "Blood request not found"

        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(

        user_id=user_id

    ).first()

    if patient is None:

        return jsonify({

            "message":
                "Patient profile not found"

        }), 404

    if req.patient_id != patient.patient_id:

        return jsonify({

            "message":
                "Unauthorized"

        }), 403

    if req.status == "Completed":

        return jsonify({

            "message":
                "Completed request cannot be deleted"

        }), 400

    # Remove pending matches first
    DonorMatch.query.filter_by(

        request_id=req.request_id

    ).delete(

        synchronize_session=False

    )

    delete_request(req)

    return jsonify({

        "message":
            "Blood request deleted successfully"

    }), 200


# ====================================================
# CANCEL BLOOD REQUEST
# ====================================================

@request_bp.route(
    "/<int:request_id>/cancel",
    methods=["PATCH"]
)
@jwt_required()
@role_required("PATIENT")
def cancel_request(request_id):

    req = get_request(request_id)

    if req is None:

        return jsonify({

            "message":
                "Blood request not found"

        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(

        user_id=user_id

    ).first()

    if patient is None:

        return jsonify({

            "message":
                "Patient profile not found"

        }), 404

    if req.patient_id != patient.patient_id:

        return jsonify({

            "message":
                "Unauthorized"

        }), 403

    if req.status == "Cancelled":

        return jsonify({

            "message":
                "Request already cancelled"

        }), 400

    if req.status == "Completed":

        return jsonify({

            "message":
                "Completed request cannot be cancelled"

        }), 400

    # Cancel request
    req.status = "Cancelled"

    # Cancel all pending donor matches
    DonorMatch.query.filter_by(

        request_id=req.request_id,

        donor_response="Pending"

    ).update({

        "donor_response":
            "Rejected"

    })

    db.session.commit()

    return jsonify({

        "message":
            "Blood request cancelled successfully",

        "status":
            req.status

    }), 200


# ====================================================
# GET REQUEST STATUS
# ====================================================

@request_bp.route(
    "/<int:request_id>/status",
    methods=["GET"]
)
@jwt_required()
@role_required("PATIENT")
def request_status(request_id):

    req = get_request(request_id)

    if req is None:

        return jsonify({

            "message":
                "Blood request not found"

        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(

        user_id=user_id

    ).first()

    if patient is None:

        return jsonify({

            "message":
                "Patient profile not found"

        }), 404

    if req.patient_id != patient.patient_id:

        return jsonify({

            "message":
                "Unauthorized"

        }), 403

    return jsonify({

        "request_id":
            req.request_id,

        "status":
            req.status,

        "emergency_level":
            req.emergency_level

    }), 200

# ====================================================
# COMPLETE BLOOD REQUEST
# ====================================================
# ====================================================
# COMPLETE BLOOD REQUEST
# ====================================================

@request_bp.route(
    "/<int:request_id>/complete",
    methods=["PATCH"]
)
@jwt_required()
@role_required("PATIENT")
def complete_blood_request(request_id):

    req = get_request(request_id)

    if req is None:
        return jsonify({
            "message": "Blood request not found"
        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:
        return jsonify({
            "message": "Patient profile not found"
        }), 404

    if req.patient_id != patient.patient_id:
        return jsonify({
            "message": "Unauthorized"
        }), 403

    result = complete_request(request_id)

    if result is None:
        return jsonify({
            "message": "Blood request not found"
        }), 404

    if result is False:
        return jsonify({
            "message": "No accepted donor found for this request"
        }), 400


    return jsonify({
        "message": "Blood request completed successfully",
        "status": result.status
    }), 200
# ====================================================
# MANUAL MATCHING
# ====================================================

@request_bp.route(
    "/<int:request_id>/match",
    methods=["POST"]
)
@jwt_required()
@role_required("PATIENT")
def trigger_matching(request_id):

    req = get_request(request_id)

    if req is None:

        return jsonify({

            "message":
                "Blood request not found"

        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(

        user_id=user_id

    ).first()

    if patient is None:

        return jsonify({

            "message":
                "Patient profile not found"

        }), 404

    if req.patient_id != patient.patient_id:

        return jsonify({

            "message":
                "Unauthorized"

        }), 403

    if req.status in [

        "Cancelled",

        "Completed",

        "Accepted"

    ]:

        return jsonify({

            "message":
                "Matching cannot be started for this request"

        }), 400

    # Check whether an active donor is already responding
    existing_pending_match = (

        DonorMatch.query.filter_by(

            request_id=request_id,

            donor_response="Pending"

        ).first()

    )

    if existing_pending_match:

        return jsonify({

            "message":
                "An active donor match already exists",

            "match_id":
                existing_pending_match.match_id

        }), 400

    # Start matching
    matches = find_matching_donors(req)

    if not matches:

        req.status = "Pending"

        db.session.commit()

        return jsonify({

            "message":
                "No eligible matching donors found",

            "status":
                req.status

        }), 404

    req.status = "Matched"

    db.session.commit()

    return jsonify({

        "message":
            "AI matching started successfully",

        "request_id":
            req.request_id,

        "donor_notified":
            True,

        "status":
            req.status

    }), 200