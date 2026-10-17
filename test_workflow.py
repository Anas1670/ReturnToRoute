from datetime import date
from unittest.mock import patch
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.returns import create_return_request
from app.status import update_return_status


print("\nReturn-to-Route Workflow Restriction Tests")
print("------------------------------------------")

conn = get_db_connection()


class TestConnection:
    def __enter__(self):
        return conn

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def expect_rejected(return_id, new_status):
    try:
        update_return_status(return_id, new_status)
    except ValueError:
        return

    raise AssertionError(
        f"Transition to {new_status} was unexpectedly accepted"
    )


try:
    with conn.cursor() as cur:
        unique_id = uuid4().hex

        cur.execute(
            """
            INSERT INTO users (
                full_name, email, password_hash, role
            )
            VALUES (%s, %s, %s, 'customer')
            RETURNING user_id;
            """,
            (
                "Workflow Test Customer",
                f"workflow-{unique_id}@example.com",
                generate_password_hash("temporary-test-password"),
            ),
        )
        customer_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO products (
                product_name, category, original_price
            )
            VALUES (%s, %s, %s)
            RETURNING product_id;
            """,
            ("Workflow Test Product", "Electronics", 50.00),
        )
        product_id = cur.fetchone()[0]

    test_connection = TestConnection()

    with patch(
        "app.returns.get_db_connection",
        return_value=test_connection
    ), patch(
        "app.status.get_db_connection",
        return_value=test_connection
    ):

        def new_return():
            result = create_return_request(
                customer_id=customer_id,
                product_id=product_id,
                purchase_date=date.today(),
                return_reason="Testing workflow restrictions",
                item_condition="good",
                packaging_condition="opened",
                functionality="working",
            )
            return result["return_id"]

        # Test 1: Valid inspection transition.
        return_id = new_return()

        result = update_return_status(
            return_id, "Pending Inspection"
        )
        assert result["new_status"] == "Pending Inspection"
        print("Test 1: PASS - Inspection transition allowed")

        # Test 2: Valid pending approval transition.
        result = update_return_status(
            return_id, "Pending Approval"
        )
        assert result["new_status"] == "Pending Approval"
        print("Test 2: PASS - Pending approval allowed")

        # Test 3: Direct approval from Submitted rejected.
        second_return = new_return()
        expect_rejected(second_return, "Approved")
        print("Test 3: PASS - Direct approval rejected")

        # Test 4: Ordinary function cannot approve.
        expect_rejected(return_id, "Approved")
        print("Test 4: PASS - Approval bypass rejected")

        # Test 5: Cancellation from Pending Approval.
        result = update_return_status(
            return_id, "Cancelled"
        )
        assert result["new_status"] == "Cancelled"
        print("Test 5: PASS - Cancellation allowed")

        # Test 6: Cancelled returns cannot restart.
        expect_rejected(return_id, "Submitted")
        print("Test 6: PASS - Cancelled return protected")

        # Verify the rejected transitions did not
        # create additional status history records.
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM return_status_history
                WHERE return_id = %s;
                """,
                (return_id,),
            )
            assert cur.fetchone()[0] == 3

            cur.execute(
                """
                SELECT status
                FROM return_requests
                WHERE return_id = %s;
                """,
                (second_return,),
            )
            assert cur.fetchone()[0] == "Submitted"

        print("Database verification: PASS")

finally:
    conn.rollback()
    conn.close()
    print("------------------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
