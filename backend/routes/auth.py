from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User, AdminLog
from models import db
import re
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        full_name = data.get("full_name", "").strip()

        if not username or not email or not password:
            return jsonify({"error": "Username, email, and password are required"}), 400

        if len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters"}), 400

        if not EMAIL_REGEX.match(email):
            return jsonify({"error": "Invalid email format"}), 400

        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 409

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        user = User(username=username, email=email, full_name=full_name or username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=str(user.id))
        return jsonify(
            {
                "message": "Account created successfully",
                "token": token,
                "user": user.to_dict(),
            }
        ), 201

    except Exception as e:
        logger.error(f"Signup error: {e}")
        db.session.rollback()
        return jsonify({"error": "Registration failed. Please try again."}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        user = User.query.filter(
            (User.username == username) | (User.email == username.lower())
        ).first()

        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401

        if not user.is_active:
            return jsonify({"error": "Account is deactivated"}), 403

        token = create_access_token(identity=str(user.id))
        return jsonify(
            {"message": "Login successful", "token": token, "user": user.to_dict()}
        ), 200

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed. Please try again."}), 500


@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"user": user.to_dict()}), 200
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return jsonify({"error": "Failed to load profile"}), 500


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        if "full_name" in data:
            user.full_name = data["full_name"]
        if "email" in data:
            new_email = data["email"].strip().lower()
            if new_email != user.email:
                if User.query.filter_by(email=new_email).first():
                    return jsonify({"error": "Email already in use"}), 409
                user.email = new_email

        db.session.commit()
        return jsonify({"message": "Profile updated", "user": user.to_dict()}), 200

    except Exception as e:
        logger.error(f"Profile update error: {e}")
        db.session.rollback()
        return jsonify({"error": "Update failed"}), 500


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        current = data.get("current_password", "")
        new_pass = data.get("new_password", "")

        if not user.check_password(current):
            return jsonify({"error": "Current password is incorrect"}), 401

        if len(new_pass) < 6:
            return jsonify({"error": "New password must be at least 6 characters"}), 400

        user.set_password(new_pass)
        db.session.commit()
        return jsonify({"message": "Password changed successfully"}), 200

    except Exception as e:
        logger.error(f"Password change error: {e}")
        db.session.rollback()
        return jsonify({"error": "Password change failed"}), 500
