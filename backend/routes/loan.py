from flask import Blueprint, jsonify, request

from models import ContactMessage, Loan, Review, User, db

loan_bp = Blueprint("loan", __name__)


@loan_bp.post("/loans")
def create_loan():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    amount = data.get("amount")
    term_months = data.get("term_months")
    purpose = (data.get("purpose") or "").strip()

    if not all([user_id, amount, term_months, purpose]):
        return jsonify({"error": "user_id, amount, term_months, and purpose are required"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    loan = Loan(
        user_id=user_id,
        amount=float(amount),
        term_months=int(term_months),
        purpose=purpose,
    )
    db.session.add(loan)
    db.session.commit()

    return jsonify({"message": "Loan application submitted", "loan": loan.to_dict()}), 201


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

    if int(rating) < 1 or int(rating) > 5:
        return jsonify({"error": "rating must be between 1 and 5"}), 400

    review = Review(
        user_id=user_id,
        reviewer_name=reviewer_name,
        role=role,
        rating=int(rating),
        comment=comment,
    )
    db.session.add(review)
    db.session.commit()

    return jsonify({"message": "Review created", "review": review.to_dict()}), 201


@loan_bp.get("/reviews")
def list_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return jsonify({"reviews": [review.to_dict() for review in reviews]})
