# Hướng dẫn Hiện thực Frontend & Quy ước API (API Specification & Integration Guide)

Tài liệu này cung cấp chi tiết toàn bộ hợp đồng API (API Contracts), cấu trúc dữ liệu, luồng xác thực, mã lỗi và hướng dẫn hiện thực tính năng cho **Agent Frontend** hoặc nhà phát triển Frontend mà không cần phải tự suy đoán hay đọc mã nguồn backend.

---

## 1. Quy chuẩn chung (General Architecture & Conventions)

- **Base URL**: `/api`
- **Authentication**: JWT Session Token truyền qua HTTP Header `Authorization: Bearer <TOKEN>`.
- **Định dạng User ID**: Tất cả `user_id` hoặc `sub` đều là chuỗi 32 ký tự Hex không chứa dấu gạch ngang (Ví dụ: `00686da162014d34804c00d0c8572ce7`).
- **Phân quyền (RBAC)**: Có 2 loại vai trò (role) chính: `"user"` và `"admin"`.

### 1.1 Envelope Response chuẩn từ Backend

Tất cả các API response đều bọc trong cấu trúc Envelope:

#### Response thành công (Success Envelope)
```json
{
  "ok": true,
  "code": "ok",
  "data": { ... },
  "pagination": {
    "total": 100,
    "page": 1,
    "pageSize": 20,
    "totalPages": 5
  }
}
```
*(Lưu ý: Trường `pagination` chỉ xuất hiện trên các API danh sách có phân trang)*.

#### Response thất bại (Error Envelope)
```json
{
  "ok": false,
  "code": "ma_loi_chi_tiet"
}
```

---

## 2. Xác thực người dùng (Authentication Module)

### 2.1 Google OAuth Login
- **Endpoint**: `POST /api/auth/google/login`
- **Auth required**: Không (Public)
- **Request Body**:
  ```json
  {
    "id_token": "string_google_oauth_id_token"
  }
  ```
- **Response Data (`LoginResponseData`)**:
  ```json
  {
    "ok": true,
    "code": "ok",
    "data": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "user": {
        "id": "00686da162014d34804c00d0c8572ce7",
        "email": "user@example.com",
        "name": "Nguyen Van A",
        "picture": "https://lh3.googleusercontent.com/...",
        "role": "user",
        "bankCode": "MB",
        "bankName": "Ngan hang Quan doi",
        "accountNumber": "0381000123456",
        "accountName": "NGUYEN VAN A",
        "createdAt": "2026-07-12 08:37:06",
        "updatedAt": "2026-08-03 08:40:49"
      }
    }
  }
  ```
- **Xử lý ở Frontend**:
  - Lưu `token` vào `localStorage` hoặc Cookie an toàn.
  - Đính kèm token vào mọi request sau này: `Authorization: Bearer <token>`.
  - Kiểm tra `user.role` (`"admin"` hoặc `"user"`) để điều hướng giao diện phù hợp.

### 2.2 Google Logout
- **Endpoint**: `POST /api/auth/google/logout`
- **Auth required**: Không
- **Response**: `{"ok": true, "code": "ok"}`
- **Xử lý ở Frontend**: Xóa `token` và thông tin `user` khỏi bộ nhớ client.

---

## 3. Danh sách Ngân hàng & Thông tin thanh toán (Banks & User Payment Profile)

### 3.1 Lấy danh sách Ngân hàng Việt Nam
- **Endpoint**: `GET /api/banks`
- **Auth required**: Không (Public)
- **Mô tả**: Trả về danh sách tất cả các ngân hàng hỗ trợ chuyển khoản tại Việt Nam (sắp xếp theo thứ tự bảng chữ cái) để hiển thị ô chọn (Select / Dropdown) trên Frontend.
- **Response Data (`list[BankSchema]`)**:
  ```json
  {
    "ok": true,
    "code": "ok",
    "data": [
      {
        "code": "ABB",
        "name": "Ngân hàng TMCP An Bình",
        "shortName": "ABBANK",
        "bin": "970425",
        "logo": "https://api.vietqr.io/img/ABB.png"
      },
      {
        "code": "MB",
        "name": "Ngân hàng TMCP Quân Đội",
        "shortName": "MBBank",
        "bin": "970422",
        "logo": "https://api.vietqr.io/img/MB.png"
      }
    ]
  }
  ```

