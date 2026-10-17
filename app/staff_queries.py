from app.db import get_db_connection


def get_staff_returns():
    """
    Retrieve return requests for the staff dashboard.

    Returns awaiting inspection or approval appear first.
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.return_id,
                    r.customer_id,
                    u.full_name,
                    p.product_name,
                    p.category,
                    r.return_reason,
                    r.item_condition,
                    r.packaging_condition,
                    r.functionality,
                    r.status,
                    r.submitted_at,
                    d.decision_id,
                    d.recommended_route
                FROM return_requests AS r
                JOIN users AS u
                    ON r.customer_id = u.user_id
                JOIN products AS p
                    ON r.product_id = p.product_id
                LEFT JOIN LATERAL (
                    SELECT
                        decision_id,
                        recommended_route
                    FROM routing_decisions
                    WHERE return_id = r.return_id
                    ORDER BY created_at DESC, decision_id DESC
                    LIMIT 1
                ) AS d ON TRUE
                ORDER BY
                    CASE r.status
                        WHEN 'Pending Inspection' THEN 1
                        WHEN 'Pending Approval' THEN 2
                        WHEN 'Submitted' THEN 3
                        WHEN 'Approved' THEN 4
                        WHEN 'Processing' THEN 5
                        WHEN 'Completed' THEN 6
                        WHEN 'Cancelled' THEN 7
                        ELSE 8
                    END,
                    r.submitted_at DESC,
                    r.return_id DESC;
                """
            )

            rows = cur.fetchall()

    return [
        {
            "return_id": row[0],
            "customer_id": row[1],
            "customer_name": row[2],
            "product_name": row[3],
            "category": row[4],
            "return_reason": row[5],
            "item_condition": row[6],
            "packaging_condition": row[7],
            "functionality": row[8],
            "status": row[9],
            "submitted_at": row[10].isoformat(),
            "decision_id": row[11],
            "recommended_route": row[12],
        }
        for row in rows
    ]
