from unittest.mock import patch
from uuid import uuid4

from flask import jsonify
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db_connection


print("\nReturn-to-Route Logout API Tests")
print("--------------------------------")

conn = get_db_connection()


class TestConnection:
    def __enter__(self):
        return conn

    def __exit__(self, exc_type, exc_value, traceback):
        return False


try:
    unique_id = uuid4().hex
    email = f"logout-test-{unique_id}@example.com"
    password = "LogoutTestPassword123!"

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (
                full_name, email, password_hash, role
            )
            VALUES (%s, %s, %s, 'customer')
            RETURNING user_id;
            """,
            (
                "Logout Test Customer",
                email,
                generate_password_hash(password),
            ),
        )
        customer_id = cur.fetchone()[0]

    app = create_app()
    app.config["TESTING"] = True

    # Temporary protected endpoint used only in this test.
    @app.route("/test-auth-status")
    @login_required
    def test_auth_status():
        return jsonify({
            "authenticated": current_user.is_authenticated,
            "user_id": current_user.id,
        })

    shared_connection = TestConnection()

    with patch(
        "app.login.get_db_connection",
        return_value=shared_connection
    ), patch(
        "app.models.get_db_connection",
        return_value=shared_connection
    ):

        client = app.test_client()

        # Test 1: Anonymous logout is rejected.
        response = client.post("/api/logout")
        assert response.status_code == 401
        print("Test 1: PASS - Anonymous logout rejected")

        # Test 2: Customer logs in successfully.
        response = client.post(
            "/api/login",
            json={
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 200
        print("Test 2: PASS - Customer login successful")

        # Test 3: Flask-Login restores the user.
        response = client.get("/test-auth-status")

        assert response.status_code == 200
        assert response.json["authenticated"] is True
        assert response.json["user_id"] == str(customer_id)

        print("Test 3: PASS - Authenticated session restored")

        # Test 4: Customer logs out successfully.
        response = client.post("/api/logout")

        assert response.status_code == 200
        assert response.json["message"] == "Logout successful"

        print("Test 4: PASS - Customer logout successful")

        # Test 5: Session is cleared.
        with client.session_transaction() as session:
            assert session.get("_user_id") is None

        response = client.get("/test-auth-status")
        assert response.status_code == 401

        print("Test 5: PASS - Session terminated")

        # Test 6: Repeated logout is rejected.
        response = client.post("/api/logout")

        assert response.status_code == 401
        print("Test 6: PASS - Repeated logout rejected")

finally:
    conn.rollback()
    conn.close()

    print("--------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
