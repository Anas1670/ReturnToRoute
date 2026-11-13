from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from app.db import get_db_connection

BACKUP = Path(
    "backups/return_to_route_before_duplicate_cleanup.dump"
)

def main():
    if not BACKUP.is_file() or BACKUP.stat().st_size == 0:
        raise RuntimeError("Database backup missing or empty.")

    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    LOCK TABLE orders, order_items, products,
                    return_requests, simulated_returnless_refunds
                    IN SHARE ROW EXCLUSIVE MODE;
                """)

                cur.execute("""
                    SELECT product_id, original_price
                    FROM products
                    ORDER BY product_id;
                """)
                products = cur.fetchall()

                cur.execute("""
                    SELECT
                        o.customer_id,
                        oi.order_item_id,
                        oi.product_id,
                        oi.quantity,
                        EXISTS (
                            SELECT 1 FROM return_requests r
                            WHERE r.order_item_id = oi.order_item_id
                        ),
                        EXISTS (
                            SELECT 1 FROM simulated_returnless_refunds s
                            WHERE s.order_item_id = oi.order_item_id
                        )
                    FROM orders o
                    JOIN order_items oi
                        ON oi.order_id = o.order_id
                    ORDER BY o.customer_id, oi.order_item_id;
                """)

                customers = defaultdict(list)

                for customer, item, product, qty, returned, refunded in cur.fetchall():
                    customers[customer].append(
                        (item, product, qty, returned or refunded)
                    )

                changes = []

                for customer, items in customers.items():
                    groups = defaultdict(list)

                    for item in items:
                        groups[item[1]].append(item)

                    used = set(groups)
                    extras = []

                    for product, group in groups.items():
                        group.sort(key=lambda x: (not x[3], x[0]))
                        extras.extend(group[1:])

                    extras.sort(key=lambda x: x[0])

                    available = [
                        (pid, price)
                        for pid, price in products
                        if pid not in used
                    ]

                    if len(available) < len(extras):
                        raise RuntimeError(
                            f"Not enough products for customer {customer}"
                        )

                    for old, replacement in zip(extras, available):
                        item_id, old_product, qty, protected = old
                        new_product, new_price = replacement

                        if protected:
                            raise RuntimeError(
                                f"Protected purchase {item_id}"
                            )

                        if qty != 1:
                            raise RuntimeError(
                                f"Unexpected quantity for {item_id}"
                            )

                        if not isinstance(new_price, Decimal) or new_price < 0:
                            raise RuntimeError(
                                f"Invalid price for product {new_product}"
                            )

                        changes.append((
                            customer,
                            item_id,
                            old_product,
                            new_product,
                            new_price
                        ))

                print("DUPLICATE PURCHASES:", len(changes))

                if len(changes) != 385:
                    raise RuntimeError(
                        "Expected 385 duplicates. Database may have changed."
                    )

                print("\nFIRST 10 PROPOSED CHANGES:")

                for customer, item, old, new, price in changes[:10]:
                    print(
                        f"Customer {customer}: "
                        f"Item {item}: {old} -> {new} (${price})"
                    )

                answer = input(
                    "\nType APPLY to commit, or anything else to cancel: "
                ).strip()

                if answer != "APPLY":
                    conn.rollback()
                    print("CANCELLED: No changes made.")
                    return

                for customer, item, old, new, price in changes:
                    cur.execute("""
                        UPDATE order_items
                        SET product_id = %s,
                            unit_price = %s
                        WHERE order_item_id = %s
                          AND product_id = %s
                          AND order_id IN (
                              SELECT order_id FROM orders
                              WHERE customer_id = %s
                          );
                    """, (new, price, item, old, customer))

                    if cur.rowcount != 1:
                        raise RuntimeError(
                            f"Unexpected update count for item {item}"
                        )

                cur.execute("""
                    SELECT COUNT(*)
                    FROM (
                        SELECT o.customer_id, oi.product_id
                        FROM orders o
                        JOIN order_items oi
                            ON oi.order_id = o.order_id
                        GROUP BY o.customer_id, oi.product_id
                        HAVING COUNT(*) > 1
                    ) duplicates;
                """)

                remaining = cur.fetchone()[0]

                if remaining != 0:
                    raise RuntimeError(
                        f"Validation failed: {remaining} duplicates"
                    )

                cur.execute("""
                    SELECT COUNT(*)
                    FROM return_requests r
                    JOIN order_items oi
                        ON oi.order_item_id = r.order_item_id
                    WHERE r.product_id <> oi.product_id;
                """)

                if cur.fetchone()[0] != 0:
                    raise RuntimeError(
                        "Return/product consistency check failed."
                    )

            conn.commit()

            print(
                f"\nSUCCESS: {len(changes)} purchases corrected."
            )
            print("REMAINING DUPLICATES: 0")

        except BaseException:
            conn.rollback()
            raise

if __name__ == "__main__":
    main()
