from app.db import get_db_connection


def get_staff_review(return_id):
    """
    Retrieve the latest staff review for a return.

    Returns a dictionary, or None if no review exists.
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sr.review_id,
                    sr.return_id,
                    sr.staff_id,
                    u.full_name AS staff_name,
                    rd.recommended_route,
                    rd.rule_applied,
                    rd.explanation,
                    sr.final_route,
                    sr.was_overridden,
                    sr.override_reason,
                    sr.reviewed_at
                FROM staff_reviews AS sr
                JOIN users AS u
                    ON sr.staff_id = u.user_id
                JOIN routing_decisions AS rd
                    ON sr.decision_id = rd.decision_id
                   AND sr.return_id = rd.return_id
                WHERE sr.return_id = %s
                ORDER BY sr.reviewed_at DESC, sr.review_id DESC
                LIMIT 1;
                """,
                (return_id,),
            )

            row = cur.fetchone()

            if row is None:
                return None

            columns = [
                column.name
                for column in cur.description
            ]

            return dict(zip(columns, row))
