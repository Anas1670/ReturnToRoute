"""Transactional, idempotent demo data for new accounts."""
from datetime import date, timedelta
from uuid import uuid4
import random
from werkzeug.security import generate_password_hash


def seed_customer(cur, customer_id, count=20):
    cur.execute("SELECT COUNT(*) FROM orders WHERE customer_id = %s", (customer_id,))
    if cur.fetchone()[0]:
        return 0
    cur.execute("SELECT product_id, original_price FROM products ORDER BY random() LIMIT %s", (count,))
    products = cur.fetchall()
    if len(products) < count:
        raise ValueError(f"Product catalog needs at least {count} products; found {len(products)}")
    for product_id, price in products:
        order_date = date.today() - timedelta(days=random.randint(2, 25))
        cur.execute("""INSERT INTO orders (order_number, customer_id, order_date)
                       VALUES (%s, %s, %s) RETURNING order_id""",
                    (f"RTR-DEMO-{uuid4().hex[:20]}", customer_id, order_date))
        order_id = cur.fetchone()[0]
        cur.execute("""INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                       VALUES (%s, %s, 1, %s)""", (order_id, product_id, price))
    return len(products)


def seed_staff(cur, staff_id, count=50):
    cur.execute("SELECT COUNT(*) FROM staff_return_assignments WHERE staff_id = %s", (staff_id,))
    if cur.fetchone()[0]:
        return 0
    cur.execute("SELECT product_id, original_price FROM products ORDER BY random() LIMIT %s", (count,))
    products = cur.fetchall()
    if len(products) < count:
        raise ValueError(f"Product catalog needs at least {count} products; found {len(products)}")
    reasons = ['Wrong size', 'No longer needed', 'Damaged in shipping', 'Not as expected', 'Defective item']
    for index, (product_id, price) in enumerate(products, 1):
        tag = uuid4().hex
        cur.execute("""INSERT INTO users (full_name, email, password_hash, role)
                       VALUES (%s, %s, %s, 'customer') RETURNING user_id""",
                    (f"Demo Customer {index}", f"demo-{tag}@example.invalid",
                     generate_password_hash(uuid4().hex)))
        customer_id = cur.fetchone()[0]
        purchase_date = date.today() - timedelta(days=random.randint(2, 25))
        cur.execute("""INSERT INTO orders (order_number, customer_id, order_date)
                       VALUES (%s, %s, %s) RETURNING order_id""",
                    (f"RTR-STAFF-{tag[:20]}", customer_id, purchase_date))
        order_id = cur.fetchone()[0]
        cur.execute("""INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                       VALUES (%s, %s, 1, %s) RETURNING order_item_id""",
                    (order_id, product_id, price))
        item_id = cur.fetchone()[0]
        condition = random.choice(['new', 'good', 'damaged', 'severely_damaged'])
        packaging = random.choice(['sealed', 'opened', 'damaged', 'missing'])
        functionality = random.choice(['working', 'partially_working', 'not_working'])
        cur.execute("""INSERT INTO return_requests
                       (customer_id, product_id, purchase_date, return_reason,
                        item_condition, packaging_condition, functionality, order_item_id, status)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Submitted') RETURNING return_id""",
                    (customer_id, product_id, purchase_date, random.choice(reasons),
                     condition, packaging, functionality, item_id))
        return_id = cur.fetchone()[0]
        cur.execute("""INSERT INTO staff_return_assignments (return_id, staff_id, is_demo)
                       VALUES (%s, %s, TRUE)""", (return_id, staff_id))
    return len(products)


def assert_staff_assignment(staff_id, return_id):
    from app.db import get_db_connection
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT 1 FROM staff_return_assignments
                           WHERE staff_id = %s AND return_id = %s""", (staff_id, return_id))
            if cur.fetchone() is None:
                raise PermissionError('Return case is not assigned to this staff account')
