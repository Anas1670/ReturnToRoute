from app.db import get_db_connection

VALID_ROUTES = {
    "Restock",
    "Refurbish",
    "Recycle",
    "Dispose",
}


def approve_routing_decision(
    return_id,
    decision_id,
    staff_id,
    final_route,
    override_reason=None,
):
    """
    Approve a routing decision or override its recommendation.

    Only a staff user can approve a decision.
    """

    if final_route not in VALID_ROUTES:
        raise ValueError("Invalid final route")

    with get_db_connection() as conn:
        with conn.cursor() as cur:

            # Verify that the approving user is staff.
            cur.execute(
                """
                SELECT role
                FROM users
                WHERE user_id = %s;
                """,
                (staff_id,),
            )

            staff = cur.fetchone()

            if staff is None or staff[0] != "staff":
                raise ValueError(
                    "Only staff members can approve routing decisions"
                )

            # Lock the return to serialize approval attempts.
            cur.execute(
                """
                SELECT status
                FROM return_requests
                WHERE return_id = %s
                FOR UPDATE;
                """,
                (return_id,),
            )

            row = cur.fetchone()

            if row is None:
                raise ValueError("Return request not found")

            if row[0] != "Pending Approval":
                raise ValueError(
                    "Return must be Pending Approval before approval"
                )

            # Retrieve the recommendation for this return.
            cur.execute(
                """
                SELECT recommended_route
                FROM routing_decisions
                WHERE decision_id = %s
                  AND return_id = %s;
                """,
                (decision_id, return_id),
            )

            decision = cur.fetchone()

            if decision is None:
                raise ValueError(
                    "Routing decision not found for this return"
                )

            recommended_route = decision[0]
            was_overridden = final_route != recommended_route

            if was_overridden:
                if (
                    not isinstance(override_reason, str)
                    or not override_reason.strip()
                ):
                    raise ValueError(
                        "Override reason is required"
                    )
                override_reason = override_reason.strip()
            else:
                override_reason = None

            # Prevent duplicate staff approvals.
            cur.execute(
                """
                SELECT review_id
                FROM staff_reviews
                WHERE return_id = %s
                LIMIT 1;
                """,
                (return_id,),
            )

            if cur.fetchone() is not None:
                raise ValueError(
                    "This return has already been reviewed"
                )

            # Save the staff review.
            cur.execute(
                """
                INSERT INTO staff_reviews (
                    return_id,
                    staff_id,
                    decision_id,
                    final_route,
                    was_overridden,
                    override_reason
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING review_id;
                """,
                (
                    return_id,
                    staff_id,
                    decision_id,
                    final_route,
                    was_overridden,
                    override_reason,
                ),
            )

            review_id = cur.fetchone()[0]

            # Update the return's status.
            cur.execute(
                """
                UPDATE return_requests
                SET status = 'Approved'
                WHERE return_id = %s;
                """,
                (return_id,),
            )

            # Record the status change in the audit history.
            cur.execute(
                """
                INSERT INTO return_status_history (
                    return_id,
                    changed_by,
                    old_status,
                    new_status
                )
                VALUES (%s, %s, 'Pending Approval', 'Approved');
                """,
                (return_id, staff_id),
            )

    return {
        "review_id": review_id,
        "return_id": return_id,
        "recommended_route": recommended_route,
        "final_route": final_route,
        "was_overridden": was_overridden,
        "override_reason": override_reason,
        "status": "Approved",
    }
