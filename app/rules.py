def recommend_route(item_condition, packaging_condition, functionality):
    """
    Recommend a return route based on product condition.

    This function only recommends a route.
    Staff approval is required before finalization.
    """

    valid_conditions = {"new", "good", "damaged", "severely_damaged"}
    valid_packaging = {"sealed", "opened", "damaged", "missing"}
    valid_functionality = {
        "working",
        "partially_working",
        "not_working",
        "not_applicable",
    }

    if item_condition not in valid_conditions:
        raise ValueError("Invalid item condition")

    if packaging_condition not in valid_packaging:
        raise ValueError("Invalid packaging condition")

    if functionality not in valid_functionality:
        raise ValueError("Invalid functionality")

    if item_condition == "severely_damaged":
        return {
            "route": "Dispose",
            "rule": "SEVERELY_DAMAGED",
            "explanation": "The product is severely damaged and is recommended for disposal.",
        }

    if functionality == "not_working":
        return {
            "route": "Recycle",
            "rule": "NOT_WORKING",
            "explanation": "The product is not functional and is recommended for recycling.",
        }

    if functionality == "partially_working":
        return {
            "route": "Refurbish",
            "rule": "PARTIALLY_WORKING",
            "explanation": "The product is partially functional and may be repaired.",
        }

    if (
        item_condition in {"new", "good"}
        and functionality in {"working", "not_applicable"}
        and packaging_condition in {"sealed", "opened"}
    ):
        return {
            "route": "Restock",
            "rule": "GOOD_WORKING_CONDITION",
            "explanation": "The product is in good condition and suitable for restocking.",
        }

    return {
        "route": "Refurbish",
        "rule": "REQUIRES_INSPECTION",
        "explanation": "The product requires inspection or restoration before reuse.",
    }
