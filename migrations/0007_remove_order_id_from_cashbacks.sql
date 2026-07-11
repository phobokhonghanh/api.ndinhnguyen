-- Migration to remove order_id column and update index
-- 1. Rename existing table
ALTER TABLE cashbacks RENAME TO cashbacks_old;

-- 2. Create the new table without order_id
CREATE TABLE cashbacks (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  cashback_amount REAL NOT NULL,
  status TEXT NOT NULL,
  checkout_id TEXT NOT NULL,
  conversion TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

-- 3. Copy existing data
INSERT INTO cashbacks (
  id, user_id, platform, cashback_amount, status, checkout_id, conversion, created_at, updated_at
)
SELECT 
  id, 
  user_id, 
  platform, 
  cashback_amount, 
  status, 
  checkout_id, 
  conversion, 
  created_at, 
  updated_at
FROM cashbacks_old;

-- 4. Recreate indices
CREATE UNIQUE INDEX IF NOT EXISTS idx_cashbacks_platform_checkout ON cashbacks(platform, checkout_id);
CREATE INDEX IF NOT EXISTS idx_cashbacks_user_id ON cashbacks(user_id);

-- 5. Drop old table
DROP TABLE cashbacks_old;
