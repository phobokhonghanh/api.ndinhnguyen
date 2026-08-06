-- Migration 0001: Payment Workflow & User ID Normalization (removing '-' from user IDs)

-- 1. Bổ sung các cột thông tin ngân hàng cho bảng users (nếu chưa có)
ALTER TABLE users ADD COLUMN bank_code TEXT;
ALTER TABLE users ADD COLUMN account_number TEXT;
ALTER TABLE users ADD COLUMN account_name TEXT;

-- 2. Tạo bảng payments
CREATE TABLE IF NOT EXISTS payments (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  amount REAL NOT NULL,
  cashback_count INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'Pending',
  bank_code TEXT,
  account_number TEXT,
  account_name TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(id)
);


CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

-- 3. Bổ sung cột payment_id cho bảng cashbacks (nếu chưa có)
ALTER TABLE cashbacks ADD COLUMN payment_id TEXT REFERENCES payments(id);
CREATE INDEX IF NOT EXISTS idx_cashbacks_payment_id ON cashbacks(payment_id);

-- 4. Bridge Migration: Chuẩn hóa User ID bằng cách hoãn kiểm tra khóa ngoại (defer foreign keys) trong transaction
PRAGMA defer_foreign_keys = ON;

UPDATE users SET id = REPLACE(id, '-', '') WHERE id LIKE '%-%';
UPDATE cashbacks SET user_id = REPLACE(user_id, '-', '') WHERE user_id LIKE '%-%';
UPDATE payments SET user_id = REPLACE(user_id, '-', '') WHERE user_id LIKE '%-%';
