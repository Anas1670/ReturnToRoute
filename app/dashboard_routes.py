
from flask import Blueprint, jsonify, request
from flask_login import current_user
from psycopg.errors import UniqueViolation

from app.returns import create_return_request
from app.status import update_return_status
from app.decisions import save_routing_decision
from app.reviews import approve_routing_decision
from app.decorators import role_required
from app.customer_queries import get_customer_returns
from app.staff_queries import get_staff_returns
from app.orders import get_customer_purchases
from app.queries import get_return_request
from app.history import get_return_history

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/api/customer/dashboard", methods=["GET"])
@role_required("customer")
def customer_dashboard():
    """
    Return customer information and their return requests.
    """
    customer_id = int(current_user.id)
    returns = get_customer_returns(customer_id)
    purchases = get_customer_purchases(customer_id)

    return jsonify({
        "message": "Welcome to your customer dashboard",
        "user": {
            "user_id": customer_id,
            "full_name": current_user.full_name,
            "role": current_user.role
        },
        "return_count": len(returns),
        "returns": returns,
        "purchase_count": len(purchases),
        "purchases": purchases,
        "features": [
            "Submit return requests",
            "Track return status",
            "View return status history",
            "View purchase history",
            "View routing decisions"
        ]
    }), 200


@dashboard.route("/api/customer/purchases", methods=["GET"])
@role_required("customer")
def customer_purchases():
    """
    Return purchase history for the authenticated customer.
    """
    customer_id = int(current_user.id)
    purchases = get_customer_purchases(customer_id)

    return jsonify({
        "message": "Customer purchase history retrieved successfully.",
        "purchase_count": len(purchases),
        "purchases": purchases,
    }), 200


@dashboard.route(
    "/api/customer/returns/<int:return_id>/history",
    methods=["GET"]
)
@role_required("customer")
def customer_return_history(return_id):
    """
    Retrieve status history for a return owned by the
    authenticated customer.
    """
    customer_id = int(current_user.id)
    return_request = get_return_request(return_id)

    if return_request is None:
        return jsonify({
            "error": "Return request not found."
        }), 404

    if int(return_request["customer_id"]) != customer_id:
        return jsonify({
            "error": "Return request not found."
        }), 404

    history = get_return_history(return_id)

    return jsonify({
        "message": "Return status history retrieved successfully.",
        "return_id": return_id,
        "current_status": return_request["status"],
        "history_count": len(history),
        "history": history
    }), 200


@dashboard.route("/api/staff/dashboard", methods=["GET"])
@role_required("staff")
def staff_dashboard():
    """
    Protected staff dashboard endpoint.
    Return staff information and customer return requests.
    """
    staff_id = int(current_user.id)
    returns = get_staff_returns()

    return jsonify({
        "message": "Welcome to your staff dashboard",
        "user": {
            "user_id": staff_id,
            "full_name": current_user.full_name,
            "role": current_user.role
        },
        "return_count": len(returns),
        "returns": returns,
        "features": [
            "Review return requests",
            "Approve routing decisions",
            "Override recommendations",
            "Manage return processing"
        ]
    }), 200


@dashboard.route("/api/customer/returns", methods=["POST"])
@role_required("customer")
def submit_customer_return():
    """
    Allow an authenticated customer to submit a return request.
    The customer ID comes from the authenticated session.
    """
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required."
        }), 400

    required_fields = [
        "product_id",
        "order_item_id",
        "purchase_date",
        "return_reason",
        "item_condition",
        "packaging_condition",
        "functionality",
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400

    product_id = data["product_id"]

    if type(product_id) is not int or product_id <= 0:
        return jsonify({
            "error": "A valid product ID is required."
        }), 400

    order_item_id = data["order_item_id"]

    if type(order_item_id) is not int or order_item_id <= 0:
        return jsonify({
            "error": "A valid order item ID is required."
        }), 400

    try:
        result = create_return_request(
            customer_id=int(current_user.id),
            product_id=product_id,
            purchase_date=data["purchase_date"],
            return_reason=data["return_reason"],
            item_condition=data["item_condition"],
            packaging_condition=data["packaging_condition"],
            functionality=data["functionality"],
            order_item_id=order_item_id,
        )

    except (ValueError, TypeError, OverflowError) as error:
        return jsonify({
            "error": str(error)
        }), 400

    except UniqueViolation as error:
        if error.diag.constraint_name == "unique_return_order_item":
            return jsonify({
                "error": "A return already exists for this purchased item."
            }), 409
        raise

    return jsonify({
        "message": "Return request submitted successfully.",
        "return": result
    }), 201


@dashboard.route(
    "/api/staff/returns/<int:return_id>/status",
    methods=["PATCH"]
)
@role_required("staff")
def staff_update_return_status(return_id):
    """
    Allow authenticated staff to update a return's status.
    """
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required."
        }), 400

    new_status = data.get("new_status")

    if not isinstance(new_status, str) or not new_status.strip():
        return jsonify({
            "error": "A valid new_status is required."
        }), 400

    try:
        result = update_return_status(
            return_id=return_id,
            new_status=new_status,
            changed_by=int(current_user.id)
        )

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    except PermissionError as error:
        return jsonify({
            "error": str(error)
        }), 403

    return jsonify({
        "message": "Return status updated successfully.",
        "return": result
    }), 200


@dashboard.route(
    "/api/staff/returns/<int:return_id>/recommend",
    methods=["POST"]
)
@role_required("staff")
def staff_generate_recommendation(return_id):
    """
    Generate and save a routing recommendation for a return.
    Only authenticated staff members can perform this action.
    """
    try:
        result = save_routing_decision(return_id=return_id)

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    return jsonify({
        "message": "Routing recommendation generated successfully.",
        "decision": result
    }), 201


@dashboard.route(
    "/api/staff/returns/<int:return_id>/approve",
    methods=["POST"]
)
@role_required("staff")
def staff_approve_return(return_id):
    """
    Approve or override a routing recommendation.
    Only authenticated staff can perform this action.
    """
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required."
        }), 400

    decision_id = data.get("decision_id")
    final_route = data.get("final_route")
    override_reason = data.get("override_reason")

    if type(decision_id) is not int or decision_id <= 0:
        return jsonify({
            "error": "A valid decision_id is required."
        }), 400

    if not isinstance(final_route, str) or not final_route.strip():
        return jsonify({
            "error": "A valid final_route is required."
        }), 400

    try:
        result = approve_routing_decision(
            return_id=return_id,
            decision_id=decision_id,
            staff_id=int(current_user.id),
            final_route=final_route,
            override_reason=override_reason
        )

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    except PermissionError as error:
        return jsonify({
            "error": str(error)
        }), 403

    return jsonify({
        "message": "Routing decision approved successfully.",
        "review": result
    }), 200
