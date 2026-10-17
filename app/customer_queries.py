from app.db import get_db_connection


def get_customer_returns(customer_id):
    """
    Retrieve return requests belonging to one customer.
    Most recently submitted returns appear first.
    """

    try:
        customer_id = int(customer_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid customer ID") from None

    if customer_id <= 0:
        raise ValueError("Invalid customer ID")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.return_id,
                    p.product_name,
                    p.category,
                    r.purchase_date,
                    r.return_reason,
                    r.item_condition,
                    r.packaging_condition,
                    r.functionality,
                    r.status,
                    r.submitted_at
                FROM return_requests AS r
                JOIN products AS p
                    ON r.product_id = p.product_id
                WHERE r.customer_id = %s
                ORDER BY r.submitted_at DESC, r.return_id DESC;
                """,
                (customer_id,),
            )

            rows = cur.fetchall()

    return [
        {
            "return_id": row[0],
            "product_name": row[1],
            "category": row[2],
            "purchase_date": row[3].isoformat(),
            "return_reason": row[4],
            "item_condition": row[5],
            "packaging_condition": row[6],
            "functionality": row[7],
            "status": row[8],
            "submitted_at": row[9].isoformat(),
        }
        for row in rows
    ]
