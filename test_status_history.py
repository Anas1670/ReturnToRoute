from datetime import date
from unittest.mock import patch
from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.returns import create_return_request
from app.status import update_return_status

print("\nReturn-to-Route Status History Tests")
print("------------------------------------")

conn = get_db_connection()

class TestConnection:
    def __enter__(self):
        return conn

    def __exit__(self, exc_type, exc_value, traceback):
        return False

try:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, 'customer')
            RETURNING user_id;
            """,
            (
                "Status Test Customer",
                "status-test@example.com",
                generate_password_hash("temporary-test-password"),
            ),
        )
        customer_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO products (product_name, category, original_price)
            VALUES (%s, %s, %s)
            RETURNING product_id;
            """,
            ("Test Smartphone", "Electronics", 299.99),
        )
        product_id = cur.fetchone()[0]

    with patch(
        "app.returns.get_db_connection",
        return_value=TestConnection()
    ), patch(
        "app.status.get_db_connection",
        return_value=TestConnection()
    ):
        created = create_return_request(
            customer_id=customer_id,
            product_id=product_id,
            purchase_date=date.today(),
            return_reason="Product does not meet expectations",
            item_condition="good",
            packaging_condition="opened",
            functionality="working",
        )

        return_id = created["return_id"]

        result = update_return_status(
            return_id=return_id,
            new_status="Pending Inspection",
            changed_by=customer_id,
        )

        assert result["old_status"] == "Submitted"
        assert result["new_status"] == "Pending Inspection"

        print("Test 1: PASS - Status update completed")

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT status
                FROM return_requests
                WHERE return_id = %s;
                """,
                (return_id,),
            )
            current_status = cur.fetchone()[0]

            cur.execute(
                """
                SELECT old_status, new_status, changed_by
                FROM return_status_history
                WHERE history_id = %s;
                """,
                (result["history_id"],),
            )
            history = cur.fetchone()

        assert current_status == "Pending Inspection"
        assert history == (
            "Submitted",
            "Pending Inspection",
            customer_id,
        )

        print("Test 2: PASS - Status history recorded correctly")

        try:
            update_return_status(
                return_id=return_id,
                new_status="Pending Inspection",
                changed_by=customer_id,
            )
        except ValueError as error:
            assert str(error) == "Return already has this status"
            print("Test 3: PASS - Duplicate status rejected")
        else:
            raise AssertionError("Duplicate status was accepted")

finally:
    conn.rollback()
    conn.close()
    print("------------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
