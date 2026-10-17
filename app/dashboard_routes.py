from flask import Blueprint, jsonify
from flask_login import current_user

from app.decorators import role_required
from app.customer_queries import get_customer_returns


dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/api/customer/dashboard", methods=["GET"])
@role_required("customer")
def customer_dashboard():
    """
    Return customer information and their return requests.
    """

    customer_id = int(current_user.id)

    returns = get_customer_returns(customer_id)

    return jsonify({
        "message": "Welcome to your customer dashboard",
        "user": {
            "user_id": customer_id,
            "full_name": current_user.full_name,
            "role": current_user.role
        },
        "return_count": len(returns),
        "returns": returns,
        "features": [
            "Submit return requests",
            "Track return status",
            "View routing decisions"
        ]
    }), 200


@dashboard.route("/api/staff/dashboard", methods=["GET"])
@role_required("staff")
def staff_dashboard():
    """
    Protected staff dashboard endpoint.
    """

    return jsonify({
        "message": "Welcome to your staff dashboard",
        "user": {
            "user_id": int(current_user.id),
            "full_name": current_user.full_name,
            "role": current_user.role
        },
        "features": [
            "Review return requests",
            "Approve routing decisions",
            "Override recommendations",
            "Manage return processing"
        ]
    }), 200