### 3.2 Lấy thông tin ngân hàng của User
- **Endpoint**: `GET /api/user/payment-info`
- **Auth required**: Có (User / Admin)
- **Response Data (`UserPaymentInfo`)**:
  ```json
  {
    "ok": true,
    "code": "ok",
    "data": {
      "bankCode": "MB",
      "bankName": "Ngân hàng TMCP Quân Đội",
      "accountNumber": "0381000123456",
      "accountName": "NGUYEN VAN A"
    }
  }
  ```

### 3.3 Cập nhật thông tin ngân hàng của User
- **Endpoint**: `PUT /api/user/payment-info`
- **Auth required**: Có (User / Admin)
- **Request Body (`UpdatePaymentInfoRequest`)**:
  *(Lưu ý: Không gửi `bank_name`, backend tự động tra cứu tên ngân hàng chuẩn từ `bank_code`)*.
  ```json
  {
    "bank_code": "MB",
    "account_number": "0381000123456",
    "account_name": "NGUYEN VAN A"
  }
  ```
- **Response Data (`UserPaymentInfo`)**: Trả về thông tin vừa cập nhật dưới dạng camelCase (`bankCode`, `bankName`, `accountNumber`, `accountName`).

---


## 4. Quản lý Cashback (Cashbacks Module)

### 4.1 Danh sách Cashback của User hiện tại
- **Endpoint**: `GET /api/cashbacks`
- **Auth required**: Có (User / Admin)
- **Query Parameters**:
  - `page` (int, default `1`): Trang hiện tại
  - `pageSize` (int, default `20`, max `100`): Số lượng bản ghi trên một trang
- **Response Data (`list[CashbackRecord]`)**:
  ```json
  {
    "ok": true,
    "code": "ok",
    "data": [
      {
        "id": "7cb3b18d-ec1d-449c-aa6b-a7815a161590",
        "userId": "00686da162014d34804c00d0c8572ce7",
        "platform": "shopee",
        "cashback": 5866.95,
        "status": "Approved",
        "checkoutId": "237804481235505",
        "paymentId": null,
        "conversion": { ... },
        "createdAt": "2026-07-16 10:40:40",
        "updatedAt": "2026-08-03 08:40:49"
      }
    ],
    "pagination": {
      "total": 1,
      "page": 1,
      "pageSize": 20,
      "totalPages": 1
    }
  }
  ```

### 4.2 Danh sách Cashback dành cho Admin
- **Endpoint**: `GET /api/admin/cashbacks`
- **Auth required**: Có (Admin only)
- **Query Parameters**:
  - `page` (int, default `1`)
  - `pageSize` (int, default `20`)
  - `userId` (string, optional): Lọc theo ID người dùng cụ thể

---

## 5. Đợt Thanh toán & Đối soát (Payments & Reconciliation)

### 5.1 Quy trình đối soát & tạo đợt thanh toán (Workflow Overview)

1. **Điều kiện tạo Payment**:
   - Cashback có trạng thái `Approved`.
   - Cashback chưa gắn vào bất kỳ Payment nào (`paymentId == null`).
   - Tổng giá trị cashback thỏa điều kiện của 1 user **từ 50.000 VNĐ trở lên**.
2. **Trạng thái của Payment**:
   - `Pending` *(Mới tạo, chờ Admin chuyển khoản thủ công)*.
   - `Completed` *(Admin đã chuyển khoản thành công)*.
   - `Cancelled` *(Admin hủy thanh toán -> Toàn bộ cashback thuộc Payment này được gỡ `payment_id = null` để chờ kỳ đối soát sau)*.
