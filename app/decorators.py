from functools import wraps

from flask import jsonify
from flask_login import current_user


def role_required(required_role):
    """
    Restrict a Flask route to authenticated users
    with the specified role.
    """

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            if not current_user.is_authenticated:
                return jsonify({
                    "error": "Authentication required."
                }), 401

            if current_user.role != required_role:
                return jsonify({
                    "error": "Access denied."
                }), 403

            return function(*args, **kwargs)

        return wrapper

    return decorator
