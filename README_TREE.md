# Cấu trúc Thư mục Dự án (Project Directory Tree)

Dưới đây là sơ đồ cây thư mục chi tiết của dự án **api.ndinhnguyen**, kèm theo mô tả vai trò và chức năng của từng thư mục, tệp tin cốt lõi trong hệ thống.

```text
.
├── AGENTS.md               # Quy định và hướng dẫn dành cho AI coding agents
├── Makefile                # Tập hợp phím tắt lệnh khởi chạy
├── README.md               # Tài liệu hướng dẫn
├── README_TREE.md          # Tài liệu này (cây thư mục và cấu trúc hệ thống)
├── pylock.toml             # File khóa phiên bản thư viện dùng cho Python Workers của Cloudflare
├── pyproject.toml          # Cấu hình project Python, dependencies (FastAPI, pytest, httpx, ...)
├── wrangler.jsonc          # Cấu hình Cloudflare Wrangler (bindings cho D1, R2, biến môi trường, compatibility)
├── uv.lock                 # File khóa môi trường ảo được tạo bởi `uv`
│
├── docs/                   # Tài liệu phác thảo chức năng
│   ├── bookmarks.txt
│   └── shope.txt
│
├── migrations/             # Các file SQL
│   ├── 0001_create_bookmarks.sql  # Khởi tạo bảng danh mục và bảng bookmarks
│   └── 0002_create_users.sql      # Khởi tạo bảng người dùng phục vụ Google Login & RBAC
│
├── postman/                # File collection hỗ trợ test API bằng Postman
│   └── bookmarks_api_collection.json
│
├── tests/                  # Bộ kiểm thử tích hợp (Integration Tests) chạy với pytest
│   ├── test_api.py         # Kiểm tra API chính cho Bookmark và Category
│   ├── test_auth.py        # Kiểm tra xác thực Google OAuth, Middleware RBAC và JWT session
│   ├── test_core.py        # Kiểm tra config và middleware tĩnh
│   ├── test_service.py     # Kiểm tra logic nghiệp vụ lưu bookmark, phân trang danh mục
│   ├── test_shopee.py      # Kiểm tra chuyển đổi link affiliate Shopee
│   └── test_stats_manager.py  # Kiểm tra tính toán và tải dữ liệu stats lên R2
│
└── src/                    # Mã nguồn chính của ứng dụng
    ├── main.py             # Khởi tạo ứng dụng FastAPI
    ├── app.py              # Đăng ký các Middleware và cấu hình Routers cho FastAPI
    ├── entry.py            # Entrypoint chạy trên Cloudflare Worker thực tế, thiết lập ContextVar worker_env
    │
    ├── api/                # Layer Controllers (Router)
    │   ├── helpers.py      # Hàm tiện ích chung cho routes
    │   ├── middleware.py   # Middleware bảo mật: Kiểm tra CORS, JWT Token session, phân quyền Admin
    │   └── routes/         # Khai báo các endpoints HTTP (FastAPI Routers)
    │       ├── auth.py         # Login & logout bằng Google OAuth 2.0
    │       ├── bookmarks.py    # CRUD bookmark cá nhân
    │       ├── categories.py   # CRUD danh mục phân cấp tree
    │       ├── health.py       # Healthcheck
    │       ├── shopee.py       # Tạo link Shopee Affiliate từ link sản phẩm gốc
    │       └── stats.py        # Ghi nhận telemetry, logs/snapshots hoạt động của app
    │
    ├── core/               # Các cấu hình và chức năng lõi hệ thống (Core Configs & Shared Utilities)
    │   ├── auth.py         # Chức năng tự sinh/xác thực JWT (HS256) không phụ thuộc thư viện ngoài
    │   ├── constants.py    # Quản lý tập trung các URL bên thứ ba (Google Tokeninfo, Shopee APIs) dưới dạng template
    │   ├── context.py      # Định nghĩa ContextVar quản lý `worker_env` (chứa binding DB, R2, vars)
    │   ├── responses.py    # Định dạng dữ liệu phản hồi JSON chuẩn hóa của API
    │   └── settings.py     # Đọc cấu hình từ các biến môi trường
    │
    ├── infra/              # Tầng tương tác hạ tầng lưu trữ (Infrastructure Storage Wrappers)
    │   ├── d1.py           # Tiện ích viết sẵn hỗ trợ query nhanh cơ sở dữ liệu Cloudflare D1
    │   ├── http.py         # Client HTTP chung: tự động đổi giữa js.fetch (Workers) và httpx (Local Dev)
    │   └── object_store.py # Wrapper quản lý lưu trữ tệp lên Cloudflare R2
    │
    └── features/           # Tầng chứa logic nghiệp vụ và schema Pydantic theo từng miền chức năng (Domain Features)
        ├── bookmarks/      # Nghiệp vụ bookmark và danh mục (Category)
        │   ├── repository.py  # Truy vấn cơ sở dữ liệu D1 cho bookmark & category
        │   ├── schemas.py     # Schema Pydantic cho dữ liệu đầu vào/đầu ra của bookmark & category
        │   └── service.py     # Xử lý nghiệp vụ phân trang, xây dựng cây danh mục (build tree)
        ├── shopee/         # Tích hợp Shopee Affiliate
        │   ├── schemas.py     # Cấu trúc request link aff, thông tin sản phẩm và báo cáo chuyển đổi (conversions)
        │   └── service.py     # Trích xuất thông tin sản phẩm, sinh link affiliate và truy vấn báo cáo từ Shopee API
        ├── stats/          # Nghiệp vụ telemetry / ghi nhận trạng thái
        │   ├── constants.py   # Các tham số cấu hình tĩnh cho telemetry (giới hạn file, kích thước)
        │   ├── errors.py      # Định nghĩa các ngoại lệ (ValidationError, StorageError) cho stats
        │   ├── path_builder.py# Tạo đường dẫn lưu trữ động trên R2
        │   ├── runtime.py     # Nghiệp vụ xử lý và lưu log runtime
        │   ├── schemas.py     # Schema Pydantic đầu vào telemetry
        │   ├── service.py     # Điều phối lưu trữ snapshot và runtime logs lên R2
        │   ├── snapshot.py    # Nghiệp vụ xử lý định dạng CSV cho snapshot telemetry
        │   └── validators.py  # Trình xác thực nội dung file telemetry
        └── users/          # Nghiệp vụ người dùng & xác thực Google
            ├── repository.py  # Truy vấn và cập nhật thông tin người dùng trong DB D1
            ├── schemas.py     # Định nghĩa schema request & response xác thực người dùng
            └── service.py     # Logic kiểm tra ID Token Google, RBAC và sinh session token JWT
```

---