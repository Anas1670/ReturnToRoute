from unittest.mock import patch
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app.db import get_db_connection
from app.staff_queries import get_staff_returns

def test_staff_returns():
    """
    Verify that staff return retrieval produces a list.
    """

    results = get_staff_returns()

    assert isinstance(results, list), (
        "Staff return retrieval should return a list."
    )

    print("Test 1: PASS - Staff retrieval returns a list")


if __name__ == "__main__":
    print("Return-to-Route Staff Retrieval Tests")
    print("-------------------------------------")

    test_staff_returns()
	    # Test 2: Empty database returns an empty list.
    results = get_staff_returns()

    assert results == [], (
        "Expected an empty list because no return requests exist."
    )

    print("Test 2: PASS - Empty database handled correctly")
    print("-------------------------------------")
    print("All staff retrieval tests passed.")
