from datetime import date
from unittest.mock import patch
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.customer_queries import get_customer_returns


print("\nReturn-to-Route Customer Return Retrieval Tests")
print("-----------------------------------------------")

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
    unique_id = uuid4().hex

    with conn.cursor() as cur:
        # Create two customers and one customer without returns.
        customer_ids = []

        for number in range(1, 4):
            cur.execute(
                """
                INSERT INTO users (
                    full_name, email, password_hash, role
                )
                VALUES (%s, %s, %s, 'customer')
                RETURNING user_id;
                """,
                (
                    f"Return Test Customer {number}",
                    f"returns-{number}-{unique_id}@example.com",
                    generate_password_hash("TestPassword123!"),
                ),
            )
            customer_ids.append(cur.fetchone()[0])

        customer_a, customer_b, customer_c = customer_ids

        # Create a temporary product.
        cur.execute(
            """
            INSERT INTO products (
                product_name, category, original_price
            )
            VALUES (%s, %s, %s)
            RETURNING product_id;
            """,
            ("Test Headphones", "Electronics", 79.99),
        )
        product_id = cur.fetchone()[0]

        # Create one return for each of the first two customers.
        return_ids = []

        for customer_id in (customer_a, customer_b):
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

        return_a, return_b = return_ids

    shared_connection = TestConnection()

    with patch(
        "app.customer_queries.get_db_connection",
        return_value=shared_connection
    ):
        # Test 1: Customer A sees their own return.
        results_a = get_customer_returns(customer_a)

        assert len(results_a) == 1
        assert results_a[0]["return_id"] == return_a
        assert results_a[0]["product_name"] == "Test Headphones"
        assert results_a[0]["status"] == "Submitted"
        print("Test 1: PASS - Customer A return retrieved")

        # Test 2: Customer B sees their own return.
        results_b = get_customer_returns(customer_b)

        assert len(results_b) == 1
        assert results_b[0]["return_id"] == return_b
        print("Test 2: PASS - Customer B return retrieved")

        # Test 3: Customer A cannot see B's return.
        assert all(
            item["return_id"] != return_b
            for item in results_a
        )
        print("Test 3: PASS - Customer A data isolated")

        # Test 4: Customer B cannot see A's return.
        assert all(
            item["return_id"] != return_a
            for item in results_b
        )
        print("Test 4: PASS - Customer B data isolated")

        # Test 5: Customer without returns gets an empty list.
        results_c = get_customer_returns(customer_c)

        assert results_c == []
        print("Test 5: PASS - Empty return list handled")

        # Test 6: Invalid customer ID rejected.
        expect_value_error(
            lambda: get_customer_returns("invalid")
        )
        print("Test 6: PASS - Invalid customer ID rejected")

    print("-----------------------------------------------")
    print("All customer return retrieval tests passed.")

finally:
    conn.rollback()
    conn.close()
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
