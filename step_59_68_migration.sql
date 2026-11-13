-- Run once on local PostgreSQL BEFORE running the modified application.
-- Stores simulated outcomes only; no real refund processing.
CREATE TABLE IF NOT EXISTS simulated_returnless_refunds (
  refund_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  return_id BIGINT NOT NULL UNIQUE REFERENCES return_requests(return_id),
  order_item_id BIGINT NOT NULL UNIQUE REFERENCES order_items(order_item_id),
  refund_amount NUMERIC(10,2) NOT NULL CHECK (refund_amount >= 0 AND refund_amount <= 25),
  recovery_cost NUMERIC(10,2) NOT NULL CHECK (recovery_cost >= 0),
  recoverable_value NUMERIC(10,2) NOT NULL CHECK (recoverable_value >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
