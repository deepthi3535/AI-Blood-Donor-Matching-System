from app import db

class EmailVerification(db.Model):
    __tablename__ = "email_verifications"

    verification_id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        nullable=False
    )

    otp_hash = db.Column(
        db.String(255),
        nullable=False
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    attempts = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    last_resend_at = db.Column(
        db.DateTime,
        nullable=True
    )

    def to_dict(self):
        return {
            "verification_id": self.verification_id,
            "user_id": self.user_id,
            "email": self.email,
            "expires_at": self.expires_at.strftime("%Y-%m-%d %H:%M:%S") if self.expires_at else None,
            "attempts": self.attempts,
            "verified": self.verified,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "last_resend_at": self.last_resend_at.strftime("%Y-%m-%d %H:%M:%S") if self.last_resend_at else None
        }
