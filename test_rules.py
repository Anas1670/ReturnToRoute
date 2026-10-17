from app.rules import recommend_route

test_cases = [
    ("new", "sealed", "working", "Restock"),
    ("good", "opened", "working", "Restock"),
    ("damaged", "opened", "partially_working", "Refurbish"),
    ("good", "opened", "not_working", "Recycle"),
    ("severely_damaged", "damaged", "not_working", "Dispose"),
    ("damaged", "missing", "working", "Refurbish"),
]

print("\nReturn-to-Route Decision Engine Tests")
print("--------------------------------------")

passed = 0

for i, (condition, packaging, functionality, expected) in enumerate(
    test_cases, start=1
):
    result = recommend_route(condition, packaging, functionality)
    actual = result["route"]

    if actual == expected:
        print(f"Test {i}: PASS - {actual}")
        passed += 1
    else:
        print(f"Test {i}: FAIL - Expected {expected}, got {actual}")

print("--------------------------------------")
print(f"Results: {passed}/{len(test_cases)} tests passed")

# Verify invalid input is rejected.
try:
    recommend_route("invalid", "sealed", "working")
    print("Invalid Input Test: FAIL")
except ValueError:
    print("Invalid Input Test: PASS")
