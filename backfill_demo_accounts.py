"""Optional one-time backfill for existing evaluator accounts. Run after SQL migration."""
from app.db import get_db_connection
from app.demo_data import seed_customer, seed_staff


def main():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM products")
            count = cur.fetchone()[0]
            if count < 50:
                raise SystemExit(f"Need at least 50 products, found {count}. No changes made.")
            cur.execute("""SELECT user_id, role FROM users
                           WHERE email NOT LIKE 'demo-%@example.invalid'
                           ORDER BY user_id""")
            accounts = cur.fetchall()
            customer_total = staff_total = 0
            for user_id, role in accounts:
                if role == 'customer':
                    customer_total += seed_customer(cur, user_id)
                elif role == 'staff':
                    staff_total += seed_staff(cur, user_id)
        print(f"Prepared {customer_total} customer purchase records and {staff_total} staff demo cases.")
        answer = input('Commit these additions? Type YES to proceed: ')
        if answer != 'YES':
            conn.rollback()
            print('Rolled back; no additions saved.')
            return
        conn.commit()
        print('Committed.')


if __name__ == '__main__':
    main()
