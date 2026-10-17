"""
Return-to-Route status transition rules.

These rules define which status changes are permitted.
Staff approval is handled separately.
"""

ALLOWED_TRANSITIONS = {
    "Submitted": {"Pending Inspection", "Cancelled"},
    "Pending Inspection": {"Pending Approval", "Cancelled"},
    "Pending Approval": {"Cancelled"},
    "Approved": {"Processing"},
    "Processing": {"Completed"},
    "Completed": set(),
    "Cancelled": set(),
}


def validate_status_transition(old_status, new_status):
    """
    Validate a requested status transition.

    Approval must occur through the dedicated staff
    approval function, not through ordinary status updates.
    """

    if old_status not in ALLOWED_TRANSITIONS:
        raise ValueError("Invalid current return status")

    if new_status not in ALLOWED_TRANSITIONS:
        raise ValueError("Invalid new return status")

    if new_status not in ALLOWED_TRANSITIONS[old_status]:
        raise ValueError(
            f"Status transition from '{old_status}' "
            f"to '{new_status}' is not permitted"
        )

    return True
