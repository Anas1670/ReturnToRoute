
from app.db import get_db_connection


def verify_purchased_item(
    customer_id,
    product_id,
    order_item_id,
    conn=None,
):
    """
    Verify that a purchased item belongs to the customer
    and matches the product being returned.

    When conn is provided, reuse the caller's transaction.
    Otherwise, open a connection for standalone verification.
    """

    if type(order_item_id) is not int or order_item_id <= 0:
        raise ValueError("A valid order item ID is required")

    if conn is None:
        with get_db_connection() as new_conn:
            return verify_purchased_item(
                customer_id,
                product_id,
                order_item_id,
                conn=new_conn,
            )

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                oi.product_id,
                oi.quantity
            FROM order_items oi
            JOIN orders o
                ON oi.order_id = o.order_id
            WHERE oi.order_item_id = %s
              AND o.customer_id = %s
            FOR UPDATE OF oi, o;
            """,
            (order_item_id, customer_id),
        )

        result = cur.fetchone()

    if result is None:
        raise ValueError(
            "Purchased item not found for this customer"
        )

    purchased_product_id, quantity = result

    if purchased_product_id != product_id:
        raise ValueError(
            "Purchased item does not match the selected product"
        )

    if quantity != 1:
        raise ValueError(
            "Only single-unit purchased items are supported"
        )

    return True
