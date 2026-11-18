# Return-to-Route coordinated demo-data correction

This is a **patch**, not a full application replacement. Existing frontend files and database records remain untouched.

## Before applying

1. Back up your current project and PostgreSQL database.
2. Stop Flask.
3. Run the database migration **before restarting the patched application**:

   `psql -d return_to_route -v ON_ERROR_STOP=1 -f migration_staff_assignments.sql`

4. Copy `app/demo_data.py`, `app/auth_routes.py`, `app/staff_queries.py`, `app/dashboard_routes.py`, and `app/returns.py` from this archive over the corresponding files in your project. Copy `backfill_demo_accounts.py` to the project root.
5. Start Flask and test fresh customer and staff registrations.
6. To add demo records to **existing** evaluator accounts without duplicating accounts already populated, run `python backfill_demo_accounts.py` and type `YES` to commit. Review your database backup first. Existing returns are assigned to the oldest staff account by the migration.

## Behavior

- Each newly registered customer gets 20 distinct random products as separate purchased orders, persisted in PostgreSQL.
- Each newly registered staff account gets 50 distinct pending demo returns from 50 fictional customer accounts.
- Staff dashboards show only assigned cases, and all four staff mutation endpoints reject cases not assigned to the logged-in staff member.
- New real customer returns are assigned to one staff account (the lowest user_id), not all staff accounts. This is a simple deterministic allocation policy, not load balancing.
- The existing 500-product catalog is **not** created by this patch; the code samples from whatever products are already in `products`. Registration requires at least 50 products for staff or 20 for customers. For a full 500-product catalog, seed the catalog separately.
- The original plan for a shared pool of 1,000 fictional customers is **not** implemented here. Instead, 50 separate fictional customer accounts are generated for each staff registration to guarantee isolation.

## Verification and limits

Python modules passed `compileall`. PostgreSQL runtime/integration tests could not be run without your Mac database and its actual schema. The SQL migration assumes the `users`, `products`, `orders`, `order_items`, and `return_requests` columns referenced in the existing application code. Test in a backed-up development database before applying to live evaluator data.

**Security:** Existing public registration accepts `role=staff` and does not verify `staff_code`; this pre-existing access-control issue is outside this patch and should be fixed before exposing the application publicly on EC2.
