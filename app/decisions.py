from app.db import get_db_connection
from app.rules import recommend_route


def save_routing_decision(return_id):
    """
    Generate and save a routing recommendation.

    This function does not approve or finalize the route.
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:

            # Lock the return while generating its recommendation.
            cur.execute(
                """
                SELECT
                    item_condition,
                    packaging_condition,
                    functionality,
                    status
                FROM return_requests
                WHERE return_id = %s
                FOR UPDATE;
                """,
                (return_id,),
            )

            row = cur.fetchone()

            if row is None:
                raise ValueError("Return request not found")

            item_condition, packaging_condition, functionality, status = row

            if status not in {
                "Submitted",
                "Pending Inspection",
                "Pending Approval",
            }:
                raise ValueError(
                    "Cannot recommend a route for this return status"
                )

            # Prevent duplicate decisions in this initial workflow.
            cur.execute(
                """
                SELECT decision_id
                FROM routing_decisions
                WHERE return_id = %s
                LIMIT 1;
                """,
                (return_id,),
            )

            if cur.fetchone() is not None:
                raise ValueError(
                    "A routing decision already exists for this return"
                )

            recommendation = recommend_route(
                item_condition,
                packaging_condition,
                functionality,
            )

            cur.execute(
                """
                INSERT INTO routing_decisions (
                    return_id,
                    recommended_route,
                    rule_applied,
                    explanation
                )
                VALUES (%s, %s, %s, %s)
                RETURNING decision_id;
                """,
                (
                    return_id,
                    recommendation["route"],
                    recommendation["rule"],
                    recommendation["explanation"],
                ),
            )

            decision_id = cur.fetchone()[0]

    return {
        "decision_id": decision_id,
        "return_id": return_id,
        "recommended_route": recommendation["route"],
        "rule_applied": recommendation["rule"],
        "explanation": recommendation["explanation"],
        "approval_required": True,
    }
