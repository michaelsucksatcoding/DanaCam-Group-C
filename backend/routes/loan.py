from flask import Blueprint, jsonify, request

from backend.models import ContactMessage, Loan, Review, User, db


loan_bp = Blueprint("loan", __name__)


@loan_bp.post("/loans/apply")
def apply_loan():
    """Stage 1: Registration & Application (Pengajuan)"""
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    amount = data.get("amount")
    term_months = data.get("term_months")
    purpose = (data.get("purpose") or "").strip()

    if user_id is None or amount is None or term_months is None or not purpose:
        return (
            jsonify({"error": "user_id, amount, term_months, and purpose are required"}),
            400,
        )

    try:
        amount_f = float(amount)
        term_i = int(term_months)
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be number and term_months must be integer"}), 400

    if amount_f <= 0:
        return jsonify({"error": "amount must be > 0"}), 400
    if term_i < 1 or term_i > 60:
        return jsonify({"error": "term_months must be between 1 and 60"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Ensure mandatory identity fields are present
    if not user.ktp_number or not user.selfie_filename:
        return (
            jsonify({"error": "User identity not complete", "details": "Provide ktp_number and selfie_filename during registration"}),
            400,
        )

    loan = Loan(
        user_id=user_id,
        amount=amount_f,
        term_months=term_i,
        purpose=purpose,
        status="pending",
        is_eligible=False,
    )
    db.session.add(loan)
    db.session.commit()

    return jsonify({"message": "Loan application submitted", "loan": loan.to_dict()}), 201


# Backward compatibility: keep old endpoint but redirect to new one semantics
@loan_bp.post("/loans")
def create_loan():
    return apply_loan()


@loan_bp.get("/loans")
def list_loans():
    user_id = request.args.get("user_id", type=int)

    query = Loan.query
    if user_id:
        query = query.filter_by(user_id=user_id)

    loans = query.order_by(Loan.created_at.desc()).all()
    return jsonify({"loans": [loan.to_dict() for loan in loans]})


@loan_bp.post("/contact")
def create_contact_message():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    message = (data.get("message") or "").strip()
    user_id = data.get("user_id")

    if not name or not email or not message:
        return jsonify({"error": "name, email, and message are required"}), 400

    contact = ContactMessage(
        user_id=user_id,
        name=name,
        email=email,
        phone=phone,
        message=message,
    )
    db.session.add(contact)
    db.session.commit()

    return jsonify({"message": "Message sent", "contact": contact.to_dict()}), 201


@loan_bp.post("/reviews")
def create_review():
    data = request.get_json(silent=True) or {}

    reviewer_name = (data.get("reviewer_name") or "").strip()
    role = (data.get("role") or "Pengguna").strip()
    comment = (data.get("comment") or "").strip()
    rating = data.get("rating")
    user_id = data.get("user_id")

    if not reviewer_name or not comment or rating is None:
        return jsonify({"error": "reviewer_name, rating, and comment are required"}), 400

    try:
        rating_i = int(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "rating must be integer"}), 400

    if rating_i < 1 or rating_i > 5:
        return jsonify({"error": "rating must be between 1 and 5"}), 400

    review = Review(
        user_id=user_id,
        reviewer_name=reviewer_name,
        role=role,
        rating=rating_i,
        comment=comment,
    )
    db.session.add(review)
    db.session.commit()

    return jsonify({"message": "Review created", "review": review.to_dict()}), 201


@loan_bp.get("/reviews")
def list_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return jsonify({"reviews": [review.to_dict() for review in reviews]})

