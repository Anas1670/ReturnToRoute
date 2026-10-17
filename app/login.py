from werkzeug.security import check_password_hash

from app.db import get_db_connection
from app.models import User


def authenticate_user(email, password):
    """
    Authenticate a customer or staff member.

    Returns a User object for valid credentials,
    or None for invalid credentials.
    """

    if not isinstance(email, str) or not isinstance(password, str):
        return None

    email = email.strip().lower()

    if not email or not password:
        return None

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    user_id,
                    full_name,
                    email,
                    password_hash,
                    role
                FROM users
                WHERE email = %s;
                """,
                (email,),
            )

            row = cur.fetchone()

    if row is None:
        return None

    user = User(*row)

    if not check_password_hash(user.password_hash, password):
        return None

    return user
