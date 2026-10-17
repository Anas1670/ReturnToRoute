from unittest.mock import patch
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db_connection


print("\nReturn-to-Route Dashboard Permission Tests")
print("------------------------------------------")

conn = get_db_connection()


class TestConnection:
    def __enter__(self):
        return conn

    def __exit__(self, exc_type, exc_value, traceback):
        return False


try:
    unique_id = uuid4().hex

    customer_email = f"dashboard-customer-{unique_id}@example.com"
    staff_email = f"dashboard-staff-{unique_id}@example.com"

    customer_password = "CustomerTestPassword123!"
    staff_password = "StaffTestPassword123!"

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, 'customer')
            RETURNING user_id;
            """,
            (
                "Dashboard Test Customer",
                customer_email,
                generate_password_hash(customer_password),
            ),
        )
        customer_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, 'staff')
            RETURNING user_id;
            """,
            (
                "Dashboard Test Staff",
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

        # Test 1: Anonymous customer dashboard access.
        anonymous = app.test_client()
        response = anonymous.get("/api/customer/dashboard")
        assert response.status_code == 401
        print("Test 1: PASS - Anonymous customer access rejected")

        # Test 2: Anonymous staff dashboard access.
        response = anonymous.get("/api/staff/dashboard")
        assert response.status_code == 401
        print("Test 2: PASS - Anonymous staff access rejected")

        # Log in as customer.
        customer_client = app.test_client()
        response = customer_client.post(
            "/api/login",
            json={
                "email": customer_email,
                "password": customer_password,
            },
        )
        assert response.status_code == 200

        # Test 3: Customer accesses customer dashboard.
        response = customer_client.get("/api/customer/dashboard")
        assert response.status_code == 200
        assert response.json["user"]["user_id"] == customer_id
        assert response.json["user"]["role"] == "customer"
        print("Test 3: PASS - Customer dashboard access allowed")

        # Test 4: Customer cannot access staff dashboard.
        response = customer_client.get("/api/staff/dashboard")
        assert response.status_code == 403
        print("Test 4: PASS - Customer denied staff access")

        # Log in as staff.
        staff_client = app.test_client()
        response = staff_client.post(
            "/api/login",
            json={
                "email": staff_email,
                "password": staff_password,
            },
        )
        assert response.status_code == 200

        # Test 5: Staff accesses staff dashboard.
        response = staff_client.get("/api/staff/dashboard")
        assert response.status_code == 200
        assert response.json["user"]["user_id"] == staff_id
        assert response.json["user"]["role"] == "staff"
        print("Test 5: PASS - Staff dashboard access allowed")

        # Test 6: Staff cannot access customer dashboard.
        response = staff_client.get("/api/customer/dashboard")
        assert response.status_code == 403
        print("Test 6: PASS - Staff denied customer access")

        # Test 7: Logout removes dashboard access.
        response = customer_client.post("/api/logout")
        assert response.status_code == 200

        response = customer_client.get("/api/customer/dashboard")
        assert response.status_code == 401
        print("Test 7: PASS - Logout removes dashboard access")

finally:
    conn.rollback()
    conn.close()

    print("------------------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
