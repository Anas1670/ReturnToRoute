from flask import Blueprint, jsonify, request
from flask_login import login_user

from app.login import authenticate_user


auth = Blueprint("auth", __name__)


@auth.route("/api/login", methods=["POST"])
def login():
    """
    Authenticate a user and establish a Flask-Login session.
    """

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required."
        }), 400

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({
            "error": "Email and password are required."
        }), 400

    user = authenticate_user(email, password)

    if user is None:
        return jsonify({
            "error": "Invalid email or password."
        }), 401

    login_user(user)

    return jsonify({
        "message": "Login successful",
        "user": {
            "user_id": int(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role
        }
    }), 200


@auth.route("/api/logout", methods=["POST"])
def logout():
    """
    End the authenticated user's Flask-Login session.
    """

    from flask_login import current_user, logout_user

    if not current_user.is_authenticated:
        return jsonify({
            "error": "Authentication required."
        }), 401

    logout_user()

    return jsonify({
        "message": "Logout successful"
    }), 200
