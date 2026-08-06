# Cấu trúc Thư mục Dự án (Project Directory Tree)

Dưới đây là sơ đồ cây thư mục chi tiết của dự án **api.ndinhnguyen**, kèm theo mô tả vai trò và chức năng của từng thư mục, tệp tin cốt lõi trong hệ thống.

```text
.
├── AGENTS.md               # Quy định và hướng dẫn dành cho AI coding agents
├── Makefile                # Tập hợp phím tắt lệnh khởi chạy
├── README.md               # Tài liệu hướng dẫn
├── pylock.toml             # File khóa phiên bản thư viện dùng cho Python Workers của Cloudflare
├── pyproject.toml          # Cấu hình project Python, dependencies (FastAPI, pytest, httpx, ...)
├── schema.sql              # Cấu trúc schema SQL của database D1
├── wrangler.jsonc          # Cấu hình Cloudflare Wrangler (bindings cho D1, R2, biến môi trường, compatibility)
├── uv.lock                 # File khóa môi trường ảo được tạo bởi `uv`
│
├── docs/                   # Thư mục chứa tài liệu hướng dẫn và tài nguyên kiểm thử
│   ├── FRONTEND_API_GUIDE.md# Hướng dẫn hiện thực Frontend, quy chuẩn API, mã lỗi & tích hợp VietQR
│   ├── README_TREE.md      # Tài liệu này (cây thư mục và cấu trúc hệ thống)
│   └── postman.json        # File collection hỗ trợ test API bằng Postman
│
├── logs/                   # Thư mục chứa log lỗi/hoạt động của app (bị bỏ qua bởi git)
│
├── scripts/                # Thư mục chứa các script hỗ trợ vận hành/tiện ích
│   ├── export_db_check.py  # Script xuất báo cáo kiểm tra cơ sở dữ liệu sau migration
│   └── get_logs.sh         # Script chạy ngầm để ghi log wrangler tail theo ngày
│
├── tests/                  # Bộ kiểm thử tích hợp (Integration Tests) chạy với pytest
│   ├── test_api.py         # Kiểm tra API chính cho Bookmark và Category
│   ├── test_auth.py        # Kiểm tra xác thực Google OAuth, Middleware RBAC và JWT session
│   ├── test_cashbacks.py   # Kiểm tra tích hợp nghiệp vụ cashback & đồng bộ Shopee
│   ├── test_core.py        # Kiểm tra config và middleware tĩnh
│   ├── test_payments.py    # Kiểm tra đợt thanh toán, đối soát tự động và chuyển đổi trạng thái
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
    │       ├── banks.py        # API lấy danh sách ngân hàng Việt Nam (công khai)
    │       ├── bookmarks.py    # CRUD bookmark cá nhân
    │       ├── cashbacks.py    # Truy xuất dữ liệu cashback và admin cashback
    │       ├── categories.py   # CRUD danh mục phân cấp tree
    │       ├── health.py       # Healthcheck
    │       ├── payments.py     # API đợt thanh toán, đối soát tự động & chuyển đổi trạng thái (User & Admin)
    │       ├── shopee.py       # Tạo link Shopee Affiliate, báo cáo conversions & sync
    │       ├── stats.py        # Ghi nhận telemetry, logs/snapshots hoạt động của app
    │       └── users.py        # Quản lý thông tin tài khoản & thông tin ngân hàng của User
    │
    ├── core/               # Các cấu hình và chức năng lõi hệ thống (Core Configs & Shared Utilities)
    │   ├── auth.py         # Chức năng tự sinh/xác thực JWT (HS256) không phụ thuộc thư viện ngoài
    │   ├── banks.py        # Helper đọc file banks.json và tra cứu thông tin/tên ngân hàng
    │   ├── constants.py    # Quản lý tập trung các URL bên thứ ba (Google Tokeninfo, Shopee APIs) dưới dạng template
    │   ├── context.py      # Định nghĩa ContextVar quản lý `worker_env` (chứa binding DB, R2, vars)
    │   ├── responses.py    # Định dạng dữ liệu phản hồi JSON chuẩn hóa của API
    │   └── settings.py     # Đọc cấu hình từ các biến môi trường
    │
    ├── data/               # Dữ liệu tĩnh dùng chung cho ứng dụng
    │   └── banks.json      # Danh sách các ngân hàng Việt Nam theo thứ tự chữ cái (code, name, short_name, bin, logo)
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
        ├── cashbacks/      # Nghiệp vụ cashback và quản lý các platform affiliate
        │   ├── interfaces.py  # Định nghĩa interface PlatformAdapter và hợp đồng các platform
        │   ├── repository.py  # Truy vấn cơ sở dữ liệu D1 cho các bản ghi cashback
        │   ├── schemas.py     # Schema Pydantic cho dữ liệu cashback
        │   ├── service.py     # Xử lý nghiệp vụ chính của cashback và đồng bộ từ các platforms
        │   └── shopee/        # Platform Shopee tích hợp cụ thể
        │       ├── adapter.py    # Shopee Platform Adapter chuyển đổi Conversion sang CashbackRecord
        │       ├── client.py     # HTTP Client kết nối API Shopee Affiliate
        │       ├── helper.py     # Các hàm tiện ích hỗ trợ chuyển đổi dữ liệu và ép kiểu an toàn cho Shopee
        │       ├── schemas.py    # Cấu trúc request link aff, thông tin sản phẩm và báo cáo chuyển đổi (conversions)
        │       └── service.py    # Trích xuất thông tin sản phẩm, sinh link affiliate và truy vấn báo cáo từ Shopee API
        ├── payments/       # Nghiệp vụ đối soát thanh toán & quản lý trạng thái đợt thanh toán
        │   ├── repository.py  # Truy vấn cơ sở dữ liệu D1 cho bảng payments & đối soát cashbacks
        │   ├── schemas.py     # Schema Pydantic cho đợt thanh toán, trạng thái & thông tin chuyển khoản User
        │   └── service.py     # Logic đối soát tự động hàng tuần (>= 50k VNĐ) & chuyển đổi trạng thái Payment
        ├── stats/          # Nghiệp vụ telemetry / ghi nhận trạng thái
        │   ├── constants.py   # Các tham số cấu hình tĩnh cho telemetry (giới hạn file, kích thước)
        │   ├── errors.py      # Định nghĩa các ngoại lệ (ValidationError, StorageError) cho stats
        │   ├── path_builder.py# Tạo đường dẫn lưu trữ động trên R2
        │   ├── runtime.py     # Nghiệp vụ xử lý và lưu log runtime
        │   ├── schemas.py     # Schema Pydantic đầu vào telemetry
        │   ├── service.py     # Điều phối lưu trữ snapshot và runtime logs lên R2
        │   ├── snapshot.py    # Nghiệp vụ xử lý định dạng CSV cho snapshot telemetry
        │   └── validators.py  # Trình xác thực nội dung file telemetry
        └── users/          # Nghiệp vụ người dùng, ngân hàng & xác thực Google
            ├── repository.py  # Truy vấn và cập nhật thông tin người dùng & ngân hàng trong DB D1
            ├── schemas.py     # Định nghĩa schema request & response xác thực & ngân hàng
            └── service.py     # Logic kiểm tra ID Token Google, RBAC và sinh session token JWT
```

---

---