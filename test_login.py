from unittest.mock import patch
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.login import authenticate_user


print("\nReturn-to-Route Login Authentication Tests")
print("------------------------------------------")

conn = get_db_connection()


class TestConnection:
    def __enter__(self):
        return conn

    def __exit__(self, exc_type, exc_value, traceback):
        return False


try:
    unique_id = uuid4().hex

    customer_email = f"login-customer-{unique_id}@example.com"
    staff_email = f"login-staff-{unique_id}@example.com"

    customer_password = "CustomerTestPassword123!"
    staff_password = "StaffTestPassword123!"

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
                "Login Test Customer",
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
                "Login Test Staff",
                staff_email,
                generate_password_hash(staff_password),
            ),
        )
        staff_id = cur.fetchone()[0]

    with patch(
        "app.login.get_db_connection",
        return_value=TestConnection()
    ):

        # Test 1: Valid customer login.
        customer = authenticate_user(
            customer_email,
            customer_password,
        )

        assert customer is not None
        assert customer.id == str(customer_id)
        assert customer.role == "customer"

        print("Test 1: PASS - Customer login successful")

        # Test 2: Incorrect password.
        assert authenticate_user(
            customer_email,
            "WrongPassword123!",
        ) is None

        print("Test 2: PASS - Incorrect password rejected")

        # Test 3: Unknown email address.
        assert authenticate_user(
            f"unknown-{unique_id}@example.com",
            customer_password,
        ) is None

        print("Test 3: PASS - Unknown email rejected")

        # Test 4: Valid staff login.
        staff = authenticate_user(
            staff_email,
            staff_password,
        )

        assert staff is not None
        assert staff.id == str(staff_id)
        assert staff.role == "staff"

        print("Test 4: PASS - Staff login successful")

        # Test 5: Case-insensitive email lookup.
        uppercase_email = customer_email.upper()

        assert authenticate_user(
            uppercase_email,
            customer_password,
        ) is not None

        print("Test 5: PASS - Email normalization works")

        # Test 6: Empty password.
        assert authenticate_user(
            customer_email,
            "",
        ) is None

        print("Test 6: PASS - Empty password rejected")

        # Test 7: Invalid password type.
        assert authenticate_user(
            customer_email,
            12345,
        ) is None

        print("Test 7: PASS - Invalid password type rejected")

finally:
    conn.rollback()
    conn.close()

    print("------------------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