3. **Cơ chế đóng băng thông tin ngân hàng (Bank Info Snapshot)**:
   - Khi ở trạng thái `Pending`: Đối tượng `userPaymentInfo` sẽ lấy thông tin trực tiếp (live) mới nhất từ hồ sơ tài khoản người dùng (`users`).
   - Khi Admin đổi trạng thái sang `Completed`: Hệ thống tự động **chụp ảnh đóng băng (Snapshot)** thông tin ngân hàng tại thời điểm chuyển khoản và lưu cố định vào bản ghi `payments`.
   - Bảo toàn lịch sử: Cho dù người dùng có thay đổi thông tin ngân hàng sau đó, bản ghi `Completed` trước đó vẫn hiển thị thông tin ngân hàng đã snapshot.


---

### 5.2 API Người dùng (User Endpoints)

#### Danh sách đợt thanh toán của User
- **Endpoint**: `GET /api/payments`
- **Auth required**: Có (User / Admin)
- **Query Parameters**:
  - `page` (int, default `1`)
  - `pageSize` (int, default `20`)
  - `status` (string, optional): Lọc theo `Pending`, `Completed`, hoặc `Cancelled`
- **Response Data (`list[PaymentRecord]`)**:
  ```json
  {
    "ok": true,
    "code": "ok",
    "data": [
      {
        "id": "pay_5a782b1928cf",
        "userId": "00686da162014d34804c00d0c8572ce7",
        "amount": 75000.0,
        "cashbackCount": 5,
        "status": "Pending",
        "userPaymentInfo": null,
        "createdAt": "2026-08-01 10:00:00",
        "paidAt": null,
        "updatedAt": "2026-08-01 10:00:00"
      }
    ],
    "pagination": { "total": 1, "page": 1, "pageSize": 20, "totalPages": 1 }
  }
  ```

#### Chi tiết 1 đợt thanh toán của User
- **Endpoint**: `GET /api/payments/{id}`
- **Auth required**: Có (User / Admin)
- **Response Data (`PaymentDetailRecord`)**: Tra về thông tin Payment + danh sách `cashbacks` đính kèm.

---

### 5.3 API Quản trị viên (Admin Endpoints)

#### 1. Kích hoạt đợt đối soát tự động (Reconcile)
- **Endpoint**: `POST /api/admin/payments/reconcile`
- **Auth required**: Có (Admin only)
- **Response Data (`ReconciliationSummary`)**:
  ```json
  {
    "ok": true,
    "code": "ok",
    "data": {
      "createdPaymentsCount": 2,
      "totalAmount": 150000.0,
      "totalCashbacksProcessed": 10
    }
  }
  ```

#### 2. Lấy danh sách tất cả Payment (Dành cho Admin)
- **Endpoint**: `GET /api/admin/payments`
- **Auth required**: Có (Admin only)
- **Query Parameters**: `page`, `pageSize`, `userId` (optional), `status` (optional)
- **Response Data (`list[PaymentRecord]`)**:
  Dữ liệu bao gồm đối tượng `userPaymentInfo` chứa thông tin ngân hàng để Frontend tạo VietQR:
  ```json
  {
    "ok": true,
    "code": "ok",
    "data": [
      {
        "id": "pay_5a782b1928cf",
        "userId": "00686da162014d34804c00d0c8572ce7",
        "amount": 75000.0,
        "cashbackCount": 5,
        "status": "Pending",
        "userPaymentInfo": {
          "userId": "00686da162014d34804c00d0c8572ce7",
          "email": "ndnhan254@gmail.com",
          "name": "Nguyen Nhan",
          "bankCode": "MB",
          "bankName": "Ngân hàng Quan doi",
          "accountNumber": "0381000123456",
          "accountName": "NGUYEN VAN A"
        },
        "createdAt": "2026-08-01 10:00:00",
        "updatedAt": "2026-08-01 10:00:00"
      }
    ]
  }
  ```

#### 3. Lấy chi tiết Payment (Dành cho Admin)
- **Endpoint**: `GET /api/admin/payments/{id}`
- **Auth required**: Có (Admin only)
- **Response Data (`PaymentDetailRecord`)**: Trả về `userPaymentInfo` + mảng danh sách `cashbacks` chi tiết thuộc đợt thanh toán này.

