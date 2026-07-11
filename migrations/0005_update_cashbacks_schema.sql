-- Migration to update the cashbacks table to store conversion JSON directly
-- 1. Rename existing table
ALTER TABLE cashbacks RENAME TO cashbacks_old;

-- 2. Create the new table
CREATE TABLE cashbacks (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  cashback_amount REAL NOT NULL,
  status TEXT NOT NULL,
  checkout_id TEXT NOT NULL,
  order_id TEXT NOT NULL,
  coversion TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

-- 3. Copy/convert existing data
INSERT INTO cashbacks (
  id, user_id, platform, cashback_amount, status, checkout_id, order_id, coversion, created_at, updated_at
)
SELECT 
  id, 
  user_id, 
  platform, 
  cashback_amount, 
  status, 
  checkout_id, 
  order_id, 
  json_object(
    'click_id', NULL,
    'click_time', NULL,
    'checkout_id', checkout_id,
    'purchase_time', purchase_time,
    'checkout_complete_time', NULL,
    'checkout_status', checkout_status,
    'affiliate_id', CAST(affiliate_id AS INTEGER),
    'affiliate_net_commission', CAST(ROUND(affiliate_net_commission * 100000) AS INTEGER),
    'utm_content', 'some-' || user_id,
    'order', json_array(
      json_object(
        'id', NULL,
        'order_sn', order_id,
        'items', CASE WHEN json_valid(items) THEN json(items) ELSE json_array() END
      )
    )
  ),
  created_at,
  updated_at
FROM cashbacks_old;

-- 4. Recreate indices
CREATE UNIQUE INDEX IF NOT EXISTS idx_cashbacks_platform_checkout_order ON cashbacks(platform, checkout_id, order_id);
CREATE INDEX IF NOT EXISTS idx_cashbacks_user_id ON cashbacks(user_id);

-- 5. Drop old table
DROP TABLE cashbacks_old;
