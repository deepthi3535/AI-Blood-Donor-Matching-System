from app import db

class BloodInventory(db.Model):
    __tablename__ = "blood_inventory"

    inventory_id = db.Column(
        db.Integer,
        primary_key=True
    )

    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitals.hospital_id"),
        nullable=False
    )

    blood_group = db.Column(
        db.String(5),
        nullable=False
    )

    available_units = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    last_updated = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # Relationship back to Hospital
    hospital = db.relationship("Hospital", backref=db.backref("inventory", lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (
        db.UniqueConstraint('hospital_id', 'blood_group', name='uq_hospital_blood_group'),
        db.CheckConstraint('available_units >= 0', name='check_positive_units'),
    )

    def to_dict(self):
        return {
            "inventory_id": self.inventory_id,
            "hospital_id": self.hospital_id,
            "blood_group": self.blood_group,
            "available_units": self.available_units,
            "last_updated": self.last_updated.strftime("%Y-%m-%d %H:%M:%S") if self.last_updated else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class BloodInventoryTransaction(db.Model):
    __tablename__ = "blood_inventory_transactions"

    transaction_id = db.Column(
        db.Integer,
        primary_key=True
    )

    inventory_id = db.Column(
        db.Integer,
        db.ForeignKey("blood_inventory.inventory_id"),
        nullable=False
    )

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("blood_requests.request_id"),
        nullable=True
    )

    transaction_type = db.Column(
        db.Enum("ADD", "REMOVE", "RESERVATION", "RELEASE", "FULFILLMENT"),
        nullable=False
    )

    units = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # Relationships
    inventory = db.relationship("BloodInventory", backref=db.backref("transactions", lazy=True, cascade="all, delete-orphan"))
    blood_request = db.relationship("BloodRequest", backref=db.backref("inventory_transactions", lazy=True))

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "inventory_id": self.inventory_id,
            "request_id": self.request_id,
            "transaction_type": self.transaction_type,
            "units": self.units,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }
