from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.hospital import Hospital
from app.models.blood_inventory import BloodInventory, BloodInventoryTransaction
from app.utils.security import role_required

hospital_bp = Blueprint(
    "hospital",
    __name__,
    url_prefix="/api/hospitals"
)

# Valid blood groups list
VALID_BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


# ==========================================
# GET HOSPITAL PROFILE
# ==========================================

@hospital_bp.route("/profile", methods=["GET"])
@jwt_required()
@role_required("HOSPITAL")
def profile():
    user_id = get_jwt_identity()
    hospital = Hospital.query.filter_by(user_id=user_id).first()

    if not hospital:
        return jsonify({
            "success": False,
            "message": "Hospital profile not found."
        }), 404

    return jsonify({
        "success": True,
        "hospital": hospital.to_dict()
    }), 200


# ==========================================
# GET HOSPITAL INVENTORY
# ==========================================

@hospital_bp.route("/inventory", methods=["GET"])
@jwt_required()
@role_required("HOSPITAL")
def get_inventory():
    user_id = get_jwt_identity()
    hospital = Hospital.query.filter_by(user_id=user_id).first()

    if not hospital:
        return jsonify({
            "success": False,
            "message": "Hospital profile not found."
        }), 404

    if not hospital.is_active:
        return jsonify({
            "success": False,
            "message": "Hospital is inactive."
        }), 400

    inventory_items = BloodInventory.query.filter_by(hospital_id=hospital.hospital_id).all()
    
    # Format and present inventory lists
    inventory_data = {item.blood_group: item.available_units for item in inventory_items}
    # Ensure all VALID_BLOOD_GROUPS are returned (default to 0 if not initialized)
    full_inventory = {bg: inventory_data.get(bg, 0) for bg in VALID_BLOOD_GROUPS}

    return jsonify({
        "success": True,
        "inventory": full_inventory,
        "items": [item.to_dict() for item in inventory_items]
    }), 200


# ==========================================
# POST ADJUST INVENTORY
# ==========================================

@hospital_bp.route("/inventory/adjust", methods=["POST"])
@jwt_required()
@role_required("HOSPITAL")
def adjust_inventory():
    user_id = get_jwt_identity()
    hospital = Hospital.query.filter_by(user_id=user_id).first()

    if not hospital:
        return jsonify({
            "success": False,
            "message": "Hospital profile not found."
        }), 404

    if not hospital.is_active:
        return jsonify({
            "success": False,
            "message": "Inactive hospital cannot modify inventory."
        }), 400

    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "message": "Request data is required."
        }), 400

    blood_group = data.get("blood_group")
    units = data.get("units")
    operation = data.get("operation") # "add" or "remove"

    # Validation Checks
    if not blood_group or blood_group not in VALID_BLOOD_GROUPS:
        return jsonify({
            "success": False,
            "message": "Invalid blood group."
        }), 400

    if units is None or not isinstance(units, int) or units <= 0:
        return jsonify({
            "success": False,
            "message": "Units must be a positive integer."
        }), 400

    if operation not in ["add", "remove"]:
        return jsonify({
            "success": False,
            "message": "Invalid operation type. Must be 'add' or 'remove'."
        }), 400

    # Retrieve or create inventory record atomically using transaction
    inventory = BloodInventory.query.filter_by(
        hospital_id=hospital.hospital_id,
        blood_group=blood_group
    ).with_for_update().first()

    if not inventory:
        if operation == "remove":
            return jsonify({
                "success": False,
                "message": "Cannot remove units. Current stock is 0."
            }), 400
        
        # Initialize
        inventory = BloodInventory(
            hospital_id=hospital.hospital_id,
            blood_group=blood_group,
            available_units=0
        )
        db.session.add(inventory)
        db.session.flush()

    # Modify stock levels
    if operation == "add":
        inventory.available_units += units
        t_type = "ADD"
    else:
        if inventory.available_units < units:
            return jsonify({
                "success": False,
                "message": "Available units cannot be negative."
            }), 400
        inventory.available_units -= units
        t_type = "REMOVE"

    # Save transaction record
    transaction = BloodInventoryTransaction(
        inventory_id=inventory.inventory_id,
        transaction_type=t_type,
        units=units
    )
    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Inventory updated successfully. New count: {inventory.available_units}",
        "blood_group": blood_group,
        "available_units": inventory.available_units
    }), 200


# ==========================================
# PUBLIC/PATIENT LIST HOSPITALS
# ==========================================

@hospital_bp.route("/", methods=["GET"])
@jwt_required()
def get_hospitals():
    """
    List all active hospitals for patients to select from.
    """
    all_hospitals = Hospital.query.filter_by(is_active=True).all()
    return jsonify([h.to_dict() for h in all_hospitals]), 200


# ==========================================
# GET INCOMING TRANSFERS
# ==========================================

@hospital_bp.route("/transfers/incoming", methods=["GET"])
@jwt_required()
@role_required("HOSPITAL")
def get_incoming_transfers():
    user_id = get_jwt_identity()
    hospital = Hospital.query.filter_by(user_id=user_id).first()
    if not hospital:
        return jsonify({"success": False, "message": "Hospital profile not found."}), 404
        
    from app.models.hospital_transfer import HospitalTransfer
    transfers = HospitalTransfer.query.filter_by(source_hospital_id=hospital.hospital_id).order_by(HospitalTransfer.created_at.desc()).all()
    
    return jsonify({
        "success": True,
        "transfers": [t.to_dict() for t in transfers]
    }), 200


