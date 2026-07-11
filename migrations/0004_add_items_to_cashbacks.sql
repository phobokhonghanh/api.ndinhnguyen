-- Migration to add items column (JSON format) to cashbacks table
ALTER TABLE cashbacks ADD COLUMN items TEXT;
