from flask import Blueprint, request, jsonify
from app.rules import recommend_route
from app.staff_queries import get_staff_returns
main = Blueprint("main", __name__)


@main.route("/")
def home():
    return """
    <h1>Return-to-Route</h1>
    <h2>Smart Product Return Management System</h2>
    <p>Welcome to Return-to-Route!</p>
    <p>Our Flask application is running successfully.</p>
    """


@main.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required."
        }), 400

    required_fields = [
        "item_condition",
        "packaging_condition",
        "functionality"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400

    try:
        result = recommend_route(
            data["item_condition"],
            data["packaging_condition"],
            data["functionality"]
        )

        return jsonify({
            "recommended_route": result["route"],
            "rule_applied": result["rule"],
            "explanation": result["explanation"],
            "approval_required": True,
            "status": "Pending Approval"
        }), 200

    except (ValueError, TypeError) as error:
        return jsonify({
            "error": str(error)
        }), 400
