import re

from psycopg.errors import UniqueViolation
from werkzeug.security import generate_password_hash

from app.db import get_db_connection


def register_customer(full_name, email, password):
    """
    Register a new customer account.

    Passwords are hashed before being saved.
    Public registration always creates a customer.
    """

    if not isinstance(full_name, str) or not full_name.strip():
        raise ValueError("Full name is required")

    if not isinstance(email, str) or not email.strip():
        raise ValueError("Email address is required")

    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("Password must contain at least 8 characters")

    full_name = full_name.strip()
    email = email.strip().lower()

    if len(full_name) > 150:
        raise ValueError("Full name is too long")

    if len(email) > 255 or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+", email
    ):
        raise ValueError("Invalid email address")

    password_hash = generate_password_hash(password)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (
                        full_name,
                        email,
                        password_hash,
                        role
                    )
                    VALUES (%s, %s, %s, 'customer')
                    RETURNING user_id;
                    """,
                    (
                        full_name,
                        email,
                        password_hash,
                    ),
                )

                user_id = cur.fetchone()[0]

    except UniqueViolation:
        raise ValueError("Email address is already registered") from None

    return {
        "user_id": user_id,
        "full_name": full_name,
        "email": email,
        "role": "customer",
    }
