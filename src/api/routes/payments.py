from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from api.helpers import get_db
from core.responses import Response, json_response
from features.payments import service
from features.payments.schemas import (
    PaymentRecord,
    PaymentDetailRecord,
    PaymentUpdateStatusRequest,
    ReconciliationSummary,
)

router = APIRouter(tags=["Payments"])


# --- Admin Routes ---

@router.post(
    "/api/admin/payments/reconcile",
    response_model=Response[ReconciliationSummary],
    summary="Kích hoạt đợt đối soát tự động tạo Payment (Admin only)",
    description="Gộp tất cả các khoản cashback có trạng thái 'Approved' chưa thuộc Payment nào. Với mỗi User có tổng cashback >= 50.000 VNĐ, hệ thống tự động tạo 1 đợt thanh toán (Payment) ở trạng thái 'Pending'. Thông tin ngân hàng khi 'Pending' được lấy trực tiếp (live) từ bảng Users.",
)
async def reconcile_payments(request: Request) -> JSONResponse:
    """
    Triggers weekly/adhoc payment reconciliation cycle for eligible approved cashbacks (Admin only).
    """
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)
    if user.get("role") != "admin":
        return json_response(ok=False, code="auth_forbidden", status_code=403)

    db = get_db()
    result = await service.run_reconciliation(db)
    return json_response(data=result.data, code=result.code, ok=result.ok)


@router.get(
    "/api/admin/payments",
    response_model=Response[list[PaymentRecord]],
    summary="Lấy danh sách tất cả các đợt thanh toán (Admin only)",
    description="Truy xuất danh sách đợt thanh toán với bộ lọc phân trang, người dùng hoặc trạng thái. Mỗi bản ghi bao gồm đối tượng `userPaymentInfo` hỗ trợ Frontend tạo mã QR chuyển khoản VietQR.",
)
async def get_admin_payments(
    request: Request,
    page: int = Query(1, ge=1, description="Số trang (bắt đầu từ 1)"),
    pageSize: int = Query(20, ge=1, le=100, description="Số lượng bản ghi trên một trang"),
    userId: str | None = Query(None, description="Lọc theo User ID cụ thể"),
    status: str | None = Query(None, description="Lọc theo trạng thái ('Pending', 'Completed', 'Cancelled')"),
) -> JSONResponse:
    """
    Retrieves all payments with user payment profile details (Admin only).
    """
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)
    if user.get("role") != "admin":
        return json_response(ok=False, code="auth_forbidden", status_code=403)

    db = get_db()
    records, pagination = await service.get_payments(
        db, page=page, page_size=pageSize, user_id=userId, status=status
    )
    return json_response(data=records, pagination=pagination)


@router.get(
    "/api/admin/payments/{id}",
    response_model=Response[PaymentDetailRecord],
    summary="Lấy chi tiết 1 đợt thanh toán (Admin only)",
    description="Trả về thông tin đợt thanh toán, tài khoản ngân hàng nhận tiền và danh sách tất cả các bản ghi cashback đính kèm.",
)
async def get_admin_payment_detail(
    id: str,
    request: Request,
) -> JSONResponse:
    """
    Retrieves payment details including user payment profile and linked cashbacks (Admin only).
    """
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)
    if user.get("role") != "admin":
        return json_response(ok=False, code="auth_forbidden", status_code=403)

    db = get_db()
    result = await service.get_payment_detail(db, payment_id=id)
    if not result.ok:
        return json_response(ok=False, code=result.code, status_code=404 if result.code == "payment_not_found" else 400)
    return json_response(data=result.data)


@router.patch(
    "/api/admin/payments/{id}/status",
    response_model=Response[PaymentRecord],
    summary="Cập nhật trạng thái đợt thanh toán (Admin only)",
    description="Cập nhật trạng thái đợt thanh toán. Khi chuyển sang 'Completed', hệ thống sẽ chụp ảnh đóng băng (Snapshot) thông tin ngân hàng của User tại thời điểm đó.",
)
async def update_admin_payment_status(
    id: str,
    payload: PaymentUpdateStatusRequest,
    request: Request,
) -> JSONResponse:
    """
    Updates a payment's status according to allowed workflow state transitions (Admin only).
    """
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)
    if user.get("role") != "admin":
        return json_response(ok=False, code="auth_forbidden", status_code=403)

    db = get_db()
    result = await service.update_payment_status(db, payment_id=id, new_status=payload.status)
    if not result.ok:
        status_code = 404 if result.code == "payment_not_found" else 400
        return json_response(ok=False, code=result.code, status_code=status_code)
    return json_response(data=result.data)


# --- User Routes ---

@router.get(
    "/api/payments",
    response_model=Response[list[PaymentRecord]],
    summary="Lấy danh sách đợt thanh toán của người dùng hiện tại",
    description="Truy xuất danh sách các đợt thanh toán thuộc sở hữu của người dùng đang đăng nhập.",
)
async def get_user_payments(
    request: Request,
    page: int = Query(1, ge=1, description="Số trang"),
    pageSize: int = Query(20, ge=1, le=100, description="Kích thước trang"),
    status: str | None = Query(None, description="Lọc theo trạng thái"),
) -> JSONResponse:
    """
    Retrieves the logged-in user's payment records.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)

    user_id = user.get("sub")
    db = get_db()
    records, pagination = await service.get_payments(
        db, page=page, page_size=pageSize, user_id=user_id, status=status
    )
    return json_response(data=records, pagination=pagination)


@router.get(
    "/api/payments/{id}",
    response_model=Response[PaymentDetailRecord],
    summary="Lấy chi tiết 1 đợt thanh toán của người dùng hiện tại",
    description="Trả về chi tiết đợt thanh toán và danh sách cashback đính kèm thuộc người dùng đang đăng nhập.",
)
async def get_user_payment_detail(
    id: str,
    request: Request,
) -> JSONResponse:
    """
    Retrieves the detail of a payment belonging to the logged-in user.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)

    user_id = user.get("sub")
    db = get_db()
    result = await service.get_payment_detail(db, payment_id=id, user_id=user_id)
    if not result.ok:
        return json_response(ok=False, code=result.code, status_code=404 if result.code == "payment_not_found" else 400)
    return json_response(data=result.data)
