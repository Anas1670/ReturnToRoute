from app.db import get_db_connection
from app.workflow import validate_status_transition
from app.permissions import validate_status_permission


def update_return_status(return_id, new_status, changed_by=None):
    """
    Update a return's status with workflow and role checks.

    changed_by must be the authenticated user's database ID.
    The Flask layer must supply this ID from the server-side
    authenticated session, never from client-submitted data.
    """

    if changed_by is None:
        raise PermissionError(
            "An authenticated user is required to change return status"
        )

    with get_db_connection() as conn:
        with conn.cursor() as cur:

            # Retrieve the actual role from PostgreSQL.
            cur.execute(
                """
                SELECT role
                FROM users
                WHERE user_id = %s;
                """,
                (changed_by,),
            )

            user_row = cur.fetchone()

            if user_row is None:
                raise PermissionError("User not found")

            user_role = user_row[0]

            # Lock the return to prevent concurrent changes.
            cur.execute(
                """
                SELECT status, customer_id
                FROM return_requests
                WHERE return_id = %s
                FOR UPDATE;
                """,
                (return_id,),
            )

            return_row = cur.fetchone()

            if return_row is None:
                raise ValueError("Return request not found")

            old_status, customer_id = return_row

            if old_status == new_status:
                raise ValueError("Return already has this status")

            # Check whether this status transition is valid.
            validate_status_transition(old_status, new_status)

            # Determine whether the user owns this return.
            is_owner = (
                user_role == "customer"
                and customer_id == changed_by
            )

            # Check role-based permissions.
            validate_status_permission(
                user_role=user_role,
                new_status=new_status,
                is_owner=is_owner,
            )

            # Customers may only cancel their own
            # returns while they are still Submitted.
            if user_role == "customer":
                if not (
                    old_status == "Submitted"
                    and new_status == "Cancelled"
                    and is_owner
                ):
                    raise PermissionError(
                        "Customers may only cancel their own "
                        "submitted returns"
                    )

            # Update the return status.
            cur.execute(
                """
                UPDATE return_requests
                SET status = %s
                WHERE return_id = %s;
                """,
                (new_status, return_id),
            )

            # Record the status change for auditing.
            cur.execute(
                """
                INSERT INTO return_status_history (
                    return_id,
                    changed_by,
                    old_status,
                    new_status
                )
                VALUES (%s, %s, %s, %s)
                RETURNING history_id;
                """,
                (
                    return_id,
                    changed_by,
                    old_status,
                    new_status,
                ),
            )

            history_id = cur.fetchone()[0]

    return {
        "return_id": return_id,
        "history_id": history_id,
        "old_status": old_status,
        "new_status": new_status,
    }
