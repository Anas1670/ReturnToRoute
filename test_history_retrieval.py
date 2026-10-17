from datetime import date
from unittest.mock import patch
from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.returns import create_return_request
from app.status import update_return_status
from app.history import get_return_history

print("\nReturn-to-Route History Retrieval Tests")
print("---------------------------------------")

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
                "History Test Customer",
                "history-test@example.com",
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
            ("Test Tablet", "Electronics", 249.99),
        )
        product_id = cur.fetchone()[0]

    # Share one database transaction for the entire test.
    test_connection = TestConnection()

    with patch(
        "app.returns.get_db_connection",
        return_value=test_connection
    ), patch(
        "app.status.get_db_connection",
        return_value=test_connection
    ), patch(
        "app.history.get_db_connection",
        return_value=test_connection
    ):
        created = create_return_request(
            customer_id=customer_id,
            product_id=product_id,
            purchase_date=date.today(),
            return_reason="Tablet does not meet expectations",
            item_condition="good",
            packaging_condition="opened",
            functionality="working",
        )

        return_id = created["return_id"]

        # First status change.
        update_return_status(
            return_id,
            "Pending Inspection",
            changed_by=customer_id,
        )

        # Second status change.
        update_return_status(
            return_id,
            "Pending Approval",
            changed_by=customer_id,
        )

        # Retrieve complete history.
        history = get_return_history(return_id)

        assert len(history) == 2
        print("Test 1: PASS - Two history records retrieved")

        assert history[0]["old_status"] == "Submitted"
        assert history[0]["new_status"] == "Pending Inspection"

        assert history[1]["old_status"] == "Pending Inspection"
        assert history[1]["new_status"] == "Pending Approval"

        print("Test 2: PASS - History is in correct order")

        assert all(
            record["changed_by"] == customer_id
            for record in history
        )
        print("Test 3: PASS - Changed-by user recorded")

        empty_history = get_return_history(-1)
        assert empty_history == []
        print("Test 4: PASS - Nonexistent return has empty history")

finally:
    conn.rollback()
    conn.close()
    print("---------------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
