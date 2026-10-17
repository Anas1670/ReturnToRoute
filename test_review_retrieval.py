from datetime import date
from unittest.mock import patch
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.returns import create_return_request
from app.decisions import save_routing_decision
from app.status import update_return_status
from app.reviews import approve_routing_decision
from app.review_history import get_staff_review


print("\nReturn-to-Route Staff Review Retrieval Tests")
print("--------------------------------------------")

conn = get_db_connection()


class TestConnection:
    def __enter__(self):
        return conn

    def __exit__(self, exc_type, exc_value, traceback):
        return False


try:
    with conn.cursor() as cur:
        unique_id = uuid4().hex

        cur.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, 'customer')
            RETURNING user_id;
            """,
            (
                "Review Retrieval Customer",
                f"review-customer-{unique_id}@example.com",
                generate_password_hash("temporary-test-password"),
            ),
        )
        customer_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, 'staff')
            RETURNING user_id;
            """,
            (
                "Review Retrieval Staff",
                f"review-staff-{unique_id}@example.com",
                generate_password_hash("temporary-test-password"),
            ),
        )
        staff_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO products (
                product_name, category, original_price
            )
            VALUES (%s, %s, %s)
            RETURNING product_id;
            """,
            ("Test Keyboard", "Electronics", 49.99),
        )
        product_id = cur.fetchone()[0]

    test_connection = TestConnection()

    with patch(
        "app.returns.get_db_connection",
        return_value=test_connection
    ), patch(
        "app.decisions.get_db_connection",
        return_value=test_connection
    ), patch(
        "app.status.get_db_connection",
        return_value=test_connection
    ), patch(
        "app.reviews.get_db_connection",
        return_value=test_connection
    ), patch(
        "app.review_history.get_db_connection",
        return_value=test_connection
    ):

        created = create_return_request(
            customer_id=customer_id,
            product_id=product_id,
            purchase_date=date.today(),
            return_reason="Keyboard did not meet expectations",
            item_condition="good",
            packaging_condition="opened",
            functionality="working",
        )

        return_id = created["return_id"]
        decision = save_routing_decision(return_id)

        # Test 1: No review exists before staff approval.
        assert get_staff_review(return_id) is None
        print("Test 1: PASS - Unreviewed return handled")

        update_return_status(
            return_id, "Pending Inspection", changed_by=staff_id
        )
        update_return_status(
            return_id, "Pending Approval", changed_by=staff_id
        )

        approved = approve_routing_decision(
            return_id=return_id,
            decision_id=decision["decision_id"],
            staff_id=staff_id,
            final_route="Refurbish",
            override_reason="Packaging requires replacement",
        )

        # Test 2: Retrieve saved staff review.
        review = get_staff_review(return_id)

        assert review is not None
        assert review["review_id"] == approved["review_id"]
        assert review["return_id"] == return_id
        print("Test 2: PASS - Staff review retrieved")

        # Test 3: Verify recommendation and override.
        assert review["recommended_route"] == "Restock"
        assert review["final_route"] == "Refurbish"
        assert review["was_overridden"] is True
        assert review["override_reason"] == (
            "Packaging requires replacement"
        )
        print("Test 3: PASS - Override details correct")

        # Test 4: Verify staff identity and timestamp.
        assert review["staff_id"] == staff_id
        assert review["staff_name"] == "Review Retrieval Staff"
        assert review["reviewed_at"] is not None
        print("Test 4: PASS - Staff and timestamp correct")

        # Test 5: Nonexistent return has no review.
        assert get_staff_review(-1) is None
        print("Test 5: PASS - Nonexistent return handled")

finally:
    conn.rollback()
    conn.close()
    print("--------------------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
