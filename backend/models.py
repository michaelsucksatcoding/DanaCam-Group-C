from datetime import datetime, date

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    ktp_number = db.Column(db.String(32), nullable=True, index=True)
    selfie_filename = db.Column(db.String(255), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    loans = db.relationship("Loan", backref="user", lazy=True, cascade="all, delete-orphan")
    contacts = db.relationship(
        "ContactMessage",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )
    reviews = db.relationship("Review", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "ktp_number": self.ktp_number,
            "selfie_filename": self.selfie_filename,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat(),
        }



class Loan(db.Model):
    __tablename__ = "loans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Stage 1 (Pengajuan) fields
    amount = db.Column(db.Float, nullable=False)  # principal amount
    term_months = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.Text, nullable=False)

    # Stage 2 (Verifikasi & Analisis)
    status = db.Column(db.String(20), default="pending", nullable=False)
    credit_score = db.Column(db.Integer, nullable=True)
    verification_notes = db.Column(db.Text, nullable=True)
    is_eligible = db.Column(db.Boolean, default=False, nullable=False)

    # Stage 3 (Persetujuan & Pencairan Dana)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_reason = db.Column(db.Text, nullable=True)
    disbursed_at = db.Column(db.DateTime, nullable=True)
    disbursement_to = db.Column(db.String(20), nullable=True)  # bank / ewallet
    disbursement_account = db.Column(db.String(80), nullable=True)

    # Repayment / Settlement (Pembayaran / Pelunasan)
    due_date = db.Column(db.Date, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    late_fee_amount = db.Column(db.Float, default=0.0, nullable=False)
    total_payable = db.Column(db.Float, default=0.0, nullable=False)
    last_late_fee_applied_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "term_months": self.term_months,
            "purpose": self.purpose,
            "status": self.status,
            "credit_score": self.credit_score,
            "is_eligible": self.is_eligible,
            "verification_notes": self.verification_notes,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_reason": self.rejected_reason,
            "disbursed_at": self.disbursed_at.isoformat() if self.disbursed_at else None,
            "disbursement_to": self.disbursement_to,
            "disbursement_account": self.disbursement_account,
            "due_date": self.due_date.isoformat() if isinstance(self.due_date, date) and self.due_date else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "late_fee_amount": self.late_fee_amount,
            "total_payable": self.total_payable,
            "created_at": self.created_at.isoformat(),
        }


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loans.id"), nullable=False, index=True)
    amount_paid = db.Column(db.Float, nullable=False)
    late_fee_applied = db.Column(db.Float, default=0.0, nullable=False)
    is_late_payment = db.Column(db.Boolean, default=False, nullable=False)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "loan_id": self.loan_id,
            "amount_paid": self.amount_paid,
            "late_fee_applied": self.late_fee_applied,
            "is_late_payment": self.is_late_payment,
            "paid_at": self.paid_at.isoformat(),
            "notes": self.notes,
        }



class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
        }






class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    reviewer_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), default="Pengguna", nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "reviewer_name": self.reviewer_name,
            "role": self.role,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
        }

