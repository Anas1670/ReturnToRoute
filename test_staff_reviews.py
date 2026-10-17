from datetime import date
from unittest.mock import patch
from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.returns import create_return_request
from app.decisions import save_routing_decision
from app.status import update_return_status
from app.reviews import approve_routing_decision

print("\nReturn-to-Route Staff Approval Tests")
print("------------------------------------")

conn = get_db_connection()


class TestConnection:
    def __enter__(self):
        return conn

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def create_test_return(customer_id, product_id, staff_id):
    created = create_return_request(
        customer_id=customer_id,
        product_id=product_id,
        purchase_date=date.today(),
        return_reason="Product did not meet expectations",
        item_condition="good",
        packaging_condition="opened",
        functionality="working",
    )

    return_id = created["return_id"]
    decision = save_routing_decision(return_id)

    update_return_status(
        return_id,
        "Pending Inspection",
        changed_by=staff_id,
    )

    update_return_status(
        return_id,
        "Pending Approval",
        changed_by=staff_id,
    )

    return return_id, decision["decision_id"]


try:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (
                full_name, email, password_hash, role
            )
            VALUES (%s, %s, %s, 'customer')
            RETURNING user_id;
            """,
            (
                "Approval Test Customer",
                "approval-customer@example.com",
                generate_password_hash("temporary-test-password"),
            ),
        )
        customer_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO users (
                full_name, email, password_hash, role
            )
            VALUES (%s, %s, %s, 'staff')
            RETURNING user_id;
            """,
            (
                "Approval Test Staff",
                "approval-staff@example.com",
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
            ("Test Headphones", "Electronics", 79.99),
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
    ):

        # Test 1: Staff accepts recommendation.
        return_id, decision_id = create_test_return(
            customer_id, product_id, staff_id
        )

        result = approve_routing_decision(
            return_id=return_id,
            decision_id=decision_id,
            staff_id=staff_id,
            final_route="Restock",
        )

        assert result["status"] == "Approved"
        assert result["was_overridden"] is False

        with conn.cursor() as cur:
            cur.execute(
                "SELECT status FROM return_requests WHERE return_id = %s",
                (return_id,),
            )
            assert cur.fetchone()[0] == "Approved"

            cur.execute(
                """
                SELECT COUNT(*)
                FROM return_status_history
                WHERE return_id = %s
                  AND old_status = 'Pending Approval'
                  AND new_status = 'Approved';
                """,
                (return_id,),
            )
            assert cur.fetchone()[0] == 1

        print("Test 1: PASS - Staff approval and history saved")

        # Test 2: Staff overrides with a reason.
        return_id2, decision_id2 = create_test_return(
            customer_id, product_id, staff_id
        )

        override = approve_routing_decision(
            return_id=return_id2,
            decision_id=decision_id2,
            staff_id=staff_id,
            final_route="Refurbish",
            override_reason="Packaging and accessories need replacement",
        )

        assert override["was_overridden"] is True
        assert override["final_route"] == "Refurbish"
        assert override["override_reason"]

        print("Test 2: PASS - Valid override approved")

        # Test 3: Override without reason is rejected.
        return_id3, decision_id3 = create_test_return(
            customer_id, product_id, staff_id
        )

        try:
            approve_routing_decision(
                return_id=return_id3,
                decision_id=decision_id3,
                staff_id=staff_id,
                final_route="Recycle",
            )
        except ValueError as error:
            assert str(error) == "Override reason is required"
            print("Test 3: PASS - Missing override reason rejected")
        else:
            raise AssertionError("Override without reason was accepted")

        # Test 4: Customer cannot approve.
        try:
            approve_routing_decision(
                return_id=return_id3,
                decision_id=decision_id3,
                staff_id=customer_id,
                final_route="Restock",
            )
        except ValueError as error:
            assert "Only staff members" in str(error)
            print("Test 4: PASS - Customer approval rejected")
        else:
            raise AssertionError("Customer approval was accepted")

        # Test 5: Duplicate approval is rejected.
        try:
            approve_routing_decision(
                return_id=return_id,
                decision_id=decision_id,
                staff_id=staff_id,
                final_route="Restock",
            )
        except ValueError:
            print("Test 5: PASS - Duplicate approval rejected")
        else:
            raise AssertionError("Duplicate approval was accepted")

finally:
    conn.rollback()
    conn.close()
    print("------------------------------------")
    print("Test transaction rolled back.")
    print("Temporary records were not saved.")
