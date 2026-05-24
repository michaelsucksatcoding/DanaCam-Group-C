from flask import Blueprint, jsonify, request

from backend.models import User, db


auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    """Stage 1: Registration (Registrasi & Pengajuan)

    DanaCam requires identity fields as part of the workflow simulation.
    We store: KTP number + selfie filename (simulated upload).
    """
    data = request.get_json(silent=True) or {}

    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    phone = (data.get("phone") or "").strip()
    ktp_number = (data.get("ktp_number") or "").strip()
    selfie_filename = (data.get("selfie_filename") or "").strip()

    # Mandatory fields for DanaCam workflow simulation
    required = {
        "full_name": full_name,
        "email": email,
        "password": password,
        "phone": phone,
        "ktp_number": ktp_number,
        "selfie_filename": selfie_filename,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        return jsonify({"error": "Missing required fields", "details": {"missing": missing}}), 400

    if len(ktp_number) < 8:
        return jsonify({"error": "ktp_number must be at least 8 characters"}), 400
    if len(phone) < 8 or not phone.isdigit():
        return jsonify({"error": "phone must be digits only (min 8 digits)"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        full_name=full_name,
        email=email,
        phone=phone,
        ktp_number=ktp_number,
        selfie_filename=selfie_filename,
    )
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
