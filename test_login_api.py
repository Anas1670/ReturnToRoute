from unittest.mock import patch
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db_connection


print("\nReturn-to-Route Login API Tests")
print("--------------------------------")

conn = get_db_connection()


class TestConnection:
    def __enter__(self):
        return conn

    def __exit__(self, exc_type, exc_value, traceback):
        return False


try:
    unique_id = uuid4().hex
    customer_email = f"api-customer-{unique_id}@example.com"
    staff_email = f"api-staff-{unique_id}@example.com"

    customer_password = "CustomerPassword123!"
    staff_password = "StaffPassword123!"

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
                "API Test Customer",
                customer_email,
                generate_password_hash(customer_password),
            ),
        )
        customer_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO users (
                full_name, email, password_hash, role
            )
            VALUES (%s, %s, %s, 'staff')
            RETURNING user_id;
            """,
            (
                "API Test Staff",
                staff_email,
                generate_password_hash(staff_password),
            ),
        )
        staff_id = cur.fetchone()[0]

    app = create_app()
    app.config["TESTING"] = True

    shared_connection = TestConnection()

    with patch(
        "app.login.get_db_connection",
        return_value=shared_connection
    ), patch(
        "app.models.get_db_connection",
        return_value=shared_connection
    ):

        client = app.test_client()

        # Test 1: Valid customer login.
        response = client.post(
            "/api/login",
            json={
                "email": customer_email,
                "password": customer_password,
            },
        )

        assert response.status_code == 200
        assert response.json["user"]["role"] == "customer"
        assert response.json["user"]["user_id"] == customer_id
        print("Test 1: PASS - Customer login successful")

        # Test 2: Incorrect password.
        wrong_client = app.test_client()

        response = wrong_client.post(
            "/api/login",
            json={
                "email": customer_email,
                "password": "IncorrectPassword!",
            },
        )

        assert response.status_code == 401
        print("Test 2: PASS - Incorrect password rejected")

        # Test 3: Invalid JSON.
        response = wrong_client.post(
            "/api/login",
            data="invalid-json",
            content_type="application/json",
        )

        assert response.status_code == 400
        print("Test 3: PASS - Invalid JSON rejected")

        # Test 4: Session cookie created.
        with client.session_transaction() as session:
            assert session.get("_user_id") == str(customer_id)

        print("Test 4: PASS - Login session created")

        # Test 5: Session persists across requests.
        with client.application.test_request_context(
            "/", headers={"Cookie": ""}
        ):
            pass

        response = client.get("/")

        assert response.status_code == 200

        with client.session_transaction() as session:
            assert session.get("_user_id") == str(customer_id)

        print("Test 5: PASS - Session persists across requests")

        # Test 6: Staff login.
        staff_client = app.test_client()

        response = staff_client.post(
            "/api/login",
            json={
                "email": staff_email,
                "password": staff_password,
            },
        )

        assert response.status_code == 200
        assert response.json["user"]["role"] == "staff"
        assert response.json["user"]["user_id"] == staff_id

        print("Test 6: PASS - Staff login successful")

finally:
    conn.rollback()
    conn.close()

    print("--------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
