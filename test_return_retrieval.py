from datetime import date
from unittest.mock import patch
from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.returns import create_return_request
from app.queries import get_return_request

print("\nReturn-to-Route Retrieval Tests")
print("--------------------------------")

conn = get_db_connection()

try:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, 'customer')
            RETURNING user_id;
            """,
            (
                "Retrieval Test Customer",
                "retrieval-test@example.com",
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
            ("Test Laptop", "Electronics", 599.99),
        )
        product_id = cur.fetchone()[0]

    # Use one transaction so all temporary records can be rolled back.
    class TestConnection:
        def __enter__(self):
            return conn

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    with patch(
        "app.returns.get_db_connection",
        return_value=TestConnection()
    ), patch(
        "app.queries.get_db_connection",
        return_value=TestConnection()
    ):
        created = create_return_request(
            customer_id=customer_id,
            product_id=product_id,
            purchase_date=date.today(),
            return_reason="Laptop does not meet expectations",
            item_condition="good",
            packaging_condition="opened",
            functionality="working",
        )

        return_id = created["return_id"]

        # Test 1: Retrieve an existing return.
        retrieved = get_return_request(return_id)

        assert retrieved is not None
        assert retrieved["return_id"] == return_id
        assert retrieved["customer_id"] == customer_id
        assert retrieved["product_id"] == product_id
        assert retrieved["status"] == "Submitted"

        print("Test 1: PASS - Existing return retrieved")
        print("Return ID:", retrieved["return_id"])
        print("Return status:", retrieved["status"])

        # Test 2: Retrieve a nonexistent return.
        missing = get_return_request(-1)

        assert missing is None

        print("Test 2: PASS - Nonexistent return handled")

finally:
    conn.rollback()
    conn.close()
    print("--------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