#### 4. Cập nhật trạng thái Payment (Dành cho Admin)
- **Endpoint**: `PATCH /api/admin/payments/{id}/status`
- **Auth required**: Có (Admin only)
- **Request Body (`PaymentUpdateStatusRequest`)**:
  ```json
  {
    "status": "Completed"
  }
  ```
- **Quy tắc chuyển trạng thái (State Transition Rules)**:
  - `Pending` ➡️ `Completed` (Chấp nhận)
  - `Pending` ➡️ `Cancelled` (Chấp nhận, tự động gỡ `payment_id` ở bảng `cashbacks`)
  - `Completed` ➡️ *(Không thể thay đổi)* -> Trả về lỗi HTTP `400`, `code`: `"payment_already_completed"`
  - `Cancelled` ➡️ *(Không thể thay đổi)* -> Trả về lỗi HTTP `400`, `code`: `"payment_already_cancelled"`

---

### 5.4 API Dashboard Thống kê (Dashboard Stats APIs)

#### 1. Lấy thông tin thống kê Dashboard cá nhân (User Dashboard)
- **Endpoint**: `GET /api/user/dashboard`
- **Auth required**: Có (User / Admin)
- **Response Data (`DashboardStats`)**:
  ```json
  {
    "ok": true,
    "code": "ok",
    "data": {
      "countOrders": 12,
      "totalCashback": 150000.0,
      "totalPaymentsPending": 50000.0,
      "totalPaymentsCompleted": 100000.0
    }
  }
  ```

#### 2. Lấy thông tin thống kê Dashboard toàn hệ thống (Admin Dashboard)
- **Endpoint**: `GET /api/admin/dashboard`
- **Auth required**: Có (Admin only)
- **Response Data (`DashboardStats`)**:
  ```json
  {
    "ok": true,
    "code": "ok",
    "data": {
      "countOrders": 150,
      "totalCashback": 25000000.0,
      "totalPaymentsPending": 2000000.0,
      "totalPaymentsCompleted": 23000000.0
    }
  }
  ```

---


## 6. Hướng dẫn tạo mã VietQR chuyển khoản cho Admin Frontend

Khi Admin mở danh sách hoặc chi tiết một Payment có trạng thái `Pending`, Frontend cần tự động hiển thị mã QR thanh toán (VietQR) để Admin mở app ngân hàng quét và chuyển khoản trực tiếp.

### 6.1 Cú pháp URL VietQR Quick Link
Frontend gọi URL ảnh VietQR trực tiếp từ CDN `img.vietqr.io` mà không cần gọi qua backend:

```text
https://img.vietqr.io/image/<BANK_ID>-<ACCOUNT_NO>-compact2.png?amount=<AMOUNT>&addInfo=<MEMO>&accountName=<ACCOUNT_NAME>
```

### 6.2 Bảng ánh xạ thuộc tính (Mapping Table)

| Tham số VietQR | Thuộc tính từ Response API (`userPaymentInfo`) | Ví dụ | Lưu ý |
| --- | --- | --- | --- |
| `<BANK_ID>` | `payment.userPaymentInfo.bankCode` | `MB`, `VCB`, `ICB`, `TCB` | Mã ngân hàng chuẩn VietQR |
| `<ACCOUNT_NO>` | `payment.userPaymentInfo.accountNumber` | `0381000123456` | Số tài khoản |
| `<AMOUNT>` | `Math.round(payment.amount)` | `75000` | Số tiền (số nguyên VNĐ) |
| `<MEMO>` | `Payment ${payment.id}` | `Payment pay_5a782b19` | Nội dung chuyển khoản |
| `<ACCOUNT_NAME>` | `payment.userPaymentInfo.accountName` | `NGUYEN VAN A` | Encode bằng `encodeURIComponent` |

### 6.3 Mã mẫu ví dụ tạo URL VietQR (TypeScript / React)

