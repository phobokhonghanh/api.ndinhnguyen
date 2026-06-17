# api.ndinhnguyen

> _Personal API for Nguyen Dinh Nguyen_

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=flat-square&logo=fastapi&logoColor=white) ![Cloudflare Workers](https://img.shields.io/badge/Cloudflare_Workers-Python-F38020?style=flat-square&logo=cloudflareworkers&logoColor=white) ![Cloudflare D1](https://img.shields.io/badge/Cloudflare_D1-SQLite-F38020?style=flat-square&logo=cloudflare&logoColor=white) ![Make](https://img.shields.io/badge/Make-Workflow-427819?style=flat-square&logo=gnu&logoColor=white)

---

## Routes

| Route                        | Type        | Description                                                                       |
| ---------------------------- | ----------- | --------------------------------------------------------------------------------- |
| `/health`                    | Public GET  | Health check endpoint returning API status metadata.                              |
| `/api/bookmarks`             | Auth GET    | Returns bookmarks, categories, category tree, selected category ids, and DB flag. |
| `/api/bookmarks`             | Auth POST   | Creates a bookmark.                                                               |
| `/api/bookmarks/{id}`        | Auth PUT    | Updates a bookmark.                                                               |
| `/api/bookmarks/{id}`        | Auth DELETE | Deletes a bookmark.                                                               |
| `/api/categories`            | Auth POST   | Creates a category.                                                               |
| `/api/categories/{id}`       | Auth PUT    | Updates a category.                                                               |
| `/api/categories/{id}`       | Auth DELETE | Deletes a category with business-rule checks.                                     |
| `/api/stats`                 | Public POST | Stores snapshot CSV markers and runtime JSONL uploads in R2.                     |

> All `/api/*` routes require `Authorization: Bearer <ADMIN_TOKEN>` except
> public `POST /api/stats`.

---

## Development

## Backend structure

The Worker is assembled in `src/main.py` and keeps `src/app.py` as a
compatibility import for existing runtime/tests. Feature code is organized by
boundary:

- `src/api/`: HTTP middleware and route adapters.
- `src/core/`: context, settings, and response helpers.
- `src/features/bookmarks/`: bookmark/category schemas, use cases, repository.
- `src/features/stats/`: stats command, service, validators, path builder, handlers.
- `src/infra/`: Cloudflare D1/R2 adapter helpers.

### Cài đặt python 3.12

```bash
# Option 1: Add deadsnakes PPA (Recommended)
sudo apt update
sudo apt install -y software-properties-common

sudo add-apt-repository ppa:deadsnakes/ppa -y
```
```bash
#Option 2: Add deadsnakes repository (manually)

#Add repository
echo "deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu jammy main" \
| sudo tee /etc/apt/sources.list.d/deadsnakes.list

#Import repository signing key
sudo apt-key adv \
  --keyserver keyserver.ubuntu.com \
  --recv-keys F23C5A6CF475977595C89F51BA6932366A755776
```

```bash
# Refresh package index
sudo apt update

# Install Python 3.12
sudo apt install -y python3.12 python3.12-venv python3.12-dev
Verify installation
python3.12 --version

Expected output:

Python 3.12.x
```

### Setup Cloudflare & R2 Storage

Trước khi phát triển cục bộ hoặc triển khai dự án, hãy đảm bảo bạn đã đăng nhập và khởi tạo R2 Bucket trên Cloudflare:

1. **Đăng nhập vào tài khoản Cloudflare:**
   ```bash
   npx wrangler login
   ```
   *Lưu ý:* Trình duyệt sẽ mở ra để xác thực. Hãy đăng nhập đúng tài khoản Cloudflare chứa D1 và R2 của bạn.

2. **Xác minh tài khoản đang hoạt động:**
   ```bash
   npx wrangler whoami
   ```
   *Quan trọng:* Hãy kiểm tra trường `Account ID` hiển thị trên màn hình xem có trùng khớp với ID tài khoản chứa database của bạn hay không để tránh lỗi phân quyền (Error 404).

3. **Khởi tạo R2 Bucket:**
   Dự án sử dụng R2 Bucket tên là `lakehouse-raw` (như cấu hình trong `wrangler.jsonc`). Tạo bucket bằng lệnh:
   ```bash
   npx wrangler r2 bucket create lakehouse-raw
   ```

4. **Kiểm tra danh sách R2 Buckets:**
   Để xác minh bucket đã được tạo thành công:
   ```bash
   npx wrangler r2 bucket list
   ```
### Run project local

```bash
python3.12 -m venv .venv
. .venv/bin/activate
make install
cp .dev.vars.example .dev.vars
make db-migrate-local
pip install uv
make run
```

`POST /api/stats` uses the `STATS_BUCKET` R2 binding and these path templates:

```bash
STATS_SNAPSHOT_PATH_TEMPLATE=lakehouse-raw/{product}/snapshot/loaddate={yyyymmdd}/{machine_id}.csv
STATS_RUNTIME_PATH_TEMPLATE=lakehouse-raw/{product}/runtime/loaddate={yyyymmdd}/{machine_id}_{batch_id}.jsonl
```

Run tests with:

```bash
make test
```

`make run` uses `pywrangler dev`, which is the recommended local runner for
Cloudflare Python Workers with FastAPI packages.

---

## Deployment

### 1. Triển khai thủ công từ máy cá nhân (Local Machine)

1. **Thiết lập Secret `ADMIN_TOKEN` trên Cloudflare:**
   ```bash
   make secret-put-admin-token
   ```
   *Lưu ý:* Hệ thống sẽ hỏi bạn nhập giá trị token bảo mật cho API.

2. **Chạy Migration để tạo các bảng dữ liệu trên Cloudflare D1:**
   ```bash
   make db-migrate-remote
   ```
   *Lưu ý:* Hãy chắc chắn bạn đã đăng nhập đúng tài khoản Cloudflare chứa database (`npx wrangler whoami`).

3. **Deploy mã nguồn lên Cloudflare:**
   ```bash
   make deploy
   ```
   *Lưu ý:* Lệnh này sẽ chạy `pywrangler deploy` để tự động đóng gói (vendor) toàn bộ thư viện bên thứ ba (như `fastapi`, `pydantic`,...) và tải lên Cloudflare.

---

### 2. Triển khai tự động bằng Git Integration (Cloudflare Dashboard)

Nếu bạn kết nối trực tiếp kho chứa GitHub với Cloudflare Workers để tự động build & deploy mỗi khi push code:

1. **Thiết lập Secret:**
   Vào **Cloudflare Dashboard** > **Workers & Pages** > Chọn Worker của bạn > **Settings** > **Variables** > Thêm một Secret mới tên là `ADMIN_TOKEN` với giá trị token của bạn.

2. **Cấu hình Câu lệnh Build/Deploy (Bắt buộc):**
   Mặc định Cloudflare sẽ chạy `npx wrangler deploy` (không đóng gói thư viện Python nên sẽ bị lỗi `ModuleNotFoundError: No module named 'fastapi'`). Bạn cần đổi cấu hình:
   * Vào **Settings** > **Builds & deployments** > **Build settings**.
   * Thay đổi **Build/Deploy command** thành:
     ```bash
     uv sync --extra dev && make deploy
     ```

3. **Chạy Migration:**
   Khi deploy lần đầu hoặc khi có cập nhật database schema mới, bạn vẫn cần chạy lệnh sau từ máy cục bộ để cập nhật database D1:
   ```bash
   make db-migrate-remote
   ```

> Frontend integration uses `https://ndinhnguyen.pages.dev` and local
> development uses `http://localhost:3000` via `ALLOWED_ORIGINS`.
