
from datetime import date

from app.db import get_db_connection
from app.orders import verify_purchased_item
from app.rules import recommend_route


def create_return_request(
    customer_id,
    product_id,
    purchase_date,
    return_reason,
    item_condition,
    packaging_condition,
    functionality,
    order_item_id=None,
):
    """
    Create a customer return request for a verified purchase.

    New returns require an order item ID.
    Existing historical returns remain unchanged.
    """

    # Validate product conditions.
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

    # Require a purchased item for every new return.
    if type(order_item_id) is not int or order_item_id <= 0:
        raise ValueError("A valid order item ID is required")

    with get_db_connection() as conn:
        # Verify the purchase inside the same transaction.
        verify_purchased_item(
            customer_id=customer_id,
            product_id=product_id,
            order_item_id=order_item_id,
            conn=conn,
        )

        with conn.cursor() as cur:
            # Confirm the submitted purchase date matches the order.
            cur.execute(
                """
                SELECT o.order_date
                FROM orders o
                JOIN order_items oi
                    ON oi.order_id = o.order_id
                WHERE oi.order_item_id = %s;
                """,
                (order_item_id,),
            )

            order_row = cur.fetchone()

            if order_row is None or order_row[0] != purchase_date:
                raise ValueError(
                    "Purchase date does not match the order"
                )

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
                    order_item_id,
                    status
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, 'Submitted'
                )
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
                    order_item_id,
                ),
            )

            result = cur.fetchone()

    return {
        "return_id": result[0],
        "status": result[1],
    }
