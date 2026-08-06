import math
from typing import Any
from api.helpers import get_payment_min_amount
from core.constants import (
    PAYMENT_ALLOWED_TRANSITIONS,
    PAYMENT_STATUS_COMPLETED,
)
from core.responses import Response, Pagination
from features.payments import repository as payment_repo
from features.payments.schemas import (
    PaymentRecord,
    PaymentDetailRecord,
    ReconciliationSummary,
)


async def run_reconciliation(db: Any) -> Response[ReconciliationSummary]:
    min_amount = get_payment_min_amount()
    summary = await payment_repo.reconcile_and_create_payments(db, min_amount=min_amount)
    return Response(ok=True, code="ok", data=summary)


async def get_payments(
    db: Any,
    page: int = 1,
    page_size: int = 20,
    user_id: str | None = None,
    status: str | None = None,
) -> tuple[list[PaymentRecord], Pagination]:
    total = await payment_repo.count_payments(db, user_id=user_id, status=status)
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    pagination = Pagination(total=total, page=page, pageSize=page_size, totalPages=total_pages)
    records = await payment_repo.list_payments_paginated(
        db, page=page, page_size=page_size, user_id=user_id, status=status
    )
    return records, pagination



async def get_payment_detail(
    db: Any, payment_id: str, user_id: str | None = None
) -> Response[PaymentDetailRecord]:
    payment = await payment_repo.get_payment_by_id(db, payment_id)
    if not payment:
        return Response(ok=False, code="payment_not_found")

    if user_id and payment.user_id != user_id:
        return Response(ok=False, code="payment_not_found")

    cashbacks = await payment_repo.get_payment_cashbacks(db, payment_id)
    
    detail = PaymentDetailRecord(
        id=payment.id,
        user_id=payment.user_id,
        amount=payment.amount,
        cashback_count=payment.cashback_count,
        status=payment.status,
        user_payment_info=payment.user_payment_info,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        cashbacks=cashbacks,
    )
    return Response(ok=True, code="ok", data=detail)


async def update_payment_status(
    db: Any, payment_id: str, new_status: str
) -> Response[PaymentRecord]:
    payment = await payment_repo.get_payment_by_id(db, payment_id)
    if not payment:
        return Response(ok=False, code="payment_not_found")

    current_status = payment.status

    if current_status == PAYMENT_STATUS_COMPLETED:
        return Response(ok=False, code="payment_already_completed")

    allowed_next_statuses = PAYMENT_ALLOWED_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_next_statuses:
        return Response(ok=False, code="invalid_status_transition")

    updated = await payment_repo.update_payment_status(db, payment_id, new_status)
    return Response(ok=True, code="ok", data=updated)
