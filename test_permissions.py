from datetime import date
from unittest.mock import patch
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.returns import create_return_request
from app.status import update_return_status


print("\nReturn-to-Route Role Authorization Tests")
print("----------------------------------------")

conn = get_db_connection()


class TestConnection:
    def __enter__(self):
        return conn

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def expect_error(function, error_type):
    try:
        function()
    except error_type:
        return
    raise AssertionError(
        f"Expected {error_type.__name__}, but no error occurred"
    )


try:
    unique_id = uuid4().hex

    with conn.cursor() as cur:
        user_ids = {}

        for role, label in [
            ("customer", "customer1"),
            ("customer", "customer2"),
            ("staff", "staff"),
        ]:
            cur.execute(
                """
                INSERT INTO users (
                    full_name, email, password_hash, role
                )
                VALUES (%s, %s, %s, %s)
                RETURNING user_id;
                """,
                (
                    f"Test {label}",
                    f"{label}-{unique_id}@example.com",
                    generate_password_hash("temporary-test-password"),
                    role,
                ),
            )
            user_ids[label] = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO products (
                product_name, category, original_price
            )
            VALUES (%s, %s, %s)
            RETURNING product_id;
            """,
            ("Authorization Test Product", "Electronics", 99.99),
        )
        product_id = cur.fetchone()[0]

    customer1 = user_ids["customer1"]
    customer2 = user_ids["customer2"]
    staff_id = user_ids["staff"]

    shared_connection = TestConnection()

    with patch(
        "app.returns.get_db_connection",
        return_value=shared_connection
    ), patch(
        "app.status.get_db_connection",
        return_value=shared_connection
    ):

        def new_return(customer_id):
            result = create_return_request(
                customer_id=customer_id,
                product_id=product_id,
                purchase_date=date.today(),
                return_reason="Testing role authorization",
                item_condition="good",
                packaging_condition="opened",
                functionality="working",
            )
            return result["return_id"]

        return1 = new_return(customer1)

        # Test 1: Staff begins inspection.
        result = update_return_status(
            return1,
            "Pending Inspection",
            changed_by=staff_id,
        )
        assert result["new_status"] == "Pending Inspection"
        print("Test 1: PASS - Staff inspection allowed")

        # Test 2: Staff sends return for approval.
        result = update_return_status(
            return1,
            "Pending Approval",
            changed_by=staff_id,
        )
        assert result["new_status"] == "Pending Approval"
        print("Test 2: PASS - Staff approval queue allowed")

        # Test 3: Customer cancels their own submitted return.
        return2 = new_return(customer1)

        result = update_return_status(
            return2,
            "Cancelled",
            changed_by=customer1,
        )
        assert result["new_status"] == "Cancelled"
        print("Test 3: PASS - Customer cancellation allowed")

        # Test 4: Customer cannot cancel someone else's return.
        return3 = new_return(customer2)

        expect_error(
            lambda: update_return_status(
                return3,
                "Cancelled",
                changed_by=customer1,
            ),
            PermissionError,
        )
        print("Test 4: PASS - Other customer's return protected")

        # Test 5: Customer cannot start inspection.
        expect_error(
            lambda: update_return_status(
                return3,
                "Pending Inspection",
                changed_by=customer2,
            ),
            PermissionError,
        )
        print("Test 5: PASS - Staff-only transition protected")

        # Test 6: Staff cannot bypass approval.
        expect_error(
            lambda: update_return_status(
                return3,
                "Approved",
                changed_by=staff_id,
            ),
            ValueError,
        )
        print("Test 6: PASS - Approval bypass rejected")

        # Test 7: Anonymous status change rejected.
        expect_error(
            lambda: update_return_status(
                return3,
                "Cancelled",
            ),
            PermissionError,
        )
        print("Test 7: PASS - Anonymous change rejected")

        # Verify unauthorized attempts did not change records.
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT status
                FROM return_requests
                WHERE return_id = %s;
                """,
                (return3,),
            )
            assert cur.fetchone()[0] == "Submitted"

            cur.execute(
                """
                SELECT COUNT(*)
                FROM return_status_history
                WHERE return_id = %s;
                """,
                (return3,),
            )
            assert cur.fetchone()[0] == 0

        print("Database verification: PASS")

finally:
    conn.rollback()
    conn.close()
    print("----------------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
