-- Bật tính năng khóa ngoại (Foreign Keys)
PRAGMA foreign_keys = ON;

-- 1. Bảng Categories (Danh mục)
CREATE TABLE IF NOT EXISTS categories (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  color TEXT NOT NULL DEFAULT 'blue',
  parent_id TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (parent_id) REFERENCES categories(id)
);
CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories(parent_id);

-- 2. Bảng Bookmarks (Dấu trang)
CREATE TABLE IF NOT EXISTS bookmarks (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  description TEXT,
  category_id TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES categories(id)
);
CREATE INDEX IF NOT EXISTS idx_bookmarks_category_id ON bookmarks(category_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_created_at ON bookmarks(created_at);

-- 3. Bảng Users (Người dùng)
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  picture TEXT,
  role TEXT NOT NULL DEFAULT 'user',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

INSERT OR IGNORE INTO users (id, email, name, role) VALUES ('system', 'system@ndinhnguyen.com', 'System Account', 'admin');

-- 4. Bảng Cashbacks (Hoàn tiền mua sắm đa nền tảng)
CREATE TABLE IF NOT EXISTS cashbacks (
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
CREATE UNIQUE INDEX IF NOT EXISTS idx_cashbacks_platform_checkout ON cashbacks(platform, checkout_id);
CREATE INDEX IF NOT EXISTS idx_cashbacks_user_id ON cashbacks(user_id);
