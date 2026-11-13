from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    redirect,
    url_for
)
from flask_login import current_user

from app.rules import recommend_route


main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@main.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")


@main.route("/dashboard", methods=["GET"])
def dashboard_redirect():
    """Send each signed-in user to the dashboard for their role."""
    if not current_user.is_authenticated:
        return redirect(url_for("main.login_page"))

    if current_user.role == "customer":
        return redirect(url_for("main.customer_dashboard_page"))
    if current_user.role == "staff":
        return redirect(url_for("main.staff_dashboard_page"))

    return jsonify({"error": "Unsupported account role."}), 403


@main.route("/customer/dashboard", methods=["GET"])
def customer_dashboard_page():
    """
    Display the dashboard only to authenticated customers.
    """
    if not current_user.is_authenticated:
        return redirect(url_for("main.login_page"))

    if current_user.role != "customer":
        return redirect(url_for("main.dashboard_redirect"))

    return render_template("customer_dashboard.html")


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


@main.route("/staff/dashboard", methods=["GET"])
def staff_dashboard_page():
    """Display the staff dashboard to authenticated staff."""
    if not current_user.is_authenticated:
        return redirect(url_for("main.login_page"))

    if current_user.role != "staff":
        return redirect(url_for("main.dashboard_redirect"))

    return render_template("staff_dashboard.html")


@main.route("/faq", methods=["GET"])
def faq_page():
    return render_template("faq.html")
