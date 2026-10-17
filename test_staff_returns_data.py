from unittest.mock import patch
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.staff_queries import get_staff_returns
from app.returns import create_return_request
from app.decisions import save_routing_decision
from app.status import update_return_status


class TestConnection:
    """
    Reuse one database connection so test changes
    can be rolled back afterward.
    """

    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc_value, traceback):
        return False

def test_staff_returns_data():
    conn = get_db_connection()

    try:
        with patch(
            "app.returns.get_db_connection",
            return_value=TestConnection(conn)
        ):
            with conn.cursor() as cur:
                unique = uuid4().hex[:8]

                customer_ids = []

                for number in range(2):
                    cur.execute(
                        """
                        INSERT INTO users (
                            full_name, email, password_hash, role
                        )
                        VALUES (%s, %s, %s, 'customer')
                        RETURNING user_id;
                        """,
                        (
                            f"Test Customer {number + 1}",
                            f"stafftest{number}_{unique}@example.com",
                            generate_password_hash("TestPassword123"),
                        ),
                    )
                    customer_ids.append(cur.fetchone()[0])

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
	                # Create a temporary staff user for status updates.
                cur.execute(
                    """
                    INSERT INTO users (
                        full_name, email, password_hash, role
                    )
                    VALUES (%s, %s, %s, 'staff')
                    RETURNING user_id;
                    """,
                    (
                        "Test Staff Member",
                        f"staff_member_{unique}@example.com",
                        generate_password_hash("TestPassword123"),
                    ),
                )

                staff_id = cur.fetchone()[0]

            return_ids = []

            for customer_id in customer_ids:
                result = create_return_request(
                    customer_id=customer_id,
                    product_id=product_id,
                    purchase_date="2026-10-01",
                    return_reason="Product no longer needed",
                    item_condition="good",
                    packaging_condition="opened",
                    functionality="working",
                )

                return_ids.append(result["return_id"])

            assert len(return_ids) == 2

            print("Test 1: PASS - Two temporary returns created")
		            # Test 2: Staff retrieves both return requests.
            with patch(
                "app.staff_queries.get_db_connection",
                return_value=TestConnection(conn)
            ):
                staff_returns = get_staff_returns()

            retrieved_ids = {
                item["return_id"] for item in staff_returns
            }

            assert set(return_ids).issubset(retrieved_ids)

            print("Test 2: PASS - Staff retrieved both returns")

            # Test 3: Verify customer and product information.
            for item in staff_returns:
                if item["return_id"] in return_ids:
                    assert item["customer_id"] in customer_ids
                    assert item["product_name"] == "Test Headphones"
                    assert item["category"] == "Electronics"
                    assert item["status"] == "Submitted"

            print("Test 3: PASS - Return information is correct")
		            # Test 4: Prepare different statuses for priority testing.
            with patch(
                "app.status.get_db_connection",
                return_value=TestConnection(conn)
            ):
                update_return_status(
                    return_ids[0],
                    "Pending Inspection",
		    changed_by=staff_id,
                )

                update_return_status(
                    return_ids[0],
                    "Pending Approval",
	       	    changed_by=staff_id,
                )

            print("Test 4: PASS - Different return statuses prepared")
            # Test 5: Verify staff dashboard priority ordering.
            with patch(
                "app.staff_queries.get_db_connection",
                return_value=TestConnection(conn)
            ):
                prioritized_returns = get_staff_returns()

            prioritized_ids = [
                item["return_id"] for item in prioritized_returns
                if item["return_id"] in return_ids
            ]

            assert prioritized_ids == [
                return_ids[0],
                return_ids[1],
            ], "Pending Approval should appear before Submitted"

            assert next(
                item["status"] for item in prioritized_returns
                if item["return_id"] == return_ids[0]
            ) == "Pending Approval"

            print("Test 5: PASS - Staff dashboard priority ordering is correct")
    finally:
        conn.rollback()
        conn.close()
        print("Test transaction rolled back.")
        print("Temporary records were not saved.")


if __name__ == "__main__":
    print("Return-to-Route Staff Dashboard Data Tests")
    print("------------------------------------------")
    test_staff_returns_data()
