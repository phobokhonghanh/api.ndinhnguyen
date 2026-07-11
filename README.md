# api.ndinhnguyen

> _API cá nhân của Nguyễn Đình Nguyên_

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=flat-square&logo=fastapi&logoColor=white) ![Cloudflare Workers](https://img.shields.io/badge/Cloudflare_Workers-Python-F38020?style=flat-square&logo=cloudflareworkers&logoColor=white) ![Cloudflare D1](https://img.shields.io/badge/Cloudflare_D1-SQLite-F38020?style=flat-square&logo=cloudflare&logoColor=white) ![Make](https://img.shields.io/badge/Make-Workflow-427819?style=flat-square&logo=gnu&logoColor=white)

---

## Các Endpoint (Routes)

| Route                              | Kiểu        | Mô tả                                                                             |
| ---------------------------------- | ----------- | --------------------------------------------------------------------------------- |
| `/health`                          | Public GET  | Kiểm tra trạng thái hoạt động của API.                                             |
| `/api/bookmarks`                   | Auth GET    | Lấy toàn bộ danh sách bookmark, category, cấu trúc cây và thông tin cấu hình DB.  |
| `/api/bookmarks`                   | Auth POST   | Tạo mới một bookmark.                                                            |
| `/api/bookmarks/{id}`              | Auth PUT    | Cập nhật thông tin bookmark.                                                      |
| `/api/bookmarks/{id}`              | Auth DELETE | Xóa một bookmark.                                                                 |
| `/api/categories`                  | Auth POST   | Tạo mới một category (danh mục).                                                  |
| `/api/categories/{id}`             | Auth PUT    | Cập nhật thông tin danh mục.                                                      |
| `/api/categories/{id}`             | Auth DELETE | Xóa danh mục (có kèm các ràng buộc logic nghiệp vụ).                              |
| `/api/stats`                       | Public POST | Lưu thông tin snapshot CSV và log runtime JSONL lên Cloudflare R2.               |
| `/api/auth/google/login`           | Public POST | Xác thực người dùng bằng Google OAuth ID token.                                   |
| `/api/shopee/affiliate`            | Public POST | Tạo link Shopee Affiliate từ link sản phẩm gốc.                                   |
| `/api/shopee/conversions`          | Auth GET    | Lấy báo cáo chuyển đổi Shopee của người dùng hiện tại.                            |
| `/api/admin/shopee/conversions`    | Auth GET    | Lấy toàn bộ báo cáo chuyển đổi Shopee (Chỉ Admin).                                |
| `/api/admin/shopee/conversions/sync` | Auth POST   | Đồng bộ thủ công dữ liệu conversions Shopee sang bảng Cashback (Chỉ Admin).        |
| `/api/cashbacks`                   | Auth GET    | Lấy lịch sử hoàn tiền của người dùng hiện tại.                                    |
| `/api/admin/cashbacks`             | Auth GET    | Lấy danh sách toàn bộ cashback trên hệ thống (Chỉ Admin).                         |

> Tất cả các route dạng `/api/*` yêu cầu header xác thực `Authorization: Bearer <ADMIN_TOKEN>` hoặc token JWT hợp lệ, ngoại trừ các route public sau: `/api/stats`, `/api/auth/google/login`, và `/api/shopee/affiliate`.

---

## Phát triển ứng dụng (Development)

### 1. Cài đặt môi trường (OS Linux/Ubuntu)

#### Bước A: Cài đặt Python 3.12 và Pip
```bash
# Thêm kho phần mềm deadsnakes (Khuyên dùng cho Ubuntu)
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y

# Cập nhật lại chỉ mục gói và cài đặt Python 3.12
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Xác minh phiên bản đã cài đặt
python3.12 --version  # Output kỳ vọng: Python 3.12.x
```

#### Bước B: Cài đặt Node.js & Wrangler (Để chạy Cloudflare Worker)
Wrangler yêu cầu Node.js để thực thi. Nếu chưa cài đặt Node.js:
```bash
# Cài đặt Node.js và npm
sudo apt install -y nodejs npm
```

#### Bước C: Cài đặt công cụ quản lý UV (Mạnh mẽ hơn pip)
```bash
pip install uv
```

---

### 2. Thiết lập Cloudflare & R2 Storage

Đăng nhập Cloudflare và khởi tạo R2:

1. **Đăng nhập Cloudflare:**
   ```bash
   npx wrangler login
   ```

2. **Xác minh tài khoản đang hoạt động:**
   ```bash
   npx wrangler whoami
   ```

3. **Khởi tạo R2 Bucket:**
   ```bash
   npx wrangler r2 bucket create lakehouse-raw
   ```

4. **Kiểm tra danh sách R2 Buckets:**
   ```bash
   npx wrangler r2 bucket list
   ```

---

### 3. Cấu hình & Chạy dự án cục bộ (Local)

1. **Tạo môi trường ảo Python:**
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

2. **Cài đặt thư viện phụ thuộc:**
   ```bash
   make install
   ```

3. **Tạo file cấu hình môi trường cục bộ:**
   ```bash
   cp .dev.vars.example .dev.vars
   ```
   *Lưu ý:* Hãy mở file `.dev.vars` lên để cấu hình các biến môi trường như `ADMIN_TOKEN`, `JWT_SECRET`, và các thông tin Google OAuth.

4. **Khởi tạo Database SQLite:**
   ```bash
   npx wrangler d1 execute ndinhnguyen --local --file=schema.sql
   ```

5. **Chạy ứng dụng:**
   ```bash
   make run
   ```
   Sử dụng `pywrangler dev` (chạy local dưới nền tảng Python của Cloudflare Worker kết hợp FastAPI).

---

### 4. Lấy Google ID Token để test Login

Để kiểm thử chức năng Đăng nhập Google (`/api/auth/google/login`), backend cần nhận một `id_token` hợp lệ từ Google gửi lên. Dưới đây là các bước chi tiết để cấu hình và lấy token này:

#### Bước 1: Tạo dự án trên Google Cloud Console
Truy cập [Google Cloud Console](https://console.cloud.google.com/).

#### Bước 2: Cập nhật biến môi trường backend
Mở file `.dev.vars` (ở thư mục gốc dự án) và cập nhật Client ID của bạn vào:
```ini
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_COPIED_ABOVE.apps.googleusercontent.com
ADMIN_EMAIL=your-email-address@gmail.com
```

#### Bước 3: Lấy ID Token

1. Truy cập **Google OAuth 2.0 Playground**:

   https://developers.google.com/oauthplayground/

2. Ở cột bên trái, trong mục **Select & authorize APIs**, tìm kiếm và chọn:

   ```
   Google OAuth2 API v2
   ```

3. Tick chọn đầy đủ **3 scope** sau:

   ```
   https://www.googleapis.com/auth/userinfo.email
   https://www.googleapis.com/auth/userinfo.profile
   openid
   ```

   > **Lưu ý:** Nếu thiếu scope `openid` thì Google sẽ không trả về `id_token`.

4. Nhấn **Authorize APIs**.

5. Đăng nhập bằng tài khoản Google mà bạn muốn lấy **ID Token**.

6. Nếu Google hiển thị màn hình xác nhận quyền truy cập, chọn **Allow** (Cho phép).

7. Sau khi xác thực thành công, bạn sẽ được chuyển về OAuth Playground với **Authorization Code** đã được điền tự động.

8. Nhấn nút **Exchange authorization code for tokens**.

9. Sau vài giây, ở khung **Response** bên phải sẽ xuất hiện nội dung JSON tương tự:

   ```json
   {
     "access_token": "...",
     "id_token": "eyJhbGciOiJSUzI1NiIs...",
     "refresh_token": "...",
     "expires_in": 3599,
     "token_type": "Bearer"
   }
   ```

10. Sao chép giá trị của trường **`id_token`** và sử dụng cho các bước tiếp theo.

#### Bước 4: Gọi API Đăng nhập từ Postman hoặc Swagger (http://localhost:8787/docs)
Gửi request dạng `POST` tới local backend:
* **Method:** `POST`
* **URL:** `http://localhost:8787/api/auth/google/login`
* **Body (JSON):**
  ```json
  {
    "id_token": "<Chuỗi ID Token bạn vừa sao chép>"
  }
  ```
Backend sẽ tự động xác thực token này với Google, khởi tạo tài khoản trong database và trả về JWT session hợp lệ để bạn dùng cho các API sau.

---

### 5. Chạy Kiểm thử (Tests)

Chạy bộ test case tự động:
```bash
make test
```

---

## Triển khai (Deployment)

### 1. Triển khai thủ công từ máy cá nhân (Local Machine)

1. **Thiết lập Secret `ADMIN_TOKEN` trên Cloudflare:**
   ```bash
   make secret-put-admin-token
   ```
   *(Nhập giá trị token bảo mật cho API khi được yêu cầu)*

2. **Khởi tạo cấu trúc Database trên Cloudflare D1 (Chạy 1 lần duy nhất):**
   Bạn có thể dùng file `schema.sql` để tạo toàn bộ các bảng trực tiếp trên database remote của Cloudflare:
   ```bash
   npx wrangler d1 execute ndinhnguyen --remote --file=schema.sql
   ```

3. **Deploy mã nguồn lên Cloudflare:**
   ```bash
   make deploy
   ```
   Lệnh này tự động đóng gói toàn bộ thư viện bên thứ ba và tải ứng dụng lên Cloudflare Workers.

---

### 2. Triển khai tự động bằng Git Integration (Cloudflare Dashboard)

Nếu bạn kết nối trực tiếp kho chứa GitHub với Cloudflare Workers để tự động build & deploy mỗi khi push code:

1. **Thiết lập Secret:**
   Vào **Cloudflare Dashboard** > **Workers & Pages** > Chọn Worker của bạn > **Settings** > **Variables** > Thêm một Secret mới tên là `ADMIN_TOKEN`.

2. **Cấu hình Câu lệnh Build/Deploy (Bắt buộc):**
   Thay đổi **Build/Deploy command** trong **Build settings** thành:
   ```bash
   uv sync --extra dev && make deploy
   ```

3. **Đồng bộ cơ sở dữ liệu khi có thay đổi:**
   Khi deploy lần đầu hoặc khi có cập nhật cấu trúc bảng mới, chạy lệnh sau từ máy cục bộ để cập nhật database D1 remote:
   ```bash
   npx wrangler d1 execute ndinhnguyen --remote --file=schema.sql
   ```