# ==========================================
# GET OUTGOING TRANSFERS
# ==========================================

@hospital_bp.route("/transfers/outgoing", methods=["GET"])
@jwt_required()
@role_required("HOSPITAL")
def get_outgoing_transfers():
    user_id = get_jwt_identity()
    hospital = Hospital.query.filter_by(user_id=user_id).first()
    if not hospital:
        return jsonify({"success": False, "message": "Hospital profile not found."}), 404
        
    from app.models.hospital_transfer import HospitalTransfer
    transfers = HospitalTransfer.query.filter_by(destination_hospital_id=hospital.hospital_id).order_by(HospitalTransfer.created_at.desc()).all()
    
    return jsonify({
        "success": True,
        "transfers": [t.to_dict() for t in transfers]
    }), 200


# ==========================================
# POST APPROVE TRANSFER
# ==========================================

@hospital_bp.route("/transfers/<int:transfer_id>/approve", methods=["POST"])
@jwt_required()
@role_required("HOSPITAL")
def approve_transfer(transfer_id):
    user_id = get_jwt_identity()
    hospital = Hospital.query.filter_by(user_id=user_id).first()
    if not hospital:
        return jsonify({"success": False, "message": "Hospital profile not found."}), 404
        
    from app.models.hospital_transfer import HospitalTransfer
    transfer = HospitalTransfer.query.filter_by(transfer_id=transfer_id, source_hospital_id=hospital.hospital_id).first()
    if not transfer:
        return jsonify({"success": False, "message": "Transfer request not found."}), 404
        
    if transfer.status != "PENDING":
        return jsonify({"success": False, "message": f"Cannot approve transfer with status: {transfer.status}"}), 400
        
    # Lock source inventory row
    inventory = BloodInventory.query.filter_by(
        hospital_id=hospital.hospital_id,
        blood_group=transfer.blood_group
    ).with_for_update().first()
    
    if not inventory or inventory.available_units < transfer.units_requested:
        return jsonify({"success": False, "message": "Insufficient stock to fulfill transfer."}), 400
        
    try:
        # Deduct units from source
        inventory.available_units -= transfer.units_requested
        
        # Update transfer status
        transfer.status = "APPROVED"
        
        # Update blood request status
        blood_request = transfer.blood_request
        blood_request.status = "Completed"
        
        # Record source inventory transaction history
        transaction = BloodInventoryTransaction(
            inventory_id=inventory.inventory_id,
            request_id=blood_request.request_id,
            transaction_type="REMOVE",
            units=transfer.units_requested
        )
        db.session.add(transaction)
        
        # Send Notification to patient
        from app.notifications.services import create_notification
        create_notification({
            "user_id": blood_request.patient.user_id,
            "message": f"Your request for {blood_request.blood_group} has been fulfilled via transfer from {hospital.hospital_name}.",
            "type": "SUCCESS",
            "is_read": False,
            "related_request_id": blood_request.request_id
        })
        
        # Send Notification to destination hospital (requestor)
        create_notification({
            "user_id": blood_request.hospital.user.user_id,
            "message": f"Hospital {hospital.hospital_name} approved the transfer of {transfer.units_requested} units of {transfer.blood_group}.",
            "type": "SUCCESS",
            "is_read": False,
            "related_request_id": blood_request.request_id
        })
        
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Transfer approved and completed successfully.",
            "transfer": transfer.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# ==========================================
# POST REJECT TRANSFER
# ==========================================

@hospital_bp.route("/transfers/<int:transfer_id>/reject", methods=["POST"])
@jwt_required()
@role_required("HOSPITAL")
def reject_transfer(transfer_id):
    user_id = get_jwt_identity()
    hospital = Hospital.query.filter_by(user_id=user_id).first()
    if not hospital:
        return jsonify({"success": False, "message": "Hospital profile not found."}), 404
        
    from app.models.hospital_transfer import HospitalTransfer
    transfer = HospitalTransfer.query.filter_by(transfer_id=transfer_id, source_hospital_id=hospital.hospital_id).first()
    if not transfer:
        return jsonify({"success": False, "message": "Transfer request not found."}), 404
        
    if transfer.status != "PENDING":
        return jsonify({"success": False, "message": f"Cannot reject transfer with status: {transfer.status}"}), 400
        
    try:
        # Update transfer status
        transfer.status = "REJECTED"
        
        # Trigger fallback to donor matching
        blood_request = transfer.blood_request
        
        # Send Notification to patient
        from app.notifications.services import create_notification
        create_notification({
            "user_id": blood_request.patient.user_id,
            "message": f"Hospital transfer request rejected by {hospital.hospital_name}. Searching compatible donors...",
            "type": "WARNING",
            "is_read": False,
            "related_request_id": blood_request.request_id
        })
        
        # Send Notification to destination hospital (requestor)
        create_notification({
            "user_id": blood_request.hospital.user.user_id,
            "message": f"Hospital {hospital.hospital_name} rejected the transfer of {transfer.units_requested} units of {transfer.blood_group}.",
            "type": "WARNING",
            "is_read": False,
            "related_request_id": blood_request.request_id
        })
        
        from app.matching.services import find_matching_donors
        matches = find_matching_donors(blood_request)
        if matches:
            blood_request.status = "Matched"
        else:
            blood_request.status = "Pending"
            
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Transfer rejected. Switched request to donor matching fallback.",
            "transfer": transfer.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500