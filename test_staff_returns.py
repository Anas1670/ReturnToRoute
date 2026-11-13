from app.staff_queries import get_staff_returns


def test_staff_returns():
    """
    Verify that staff return retrieval works
    with an existing database.
    """
    results = get_staff_returns()

    assert isinstance(results, list), (
        "Staff return retrieval should return a list."
    )

    print("PASS: Staff retrieval returns a list")


def test_staff_return_records():
    """
    Verify that retrieved return records are dictionaries.
    """
    results = get_staff_returns()

    assert all(isinstance(item, dict) for item in results), (
        "Every staff return should be a dictionary."
    )

    print("PASS: Staff return records have valid structure")


if __name__ == "__main__":
    print("Return-to-Route Staff Retrieval Tests")
    print("-------------------------------------")

    test_staff_returns()
    test_staff_return_records()

    print("-------------------------------------")
    print("All staff retrieval tests passed.")
