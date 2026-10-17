from app.db import get_db_connection


def get_return_history(return_id):
    """
    Retrieve all recorded status changes for a return.

    Returns a list of dictionaries ordered from oldest to newest.
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    history_id,
                    return_id,
                    changed_by,
                    old_status,
                    new_status,
                    changed_at
                FROM return_status_history
                WHERE return_id = %s
                ORDER BY changed_at ASC, history_id ASC;
                """,
                (return_id,),
            )

            rows = cur.fetchall()
            columns = [column.name for column in cur.description]

            return [
                dict(zip(columns, row))
                for row in rows
            ]
