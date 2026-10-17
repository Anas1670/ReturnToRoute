from datetime import date
from unittest.mock import patch
from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.returns import create_return_request
from app.decisions import save_routing_decision

print("\nReturn-to-Route Routing Decision Tests")
print("--------------------------------------")

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
                "Routing Test Customer",
                "routing-test@example.com",
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
            ("Test Monitor", "Electronics", 199.99),
        )
        product_id = cur.fetchone()[0]

    test_connection = TestConnection()

    with patch(
        "app.returns.get_db_connection",
        return_value=test_connection
    ), patch(
        "app.decisions.get_db_connection",
        return_value=test_connection
    ):
        created = create_return_request(
            customer_id=customer_id,
            product_id=product_id,
            purchase_date=date.today(),
            return_reason="Monitor did not meet expectations",
            item_condition="good",
            packaging_condition="opened",
            functionality="working",
        )

        return_id = created["return_id"]

        # Test 1: Generate and save recommendation.
        decision = save_routing_decision(return_id)

        assert decision["recommended_route"] == "Restock"
        assert decision["approval_required"] is True

        print("Test 1: PASS - Recommendation generated")
        print("Recommended route:", decision["recommended_route"])

        # Test 2: Verify recommendation in PostgreSQL.
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT recommended_route, rule_applied
                FROM routing_decisions
                WHERE decision_id = %s;
                """,
                (decision["decision_id"],),
            )
            saved = cur.fetchone()

        assert saved == ("Restock", "GOOD_WORKING_CONDITION")

        print("Test 2: PASS - Recommendation saved in PostgreSQL")

        # Test 3: Reject duplicate recommendation.
        try:
            save_routing_decision(return_id)
        except ValueError as error:
            assert "already exists" in str(error)
            print("Test 3: PASS - Duplicate recommendation rejected")
        else:
            raise AssertionError("Duplicate recommendation was accepted")

        # Test 4: Reject nonexistent return.
        try:
            save_routing_decision(-1)
        except ValueError as error:
            assert str(error) == "Return request not found"
            print("Test 4: PASS - Nonexistent return rejected")
        else:
            raise AssertionError("Nonexistent return was accepted")

        # Verify that no staff approval was created.
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM staff_reviews
                WHERE return_id = %s;
                """,
                (return_id,),
            )
            review_count = cur.fetchone()[0]

        assert review_count == 0
        print("Test 5: PASS - No staff approval created")

finally:
    conn.rollback()
    conn.close()
    print("--------------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
