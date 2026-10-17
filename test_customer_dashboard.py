from datetime import date
from unittest.mock import patch
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db_connection


print("\nReturn-to-Route Customer Dashboard Data Tests")
print("---------------------------------------------")

conn = get_db_connection()


class TestConnection:
    def __enter__(self):
        return conn

    def __exit__(self, exc_type, exc_value, traceback):
        return False


try:
    unique_id = uuid4().hex
    password = "DashboardTestPassword123!"

    customer_ids = []
    customer_emails = []

    with conn.cursor() as cur:
        for number in range(1, 4):
            email = f"dashboard-data-{number}-{unique_id}@example.com"

            cur.execute(
                """
                INSERT INTO users (
                    full_name, email, password_hash, role
                )
                VALUES (%s, %s, %s, 'customer')
                RETURNING user_id;
                """,
                (
                    f"Dashboard Customer {number}",
                    email,
                    generate_password_hash(password),
                ),
            )

            customer_ids.append(cur.fetchone()[0])
            customer_emails.append(email)

        cur.execute(
            """
            INSERT INTO products (
                product_name, category, original_price
            )
            VALUES (%s, %s, %s)
            RETURNING product_id;
            """,
            ("Dashboard Test Laptop", "Electronics", 499.99),
        )
        product_id = cur.fetchone()[0]

        return_ids = []

        for customer_id in customer_ids[:2]:
            cur.execute(
                """
                INSERT INTO return_requests (
                    customer_id,
                    product_id,
                    purchase_date,
                    return_reason,
                    item_condition,
                    packaging_condition,
                    functionality
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING return_id;
                """,
                (
                    customer_id,
                    product_id,
                    date(2026, 10, 1),
                    "Product no longer needed",
                    "good",
                    "opened",
                    "working",
                ),
            )
            return_ids.append(cur.fetchone()[0])

    app = create_app()
    app.config["TESTING"] = True

    shared_connection = TestConnection()

    with patch(
        "app.login.get_db_connection",
        return_value=shared_connection
    ), patch(
        "app.models.get_db_connection",
        return_value=shared_connection
    ), patch(
        "app.customer_queries.get_db_connection",
        return_value=shared_connection
    ):

        # Test 1: Customer A sees their own return.
        client_a = app.test_client()

        response = client_a.post(
            "/api/login",
            json={
                "email": customer_emails[0],
                "password": password,
            },
        )
        assert response.status_code == 200

        response = client_a.get("/api/customer/dashboard")
        assert response.status_code == 200

        data_a = response.get_json()

        assert data_a["user"]["user_id"] == customer_ids[0]
        assert data_a["return_count"] == 1
        assert data_a["returns"][0]["return_id"] == return_ids[0]
        assert data_a["returns"][0]["product_name"] == "Dashboard Test Laptop"

        print("Test 1: PASS - Customer A sees own return")

        # Test 2: Customer A cannot see Customer B's return.
        assert all(
            item["return_id"] != return_ids[1]
            for item in data_a["returns"]
        )
        print("Test 2: PASS - Customer A cannot see B's return")

        # Test 3: Customer B sees their own return.
        client_b = app.test_client()

        response = client_b.post(
            "/api/login",
            json={
                "email": customer_emails[1],
                "password": password,
            },
        )
        assert response.status_code == 200

        response = client_b.get("/api/customer/dashboard")
        assert response.status_code == 200

        data_b = response.get_json()

        assert data_b["user"]["user_id"] == customer_ids[1]
        assert data_b["return_count"] == 1
        assert data_b["returns"][0]["return_id"] == return_ids[1]

        print("Test 3: PASS - Customer B sees own return")

        # Test 4: Customer B cannot see Customer A's return.
        assert all(
            item["return_id"] != return_ids[0]
            for item in data_b["returns"]
        )
        print("Test 4: PASS - Customer B cannot see A's return")

        # Test 5: Customer C has no returns.
        client_c = app.test_client()

        response = client_c.post(
            "/api/login",
            json={
                "email": customer_emails[2],
                "password": password,
            },
        )
        assert response.status_code == 200

        response = client_c.get("/api/customer/dashboard")
        assert response.status_code == 200

        data_c = response.get_json()

        assert data_c["return_count"] == 0
        assert data_c["returns"] == []

        print("Test 5: PASS - Empty dashboard handled")

        # Test 6: Anonymous visitor is rejected.
        anonymous = app.test_client()

        response = anonymous.get("/api/customer/dashboard")
        assert response.status_code == 401

        print("Test 6: PASS - Anonymous access rejected")

    print("---------------------------------------------")
    print("All customer dashboard data tests passed.")

finally:
    conn.rollback()
    conn.close()

    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
