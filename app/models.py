from flask_login import UserMixin

from app.db import get_db_connection


class User(UserMixin):
    """
    Represents an authenticated Return-to-Route user.
    """

    def __init__(self, user_id, full_name, email, password_hash, role):
        self.id = str(user_id)
        self.full_name = full_name
        self.email = email
        self.password_hash = password_hash
        self.role = role

    @staticmethod
    def get_by_id(user_id):
        """
        Retrieve a user from PostgreSQL by user ID.
        """

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
                    WHERE user_id = %s;
                    """,
                    (user_id,),
                )

                row = cur.fetchone()

                if row is None:
                    return None

                return User(*row)
