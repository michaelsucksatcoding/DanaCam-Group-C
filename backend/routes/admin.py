from flask import Blueprint, jsonify, request

from models import ContactMessage, Loan, db

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/loans")
def get_all_loans():
    loans = Loan.query.order_by(Loan.created_at.desc()).all()
    return jsonify({"loans": [loan.to_dict() for loan in loans]})


@admin_bp.patch("/loans/<int:loan_id>/status")
def update_loan_status(loan_id: int):
    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip().lower()
    allowed_statuses = {"pending", "approved", "rejected", "paid"}

    if new_status not in allowed_statuses:
        return jsonify({"error": f"status must be one of {sorted(allowed_statuses)}"}), 400

    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({"error": "Loan not found"}), 404

    loan.status = new_status
    db.session.commit()

    return jsonify({"message": "Loan status updated", "loan": loan.to_dict()})


@admin_bp.get("/contacts")
def get_contact_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return jsonify({"contacts": [item.to_dict() for item in messages]})
