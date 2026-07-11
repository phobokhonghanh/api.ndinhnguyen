-- Migration to create the cashbacks table for multi-platform cashback tracking
CREATE TABLE IF NOT EXISTS cashbacks (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  purchase_time INTEGER NOT NULL,
  checkout_id TEXT NOT NULL,
  checkout_status TEXT NOT NULL,
  affiliate_id TEXT NOT NULL,
  affiliate_net_commission REAL NOT NULL,
  platform_commission_rate INTEGER NOT NULL,
  order_id TEXT NOT NULL,
  item_name TEXT NOT NULL,
  img_code TEXT,
  actual_amount REAL NOT NULL,
  is_fraud INTEGER NOT NULL DEFAULT 0,
  cashback_amount REAL NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_cashbacks_platform_checkout_order ON cashbacks(platform, checkout_id, order_id);
CREATE INDEX IF NOT EXISTS idx_cashbacks_user_id ON cashbacks(user_id);
