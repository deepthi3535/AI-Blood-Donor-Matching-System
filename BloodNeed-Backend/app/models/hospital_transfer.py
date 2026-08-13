from app import db

class HospitalTransfer(db.Model):
    __tablename__ = "hospital_transfers"

    transfer_id = db.Column(
        db.Integer,
        primary_key=True
    )

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("blood_requests.request_id"),
        nullable=False
    )

    source_hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitals.hospital_id"),
        nullable=False
    )

    destination_hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitals.hospital_id"),
        nullable=False
    )

    blood_group = db.Column(
        db.String(5),
        nullable=False
    )

    units_requested = db.Column(
        db.Integer,
        nullable=False
    )

    distance_km = db.Column(
        db.Float,
        nullable=False
    )

    status = db.Column(
        db.Enum("PENDING", "APPROVED", "REJECTED", "CANCELLED"),
        default="PENDING",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    # Relationships
    blood_request = db.relationship("BloodRequest", backref=db.backref("transfers", lazy=True, cascade="all, delete-orphan"))
    source_hospital = db.relationship("Hospital", foreign_keys=[source_hospital_id], backref=db.backref("outgoing_transfers", lazy=True))
    destination_hospital = db.relationship("Hospital", foreign_keys=[destination_hospital_id], backref=db.backref("incoming_transfers", lazy=True))

    def to_dict(self):
        return {
            "transfer_id": self.transfer_id,
            "request_id": self.request_id,
            "source_hospital_id": self.source_hospital_id,
            "source_hospital_name": self.source_hospital.hospital_name if self.source_hospital else None,
            "destination_hospital_id": self.destination_hospital_id,
            "destination_hospital_name": self.destination_hospital.hospital_name if self.destination_hospital else None,
            "blood_group": self.blood_group,
            "units_requested": self.units_requested,
            "distance_km": round(self.distance_km, 2),
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }
