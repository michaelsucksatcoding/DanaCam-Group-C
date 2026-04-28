from flask import Blueprint, jsonify, request

from models import User, db

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    phone = (data.get("phone") or "").strip()

    if not full_name or not email or not password:
        return jsonify({"error": "full_name, email, and password are required"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "Email already registered"}), 409

    user = User(full_name=full_name, email=email, phone=phone)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registration successful", "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify(
        {
            "message": "Login successful",
            "user": user.to_dict(),
            "token": f"demo-token-{user.id}",
        }
    )
