"""
Role-based permissions for return status changes.
"""

STAFF_ONLY_STATUSES = {
    "Pending Inspection",
    "Pending Approval",
    "Processing",
    "Completed",
}


def validate_status_permission(
    user_role,
    new_status,
    is_owner=False,
):
    """
    Check whether a user may request a status change.

    Workflow transition validation is handled separately.
    """

    if user_role not in {"customer", "staff"}:
        raise ValueError("Invalid user role")

    if new_status == "Approved":
        raise ValueError(
            "Approval requires the dedicated staff approval function"
        )

    if user_role == "staff":
        return True

    if new_status == "Cancelled" and is_owner:
        return True

    raise PermissionError(
        "User is not authorized to perform this status change"
    )
