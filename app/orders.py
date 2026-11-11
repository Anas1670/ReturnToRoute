
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


def get_customer_purchases(customer_id):
    """
    Retrieve purchased items belonging to one customer.
    Include existing returns and return eligibility.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    o.order_id,
                    o.order_number,
                    o.order_date,
                    oi.order_item_id,
                    oi.product_id,
                    p.product_name,
                    p.category,
                    oi.quantity,
                    oi.unit_price,
                    rr.return_id
                FROM orders o
                JOIN order_items oi
                    ON o.order_id = oi.order_id
                JOIN products p
                    ON oi.product_id = p.product_id
                LEFT JOIN return_requests rr
                    ON rr.order_item_id = oi.order_item_id
                WHERE o.customer_id = %s
                ORDER BY o.order_date DESC, oi.order_item_id DESC;
                """,
                (customer_id,),
            )

            columns = [
                column.name for column in cur.description
            ]
            rows = cur.fetchall()

    purchases = []

    for row in rows:
        item = dict(zip(columns, row))

        item["order_date"] = item["order_date"].isoformat()
        item["unit_price"] = float(item["unit_price"])

        item["has_return"] = item["return_id"] is not None

        item["can_request_return"] = (
            not item["has_return"]
            and item["quantity"] == 1
        )

        if item["has_return"]:
            item["return_eligibility_reason"] = (
                "A return already exists for this purchased item."
            )
        elif item["quantity"] != 1:
            item["return_eligibility_reason"] = (
                "Only single-unit purchased items are supported."
            )
        else:
            item["return_eligibility_reason"] = None

        purchases.append(item)

    return purchases
