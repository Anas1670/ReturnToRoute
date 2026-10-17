from unittest.mock import patch
from uuid import uuid4

from werkzeug.security import check_password_hash

from app.db import get_db_connection
from app.auth import register_customer


print("\nReturn-to-Route Customer Registration Tests")
print("-------------------------------------------")

conn = get_db_connection()


class TestConnection:
    def __enter__(self):
        return conn

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def expect_value_error(function):
    try:
        function()
    except ValueError:
        return
    raise AssertionError("Expected ValueError was not raised")


try:
    unique_email = f"registration-{uuid4().hex}@example.com"
    test_password = "SecureTestPassword123!"

    # Use the same transaction for every test.
    with patch(
        "app.auth.get_db_connection",
        return_value=TestConnection()
    ):

        # Test 1: Register a new customer.
        result = register_customer(
            full_name="Registration Test Customer",
            email=unique_email,
            password=test_password,
        )

        assert result["user_id"] is not None
        assert result["email"] == unique_email
        print("Test 1: PASS - Customer registered")

        # Test 2: Verify customer role.
        assert result["role"] == "customer"

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT role, password_hash
                FROM users
                WHERE user_id = %s;
                """,
                (result["user_id"],),
            )
            row = cur.fetchone()

        assert row is not None
        role, stored_hash = row
        assert role == "customer"
        print("Test 2: PASS - Customer role enforced")

        # Test 3: Verify secure password hashing.
        assert stored_hash != test_password
        assert check_password_hash(stored_hash, test_password)
        assert "password_hash" not in result
        print("Test 3: PASS - Password securely hashed")

        # Test 4: Duplicate email rejected.
        expect_value_error(
            lambda: register_customer(
                full_name="Duplicate Customer",
                email=unique_email,
                password="AnotherPassword123!",
            )
        )
        print("Test 4: PASS - Duplicate email rejected")

        # Test 5: Invalid email rejected.
        expect_value_error(
            lambda: register_customer(
                full_name="Invalid Email Customer",
                email="not-an-email",
                password=test_password,
            )
        )
        print("Test 5: PASS - Invalid email rejected")

        # Test 6: Short password rejected.
        expect_value_error(
            lambda: register_customer(
                full_name="Short Password Customer",
                email=f"short-{uuid4().hex}@example.com",
                password="abc",
            )
        )
        print("Test 6: PASS - Short password rejected")

finally:
    conn.rollback()
    conn.close()
    print("-------------------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
