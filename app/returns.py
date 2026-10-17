from datetime import date
from app.db import get_db_connection
from app.rules import recommend_route


def create_return_request(
    customer_id,
    product_id,
    purchase_date,
    return_reason,
    item_condition,
    packaging_condition,
    functionality,
):
    """
    Create a customer return request in PostgreSQL.

    A new return starts with the status 'Submitted'.
    No routing decision is approved or finalized here.
    """

    # Validate the product conditions using our existing rules.
    recommend_route(
        item_condition,
        packaging_condition,
        functionality,
    )

    # Validate the purchase date.
    if isinstance(purchase_date, str):
        purchase_date = date.fromisoformat(purchase_date)

    if not isinstance(purchase_date, date):
        raise ValueError("Invalid purchase date")

    if purchase_date > date.today():
        raise ValueError("Purchase date cannot be in the future")

    # Validate the return reason.
    if not isinstance(return_reason, str) or not return_reason.strip():
        raise ValueError("Return reason is required")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO return_requests (
                    customer_id,
                    product_id,
                    purchase_date,
                    return_reason,
                    item_condition,
                    packaging_condition,
                    functionality,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Submitted')
                RETURNING return_id, status;
                """,
                (
                    customer_id,
                    product_id,
                    purchase_date,
                    return_reason.strip(),
                    item_condition,
                    packaging_condition,
                    functionality,
                ),
            )

            result = cur.fetchone()

    return {
        "return_id": result[0],
        "status": result[1],
    }
