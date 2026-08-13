from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.hospital.services import (
    create_hospital,
    get_all_hospitals,
    get_hospital,
    update_hospital,
    delete_hospital
)

from app.schemas.hospital_schema import validate_hospital

hospital_bp = Blueprint(
    "hospital",
    __name__
)
@hospital_bp.route("/", methods=["GET"])
@jwt_required()
def hospitals():

    hospitals = get_all_hospitals()

    return jsonify([
        hospital.to_dict()
        for hospital in hospitals
    ])
@hospital_bp.route("/<int:hospital_id>", methods=["GET"])
@jwt_required()
def hospital(hospital_id):

    hospital = get_hospital(hospital_id)

    if not hospital:
        return jsonify({
            "message": "Hospital not found"
        }), 404

    return jsonify(hospital.to_dict())
@hospital_bp.route("/", methods=["POST"])
@jwt_required()
def add_hospital():

    data = request.get_json()

    valid, message = validate_hospital(data)

    if not valid:
        return jsonify({
            "message": message
        }), 400

    hospital = create_hospital(data)

    return jsonify(hospital.to_dict()), 201
@hospital_bp.route("/<int:hospital_id>", methods=["PUT"])
@jwt_required()
def edit_hospital(hospital_id):

    hospital = get_hospital(hospital_id)

    if not hospital:
        return jsonify({
            "message": "Hospital not found"
        }), 404

    hospital = update_hospital(
        hospital,
        request.get_json()
    )

    return jsonify(hospital.to_dict())
@hospital_bp.route("/<int:hospital_id>", methods=["DELETE"])
@jwt_required()
def remove_hospital(hospital_id):

    hospital = get_hospital(hospital_id)

    if not hospital:
        return jsonify({
            "message": "Hospital not found"
        }), 404

    delete_hospital(hospital)

    return jsonify({
        "message": "Hospital deleted successfully"
    })