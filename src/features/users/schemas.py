from pydantic import BaseModel, Field


class User(BaseModel):
    id: str = Field(..., description="User ID Hex (32 ký tự)", json_schema_extra={"example": "00686da162014d34804c00d0c8572ce7"})
    email: str = Field(..., description="Email người dùng", json_schema_extra={"example": "user@example.com"})
    name: str | None = Field(None, description="Họ và tên người dùng", json_schema_extra={"example": "Nguyen Van A"})
    picture: str | None = Field(None, description="URL ảnh đại diện Google", json_schema_extra={"example": "https://lh3.googleusercontent.com/a/..."})
    role: str = Field("user", description="Vai trò người dùng ('user' hoặc 'admin')", json_schema_extra={"example": "user"})
    bankCode: str | None = Field(None, description="Mã ngân hàng (MB, VCB, TCB, ...)", json_schema_extra={"example": "MB"})
    bankName: str | None = Field(None, description="Tên ngân hàng (tự động tra cứu từ bankCode)", json_schema_extra={"example": "Ngân hàng TMCP Quân Đội"})
    accountNumber: str | None = Field(None, description="Số tài khoản ngân hàng", json_schema_extra={"example": "0381000123456"})
    accountName: str | None = Field(None, description="Tên chủ tài khoản ngân hàng", json_schema_extra={"example": "NGUYEN VAN A"})
    createdAt: str | None = Field(None, description="Thời gian tạo tài khoản")
    updatedAt: str | None = Field(None, description="Thời gian cập nhật gần nhất")


class UserPaymentInfo(BaseModel):
    bankCode: str | None = Field(None, description="Mã ngân hàng (MB, VCB, TCB, ...)", json_schema_extra={"example": "MB"})
    bankName: str | None = Field(None, description="Tên ngân hàng (tự động tra cứu từ bankCode)", json_schema_extra={"example": "Ngân hàng TMCP Quân Đội"})
    accountNumber: str | None = Field(None, description="Số tài khoản ngân hàng", json_schema_extra={"example": "0381000123456"})
    accountName: str | None = Field(None, description="Tên chủ tài khoản ngân hàng", json_schema_extra={"example": "NGUYEN VAN A"})


class UpdatePaymentInfoRequest(BaseModel):
    bank_code: str | None = Field(None, description="Mã ngân hàng (MB, VCB, TCB, ...)", json_schema_extra={"example": "MB"})
    account_number: str | None = Field(None, description="Số tài khoản ngân hàng", json_schema_extra={"example": "0381000123456"})
    account_name: str | None = Field(None, description="Tên chủ tài khoản ngân hàng", json_schema_extra={"example": "NGUYEN VAN A"})


class DashboardStats(BaseModel):
    countOrders: int = Field(..., description="Tổng số đơn hàng / cashback", json_schema_extra={"example": 12})
    totalCashback: float = Field(..., description="Tổng số tiền cashback tích lũy (VNĐ)", json_schema_extra={"example": 150000.0})
    totalPaymentsPending: float = Field(..., description="Tổng số tiền các đợt thanh toán đang chờ xử lý (VNĐ)", json_schema_extra={"example": 50000.0})
    totalPaymentsCompleted: float = Field(..., description="Tổng số tiền các đợt thanh toán đã hoàn thành (VNĐ)", json_schema_extra={"example": 100000.0})


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(..., description="Google OAuth ID Token thu được từ Google Client SDK", json_schema_extra={"example": "eyJhbGciOiJSUzI1NiIs..."})


class LoginResponseData(BaseModel):
    token: str = Field(..., description="JWT Session Token của hệ thống", json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."})
    user: User = Field(..., description="Thông tin profile của người dùng")