```typescript
function generateVietQRUrl(payment: PaymentRecord): string | null {
  const info = payment.userPaymentInfo;
  if (!info || !info.bankCode || !info.accountNumber) {
    return null; // User chưa điền thông tin ngân hàng
  }

  const bankId = info.bankCode.trim();
  const accountNo = info.accountNumber.trim();
  const amount = Math.round(payment.amount);
  const memo = encodeURIComponent(`Thanh toan cashback ${payment.id}`);
  const accountName = encodeURIComponent(info.accountName || '');

  return `https://img.vietqr.io/image/${bankId}-${accountNo}-compact2.png?amount=${amount}&addInfo=${memo}&accountName=${accountName}`;
}
```

> **Lưu ý giao diện UI cho Frontend**:
> Nếu `generateVietQRUrl` trả về `null` (User chưa nhập ngân hàng), Frontend hiển thị thẻ Cảnh báo màu vàng (Warning Banner): *"Người dùng chưa cấu hình thông tin tài khoản ngân hàng"*.

---

## 7. Module Shopee Affiliate & Conversion

### 7.1 Tạo link Shopee Affiliate
- **Endpoint**: `POST /api/shopee/affiliate`
- **Request Body**:
  ```json
  {
    "link": "https://shopee.vn/product/1101127972/15098368521",
    "affiliate_id": "17314780502",
    "sub_ids": ["ndinhnguyen", "user_id_hex"],
    "deep_and_deferred": 0
  }
  ```

### 7.2 Lấy báo cáo Conversion từ Shopee (User)
- **Endpoint**: `GET /api/shopee/conversions`
- **Query Parameters**:
  - `page_num` (int, default `1`)
  - `page_size` (int, default `20`)
  - `purchase_time_s` (int, required): Unix timestamp bắt đầu (giây)
  - `purchase_time_e` (int, required): Unix timestamp kết thúc (giây)

### 7.3 Kích hoạt đồng bộ Cashback từ Shopee (Admin)
- **Endpoint**: `POST /api/admin/shopee/conversions/sync`
- **Query Parameters**: `purchase_time_s`, `purchase_time_e`, `sub_id` (optional)
- **Response**: `{"ok": true, "code": "ok", "data": {"synced_count": 5}}`

---

## 8. Dashboard Bookmarks & Categories

### 8.1 Danh mục (Categories)
- `GET /api/categories?q=&page=1&pageSize=10&sortBy=name&sortOrder=asc`
- `POST /api/categories`: Payload `{"name": "AI", "color": "blue", "parentId": null}`
- `PUT /api/categories/{category_id}`
- `DELETE /api/categories/{category_id}`

### 8.2 Bookmark
- `GET /api/bookmarks?categoryId=&q=&page=1&pageSize=20&sortBy=createdAt&sortOrder=desc`
- `POST /api/bookmarks`: Payload `{"title": "Google", "url": "https://google.com", "description": "", "categoryId": "cat_id"}`
- `PUT /api/bookmarks/{bookmark_id}`
- `DELETE /api/bookmarks/{bookmark_id}`

---

## 9. Bảng tra cứu mã lỗi hệ thống (System Error Codes Reference)

| HTTP Status | Code Error (`code`) | Ý nghĩa & Hướng xử lý ở Frontend |
| --- | --- | --- |
| `401` | `auth_required` | Chưa đăng nhập hoặc Token hết hạn. Điều hướng về trang Login. |
| `403` | `auth_forbidden` | Không có quyền truy cập (Ví dụ: User thường truy cập API Admin). |
| `404` | `user_not_found` | Không tìm thấy người dùng. |
| `404` | `payment_not_found` | Không tìm thấy mã đợt thanh toán (Payment ID). |
| `400` | `payment_already_completed` | Đợt thanh toán đã hoàn thành, không thể thay đổi trạng thái. |
| `400` | `payment_already_cancelled` | Đợt thanh toán đã bị hủy, không thể thay đổi trạng thái. |
| `400` | `invalid_status_transition` | Trạng thái chuyển đổi không hợp lệ. |
| `404` | `product_not_found` | Sản phẩm Shopee không tồn tại hoặc link sai. |
| `400` | `link_format_invalid` | Định dạng đường dẫn Shopee không đúng quy chuẩn. |
| `500` | `authentication unavailable` | Thiếu cấu hình JWT Secret hoặc Google Client ID phía Server. |
