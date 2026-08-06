from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.helpers import get_db
from core.responses import Response, json_response
from features.users import repository as user_repo
from features.users.schemas import UserPaymentInfo, UpdatePaymentInfoRequest, DashboardStats

router = APIRouter(tags=["Users"])


@router.get(
    "/api/user/payment-info",
    response_model=Response[UserPaymentInfo],
    summary="Lấy thông tin tài khoản ngân hàng của người dùng hiện tại",
    description="Trả về thông tin tài khoản ngân hàng hiện tại của người dùng đang đăng nhập (bao gồm bankCode, bankName, accountNumber, accountName).",
)
async def get_user_payment_info(request: Request) -> JSONResponse:
    """
    Retrieves the logged-in user's payment / bank account information.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)

    user_id = user.get("sub")
    db = get_db()
    user_record = await user_repo.get_user_by_id(db, user_id)
    if not user_record:
        return json_response(ok=False, code="user_not_found", status_code=404)

    payment_info = UserPaymentInfo(
        bankCode=user_record.get("bankCode"),
        bankName=user_record.get("bankName"),
        accountNumber=user_record.get("accountNumber"),
        accountName=user_record.get("accountName"),
    )
    return json_response(data=payment_info)


@router.put(
    "/api/user/payment-info",
    response_model=Response[UserPaymentInfo],
    summary="Cập nhật thông tin tài khoản ngân hàng của người dùng hiện tại",
    description="Cập nhật thông tin tài khoản ngân hàng của người dùng đang đăng nhập (chỉ cần truyền bank_code, account_number, account_name; bankName sẽ tự động tra cứu).",
)
async def update_user_payment_info(
    request: Request,
    payload: UpdatePaymentInfoRequest
) -> JSONResponse:
    """
    Updates the logged-in user's payment / bank account information.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)

    user_id = user.get("sub")
    db = get_db()

    updated_user = await user_repo.update_user_payment_info(
        db=db,
        user_id=user_id,
        bank_code=payload.bank_code,
        account_number=payload.account_number,
        account_name=payload.account_name,
    )
    if not updated_user:
        return json_response(ok=False, code="user_not_found", status_code=404)

    payment_info = UserPaymentInfo(
        bankCode=updated_user.get("bankCode"),
        bankName=updated_user.get("bankName"),
        accountNumber=updated_user.get("accountNumber"),
        accountName=updated_user.get("accountName"),
    )
    return json_response(data=payment_info)


@router.get(
    "/api/user/dashboard",
    response_model=Response[DashboardStats],
    summary="Lấy thông tin dashboard thống kê của người dùng hiện tại",
    description="Trả về tổng số lượng đơn hàng (countOrders), tổng cashback tích lũy (totalCashback), tổng tiền đợt thanh toán đang chờ (totalPaymentsPending) và đã hoàn thành (totalPaymentsCompleted) của người dùng đang đăng nhập.",
)
async def get_user_dashboard(request: Request) -> JSONResponse:
    """
    Retrieves logged-in user dashboard stats.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)

    user_id = user.get("sub")
    db = get_db()
    stats = await user_repo.get_dashboard_stats(db, user_id=user_id)
    return json_response(data=DashboardStats(**stats))


@router.get(
    "/api/admin/dashboard",
    response_model=Response[DashboardStats],
    summary="Lấy thông tin dashboard thống kê toàn hệ thống (Admin only)",
    description="Trả về tổng số lượng đơn hàng toàn hệ thống (countOrders), tổng cashback tích lũy (totalCashback), tổng tiền đợt thanh toán đang chờ (totalPaymentsPending) và đã hoàn thành (totalPaymentsCompleted).",
)
async def get_admin_dashboard(request: Request) -> JSONResponse:
    """
    Retrieves admin system-wide dashboard stats (Admin only).
    """
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)
    if user.get("role") != "admin":
        return json_response(ok=False, code="auth_forbidden", status_code=403)

    db = get_db()
    stats = await user_repo.get_dashboard_stats(db, user_id=None)
    return json_response(data=DashboardStats(**stats))

