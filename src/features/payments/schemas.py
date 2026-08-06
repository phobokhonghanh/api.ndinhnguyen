from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field
from features.cashbacks.schemas import CashbackRecord


class UserPaymentProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(..., alias="userId", description="User ID (32 ký tự Hex)", json_schema_extra={"example": "00686da162014d34804c00d0c8572ce7"})
    email: str | None = Field(None, description="Email người nhận", json_schema_extra={"example": "user@example.com"})
    name: str | None = Field(None, description="Tên người nhận", json_schema_extra={"example": "Nguyen Van A"})
    bank_code: str | None = Field(None, alias="bankCode", description="Mã ngân hàng (MB, VCB, TCB, ...)", json_schema_extra={"example": "MB"})
    bank_name: str | None = Field(None, alias="bankName", description="Tên đầy đủ của ngân hàng (tự động tra cứu)", json_schema_extra={"example": "Ngân hàng TMCP Quân Đội"})
    account_number: str | None = Field(None, alias="accountNumber", description="Số tài khoản ngân hàng", json_schema_extra={"example": "0381000123456"})
    account_name: str | None = Field(None, alias="accountName", description="Tên chủ tài khoản ngân hàng", json_schema_extra={"example": "NGUYEN VAN A"})


class PaymentRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid4()), description="Mã đợt thanh toán (Payment ID)", json_schema_extra={"example": "pay_5a782b1928cf"})
    user_id: str = Field(..., alias="userId", description="ID người dùng nhận thanh toán", json_schema_extra={"example": "00686da162014d34804c00d0c8572ce7"})
    amount: float = Field(..., description="Tổng giá trị số tiền thanh toán (VNĐ)", json_schema_extra={"example": 75000.0})
    cashback_count: int = Field(..., alias="cashbackCount", description="Số lượng khoản cashback trong đợt này", json_schema_extra={"example": 5})
    status: str = Field(..., description="Trạng thái thanh toán ('Pending', 'Completed', hoặc 'Cancelled')", json_schema_extra={"example": "Pending"})
    user_payment_info: UserPaymentProfile | None = Field(None, alias="userPaymentInfo", description="Thông tin tài khoản ngân hàng (live khi Pending, snapshot khi Completed)")
    created_at: str | None = Field(None, alias="createdAt", description="Thời gian tạo đợt thanh toán")
    paid_at: str | None = Field(None, alias="paidAt", description="Thời gian thực hiện thanh toán thành công (chỉ có khi status = Completed)")
    updated_at: str | None = Field(None, alias="updatedAt", description="Thời gian cập nhật gần nhất")


class PaymentDetailRecord(PaymentRecord):
    cashbacks: list[CashbackRecord] = Field(default_factory=list, description="Danh sách các khoản cashback chi tiết đính kèm đợt thanh toán này")


class PaymentUpdateStatusRequest(BaseModel):
    status: str = Field(..., description="Trạng thái mới cần chuyển đổi ('Completed' hoặc 'Cancelled')", json_schema_extra={"example": "Completed"})


class ReconciliationSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    created_payments_count: int = Field(..., alias="createdPaymentsCount", description="Số đợt thanh toán mới được khởi tạo", json_schema_extra={"example": 2})
    total_amount: float = Field(..., alias="totalAmount", description="Tổng số tiền cashback đối soát trong chu kỳ (VNĐ)", json_schema_extra={"example": 150000.0})
    total_cashbacks_processed: int = Field(..., alias="totalCashbacksProcessed", description="Tổng số lượng bản ghi cashback đã xử lý", json_schema_extra={"example": 10})
