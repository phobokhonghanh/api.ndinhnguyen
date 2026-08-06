-- Migration 0002: Add paid_at column to payments table
ALTER TABLE payments ADD COLUMN paid_at TEXT;
