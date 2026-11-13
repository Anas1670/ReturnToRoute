"""Deterministic demo-only returnless-refund policy; no real money moves."""
from decimal import Decimal

MAX_PRICE = Decimal("25.00")

def evaluate_returnless_refund(purchase_price, item_condition, packaging_condition, functionality):
    price = Decimal(str(purchase_price))
    if price < 0:
        raise ValueError("Invalid purchase price")
    # Illustrative, transparent economics; tune before a real deployment.
    shipping = Decimal("8.00")
    inspection = Decimal("5.00")
    handling = Decimal("4.00")
    recovery_cost = shipping + inspection + handling
    factor = Decimal("0.80")
    if item_condition == "good": factor *= Decimal("0.75")
    elif item_condition == "damaged": factor *= Decimal("0.25")
    elif item_condition == "severely_damaged": factor = Decimal("0")
    if functionality == "partially_working": factor *= Decimal("0.50")
    elif functionality == "not_working": factor = Decimal("0")
    if packaging_condition in {"damaged", "missing"}: factor *= Decimal("0.80")
    recoverable = (price * factor).quantize(Decimal("0.01"))
    eligible = price <= MAX_PRICE and recovery_cost > recoverable
    return {"eligible": eligible, "purchase_price": price,
            "recovery_cost": recovery_cost, "recoverable_value": recoverable}
