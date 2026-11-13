import re
from datetime import date

from flask import Blueprint, jsonify, request
from flask_login import login_user
from psycopg.errors import UniqueViolation
from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.login import authenticate_user


auth = Blueprint("auth", __name__)


@auth.route("/api/register", methods=["POST"])
def register():
    """
    Register a new customer account.
    Public registration cannot create staff accounts.
    """
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required."
        }), 400

    full_name = data.get("full_name")
    email = data.get("email")
    phone_number = data.get("phone_number")
    date_of_birth = data.get("date_of_birth")
    gender = data.get("gender", "")
    password = data.get("password")
    role = data.get("role", "customer")
    staff_code = data.get("staff_code", "")

    if role not in ("customer", "staff"):
        return jsonify({"error": "Invalid account type."}), 400

    fields = (
        full_name, email, phone_number,
        date_of_birth, gender, password
    )

    if not all(isinstance(value, str) for value in fields):
        return jsonify({
            "error": "Invalid or missing registration fields."
        }), 400

    full_name = full_name.strip()
    email = email.strip().lower()
    phone_number = phone_number.strip()
    gender = gender.strip()

    if not full_name or len(full_name) > 150:
        return jsonify({
            "error": "Full name must be between 1 and 150 characters."
        }), 400

    if len(email) > 254 or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+", email
    ):
        return jsonify({
            "error": "Please enter a valid email address."
        }), 400

    if (
        len(phone_number) > 20
        or not re.fullmatch(r"\+?[0-9 ()-]+", phone_number)
        or not 7 <= sum(c.isdigit() for c in phone_number) <= 15
    ):
        return jsonify({
            "error": "Please enter a valid phone number."
        }), 400

    try:
        birth_date = date.fromisoformat(date_of_birth)
    except ValueError:
        return jsonify({
            "error": "Please enter a valid date of birth."
        }), 400

    if birth_date > date.today():
        return jsonify({
            "error": "Date of birth cannot be in the future."
        }), 400

    allowed_genders = {
        "",
        "male",
        "female",
        "non_binary",
        "prefer_not_to_say"
    }

    if gender not in allowed_genders:
        if not gender.startswith("self_describe:"):
            return jsonify({
                "error": "Invalid gender selection."
            }), 400

        description = gender.split(":", 1)[1].strip()

        if not description or len(gender) > 50:
            return jsonify({
                "error": "Please provide a gender description of suitable length."
            }), 400

    if len(password) < 8 or len(password) > 128:
        return jsonify({
            "error": "Password must be between 8 and 128 characters."
        }), 400

    password_hash = generate_password_hash(password)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (
                        full_name,
                        email,
                        phone_number,
                        date_of_birth,
                        gender,
                        password_hash,
                        role
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING user_id, full_name, email, role;
                    """,
                    (
                        full_name,
                        email,
                        phone_number,
                        birth_date,
                        gender or None,
                        password_hash,
                        role
                    ),
                )

                user_id, saved_name, saved_email, role = (
                    cur.fetchone()
                )

            conn.commit()

    except UniqueViolation:
        return jsonify({
            "error": "An account with this email already exists."
        }), 409

    return jsonify({
        "message": "Account created successfully.",
        "user": {
            "user_id": int(user_id),
            "full_name": saved_name,
            "email": saved_email,
            "role": role
        }
    }), 201


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
    selected_role = data.get("role")

    if selected_role is not None and selected_role not in ("customer", "staff"):
        return jsonify({"error": "Invalid account type."}), 400

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({
            "error": "Email and password are required."
        }), 400

    user = authenticate_user(email, password)

    if user is None:
        return jsonify({
            "error": "Invalid email or password."
        }), 401

    if selected_role is not None and user.role != selected_role:
        return jsonify({
            "error": "This account is not registered as the selected account type."
        }), 403

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
