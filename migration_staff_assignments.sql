-- Run once on your existing PostgreSQL database. Non-destructive.
CREATE TABLE IF NOT EXISTS staff_return_assignments (
    return_id INTEGER PRIMARY KEY REFERENCES return_requests(return_id) ON DELETE CASCADE,
    staff_id INTEGER NOT NULL REFERENCES users(user_id),
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_staff_return_assignments_staff
    ON staff_return_assignments(staff_id);
-- Existing unassigned real returns are assigned to the oldest existing staff member,
-- if one exists. They are never duplicated across staff accounts.
INSERT INTO staff_return_assignments (return_id, staff_id, is_demo)
SELECT r.return_id, s.user_id, FALSE
FROM return_requests r
CROSS JOIN LATERAL (SELECT user_id FROM users WHERE role = 'staff' ORDER BY user_id LIMIT 1) s
WHERE NOT EXISTS (SELECT 1 FROM staff_return_assignments a WHERE a.return_id = r.return_id)
ON CONFLICT (return_id) DO NOTHING;
