from app.db import get_db_connection


def get_return_request(return_id):
    """
    Retrieve a return request by ID.

    Returns a dictionary if found, or None if not found.
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    return_id,
                    customer_id,
                    product_id,
                    purchase_date,
                    return_reason,
                    item_condition,
                    packaging_condition,
                    functionality,
                    status,
                    submitted_at
                FROM return_requests
                WHERE return_id = %s;
                """,
                (return_id,),
            )

            row = cur.fetchone()

            if row is None:
                return None

            columns = [column.name for column in cur.description]

            return dict(zip(columns, row))
