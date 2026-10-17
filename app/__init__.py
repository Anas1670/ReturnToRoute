import os

from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv


load_dotenv()

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    """
    Load an authenticated user from PostgreSQL.
    """
    from app.models import User

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return None

    return User.get_by_id(user_id)


def create_app():
    app = Flask(__name__)

    # Load the secret key from .env.
    secret_key = os.getenv("SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY is missing from the .env file"
        )

    app.config["SECRET_KEY"] = secret_key

    # Initialize Flask-Login.
    login_manager.init_app(app)

    # Register the homepage and recommendation API.
    from app.routes import main
    app.register_blueprint(main)

    # Register login and logout endpoints.
    from app.auth_routes import auth
    app.register_blueprint(auth)

    # Register protected customer and staff dashboards.
    from app.dashboard_routes import dashboard
    app.register_blueprint(dashboard)

    return app
