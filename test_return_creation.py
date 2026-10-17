from datetime import date
from unittest.mock import patch
from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.returns import create_return_request

print("\nReturn-to-Route Database Insertion Test")
print("--------------------------------------")

conn = get_db_connection()

try:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id;
            """,
            (
                "Test Customer",
                "temporary-test@example.com",
                generate_password_hash("temporary-test-password"),
                "customer",
            ),
        )
        customer_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO products (product_name, category, original_price)
            VALUES (%s, %s, %s)
            RETURNING product_id;
            """,
            ("Test Headphones", "Electronics", 49.99),
        )
        product_id = cur.fetchone()[0]

    # Keep the function's database operations inside this test transaction.
    class TestConnection:
        def __enter__(self):
            return conn

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    with patch("app.returns.get_db_connection", return_value=TestConnection()):
        result = create_return_request(
            customer_id=customer_id,
            product_id=product_id,
            purchase_date=date.today(),
            return_reason="Product did not meet expectations",
            item_condition="good",
            packaging_condition="opened",
            functionality="working",
        )

    print("Created return ID:", result["return_id"])
    print("Return status:", result["status"])

    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM return_requests WHERE return_id = %s",
            (result["return_id"],),
        )
        count = cur.fetchone()[0]

    assert count == 1, "Return request was not saved"
    assert result["status"] == "Submitted", "Incorrect initial status"

    print("Database insertion test: PASS")

finally:
    conn.rollback()
    conn.close()
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
