from datetime import date, datetime

from flask import Blueprint, jsonify, request

from backend.models import ContactMessage, Loan, Payment, db
from backend.services_danacam import (
    compute_credit_score,
    compute_due_date,
    compute_late_fee_amount,
    compute_total_payable,
)


admin_bp = Blueprint("admin", __name__)


def _require_json_field(data: dict, key: str):
    value = data.get(key)
    if value is None:
        return None, jsonify({"error": f"{key} is required"}), 400
    return value, None, None


@admin_bp.get("/loans")
def get_all_loans():
    loans = Loan.query.order_by(Loan.created_at.desc()).all()
    return jsonify({"loans": [loan.to_dict() for loan in loans]})


@admin_bp.post("/loans/<int:loan_id>/verify")
def verify_loan(loan_id: int):
    """Stage 2: Verifikasi & Analisis (credit scoring simulation)."""
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({"error": "Loan not found"}), 404

    user = loan.user
    if not user:
        return jsonify({"error": "User not found for this loan"}), 404

    # Deterministic credit scoring simulation
    result = compute_credit_score(
        phone=user.phone,
        ktp_number=user.ktp_number,
        amount=loan.amount,
    )

    loan.credit_score = result.score
    loan.verification_notes = result.notes
    loan.is_eligible = bool(result.eligible)

    # Eligible loans can proceed to stage 3 approval (disbursement).
    # Ineligible loans are rejected immediately.
    if loan.is_eligible:
        loan.status = "pending"
    else:
        loan.status = "rejected"
        loan.rejected_reason = (
            loan.verification_notes
            or "Not eligible based on simulated credit scoring"
        )

    db.session.commit()

    return (
        jsonify(
            {
                "message": "Loan verified (simulated)",
                "loan": loan.to_dict(),
                "credit_scoring": result.__dict__,
            }
        ),
        200,
    )


@admin_bp.post("/loans/<int:loan_id>/approve")
def approve_loan(loan_id: int):
    """Stage 3: Persetujuan & Pencairan Dana.

    If eligible, simulate disbursal (bank/e-wallet) and set due date + total payable.
    """
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({"error": "Loan not found"}), 404

    data = request.get_json(silent=True) or {}

    disbursement_to = (data.get("disbursement_to") or "").strip().lower()  # bank / ewallet
    disbursement_account = (data.get("disbursement_account") or "").strip()

    if not disbursement_to or disbursement_to not in {"bank", "ewallet"}:
        return jsonify({"error": "disbursement_to must be 'bank' or 'ewallet'"}), 400
    if not disbursement_account:
        return jsonify({"error": "disbursement_account is required"}), 400

    if not loan.is_eligible:
        loan.status = "rejected"
        loan.rejected_reason = "Not eligible based on simulated credit scoring"
        db.session.commit()
        return jsonify({"message": "Loan rejected (not eligible)", "loan": loan.to_dict()}), 200

    approved_at = datetime.utcnow()
    loan.approved_at = approved_at
    loan.disbursement_to = disbursement_to
    loan.disbursement_account = disbursement_account
    loan.disbursed_at = approved_at

    loan.due_date = compute_due_date(approved_at=approved_at, term_months=loan.term_months)
    loan.total_payable = compute_total_payable(principal=loan.amount, term_months=loan.term_months)
    loan.late_fee_amount = 0.0
    loan.last_late_fee_applied_at = None

    loan.status = "disbursed"
    db.session.commit()

    return jsonify({"message": "Loan approved + disbursed (simulated)", "loan": loan.to_dict()}), 200


@admin_bp.post("/loans/<int:loan_id>/reject")
def reject_loan(loan_id: int):
    """Explicit rejection for stage 3."""
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({"error": "Loan not found"}), 404

    data = request.get_json(silent=True) or {}
    reason = (data.get("reason") or "").strip() or "Rejected by admin"

    loan.status = "rejected"
    loan.rejected_reason = reason
    db.session.commit()

    return jsonify({"message": "Loan rejected", "loan": loan.to_dict()}), 200


@admin_bp.post("/overdue/settle")
def settle_overdue():
    """Stage 4 automation: calculate and apply late fees for overdue loans.

    Idempotency strategy:
    - Only apply late fee once per calendar date using last_late_fee_applied_at.
    - If already applied today, do nothing.
    """
    today = date.today()

    loans = Loan.query.filter(Loan.status == "disbursed").all()

    settled = []
    for loan in loans:
        if not loan.due_date:
            continue
        if loan.paid_at is not None:
            continue

        # Already applied fee today => skip
        if loan.last_late_fee_applied_at and loan.last_late_fee_applied_at.date() == today:
            continue

        if today <= loan.due_date:
            continue

        late_fee = compute_late_fee_amount(
            principal=loan.amount,
            due_date=loan.due_date,
            now=today,
        )

        if late_fee > 0:
            loan.late_fee_amount = float(late_fee)
            loan.total_payable = float(loan.total_payable or 0.0) + float(late_fee)
            loan.last_late_fee_applied_at = datetime.utcnow()
            loan.status = "overdue"

            payment = Payment(
                loan_id=loan.id,
                amount_paid=0.0,
                late_fee_applied=float(late_fee),
                is_late_payment=True,
                notes="late-fee-automation",
            )
            db.session.add(payment)
            db.session.commit()

            settled.append({"loan_id": loan.id, "late_fee_applied": late_fee})

    return jsonify({"message": "Overdue settlement done (simulated)", "settled": settled}), 200


# Legacy endpoint kept for backward compatibility (old frontend/admin usage)
@admin_bp.patch("/loans/<int:loan_id>/status")
def update_loan_status(loan_id: int):
    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip().lower()
    allowed_statuses = {"pending", "under_review", "approved", "disbursed", "rejected", "paid", "overdue"}

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

