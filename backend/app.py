from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import Config
from models import db
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.loan import loan_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend" / "frontend"

    CORS(app)
    db.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(loan_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.get("/api/health")
    def health_check():
        return jsonify({"status": "ok", "message": "DanaCam backend running"})

    @app.get("/")
    def serve_home():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/login.html")
    def serve_login():
        return send_from_directory(frontend_dir, "login.html")

    @app.get("/<path:filename>")
    def serve_frontend_asset(filename: str):
        return send_from_directory(frontend_dir, filename)

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
