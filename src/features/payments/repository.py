from typing import Any
from uuid import uuid4
import random
import time
from datetime import datetime
from core.banks import get_bank_name_by_code
from infra.d1 import first, row_value, rows
from core.constants import CASHBACK_STATUS_APPROVED, CASHBACK_STATUS_COMPLETED, PAYMENT_STATUS_PENDING
from features.cashbacks.repository import _cashback
from features.payments.schemas import (
    PaymentRecord,
    UserPaymentProfile,
    ReconciliationSummary,
)


def _payment(row: Any) -> PaymentRecord:
    user_info = None
    status = row_value(row, "status")

    # Snapshot vs Live bank info logic:
    p_bank_code = row_value(row, "p_bank_code") or row_value(row, "bank_code")
    p_account_number = row_value(row, "p_account_number") or row_value(row, "account_number")
    p_account_name = row_value(row, "p_account_name") or row_value(row, "account_name")

    u_bank_code = row_value(row, "u_bank_code")
    u_account_number = row_value(row, "u_account_number")
    u_account_name = row_value(row, "u_account_name")

    if status == "Completed" and p_bank_code is not None:
        # Use frozen snapshot saved on the payment record
        bank_code = p_bank_code
        account_number = p_account_number
        account_name = p_account_name
    else:
        # Use live bank account details from users table (fallback to payment columns if user table column is null)
        bank_code = u_bank_code if u_bank_code is not None else p_bank_code
        account_number = u_account_number if u_account_number is not None else p_account_number
        account_name = u_account_name if u_account_name is not None else p_account_name

    bank_name = get_bank_name_by_code(bank_code) if bank_code else None

    if row_value(row, "u_id") or row_value(row, "user_id"):
        user_info = UserPaymentProfile(
            userId=row_value(row, "u_id") or row_value(row, "user_id"),
            email=row_value(row, "u_email"),
            name=row_value(row, "u_name"),
            bankCode=bank_code,
            bankName=bank_name,
            accountNumber=account_number,
            accountName=account_name,
        )

    return PaymentRecord(
        id=row_value(row, "id"),
        user_id=row_value(row, "user_id"),
        amount=float(int(float(row_value(row, "amount") or 0))),
        cashback_count=row_value(row, "cashback_count"),
        status=status,
        user_payment_info=user_info,
        created_at=row_value(row, "created_at"),
        paid_at=row_value(row, "paid_at"),
        updated_at=row_value(row, "updated_at"),
    )


async def reconcile_and_create_payments(
    db: Any, min_amount: float = 50000.0
) -> ReconciliationSummary:
    # 1. Fetch all eligible approved cashbacks without payment_id
    eligible_rows = await rows(
        db.prepare(
            """SELECT id, user_id, cashback_amount
               FROM cashbacks
               WHERE status = ? AND payment_id IS NULL"""
        ).bind(CASHBACK_STATUS_APPROVED)
    )

    # Group by user_id
    user_cashbacks: dict[str, list[dict[str, Any]]] = {}
    for r in eligible_rows:
        u_id = row_value(r, "user_id")
        cb_id = row_value(r, "id")
        amt = float(int(float(row_value(r, "cashback_amount") or 0.0)))
        if u_id not in user_cashbacks:
            user_cashbacks[u_id] = []
        user_cashbacks[u_id].append({"id": cb_id, "amount": amt})

    created_count = 0
    total_reconciled_amount = 0.0
    total_processed_cashbacks = 0

    # Process each user
    for u_id, items in user_cashbacks.items():
        total_user_amt = sum(item["amount"] for item in items)
        if total_user_amt >= min_amount:
            payment_id = str(int(time.time())) + str(random.randint(1000, 9999))
            cb_count = len(items)

            # Insert payment (bank snapshot fields remain NULL when status is Pending)
            await db.prepare(
                """INSERT INTO payments (id, user_id, amount, cashback_count, status)
                   VALUES (?, ?, ?, ?, ?)"""
            ).bind(payment_id, u_id, total_user_amt, cb_count, PAYMENT_STATUS_PENDING).run()

            # Update linked cashbacks to status Completed and link payment_id
            for item in items:
                await db.prepare(
                    """UPDATE cashbacks
                       SET payment_id = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE id = ?"""
                ).bind(payment_id, CASHBACK_STATUS_COMPLETED, item["id"]).run()

            created_count += 1
            total_reconciled_amount += total_user_amt
            total_processed_cashbacks += cb_count

    return ReconciliationSummary(
        createdPaymentsCount=created_count,
        totalAmount=total_reconciled_amount,
        totalCashbacksProcessed=total_processed_cashbacks,
    )


async def get_payment_by_id(db: Any, payment_id: str) -> PaymentRecord | None:
    row = await first(
        db.prepare(
            """SELECT p.id, p.user_id, p.amount, p.cashback_count, p.status, p.created_at, p.paid_at, p.updated_at,
                      p.bank_code as p_bank_code, p.account_number as p_account_number, p.account_name as p_account_name,
                      u.id as u_id, u.email as u_email, u.name as u_name,
                      u.bank_code as u_bank_code, u.account_number as u_account_number, u.account_name as u_account_name
               FROM payments p
               LEFT JOIN users u ON p.user_id = u.id
               WHERE p.id = ?
               LIMIT 1"""
        ).bind(payment_id)
    )
    if row is None:
        return None
    return _payment(row)


async def get_payment_cashbacks(db: Any, payment_id: str):
    result_rows = await rows(
        db.prepare(
            """SELECT id, user_id, platform, cashback_amount, status, checkout_id, conversion, payment_id, created_at, updated_at
               FROM cashbacks
               WHERE payment_id = ?
               ORDER BY created_at DESC"""
        ).bind(payment_id)
    )
    return [_cashback(r) for r in result_rows]


async def count_payments(
    db: Any, user_id: str | None = None, status: str | None = None
) -> int:
    query = "SELECT COUNT(*) as count FROM payments WHERE 1=1"
    params = []
    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)
    if status:
        query += " AND status = ?"
        params.append(status)

    stmt = db.prepare(query)
    if params:
        stmt = stmt.bind(*params)
    row = await first(stmt)
    return int(row_value(row, "count") or 0)


async def list_payments_paginated(
    db: Any, page: int, page_size: int, user_id: str | None = None, status: str | None = None
) -> list[PaymentRecord]:
    offset = (page - 1) * page_size
    query = """SELECT p.id, p.user_id, p.amount, p.cashback_count, p.status, p.created_at, p.paid_at, p.updated_at,
                      p.bank_code as p_bank_code, p.account_number as p_account_number, p.account_name as p_account_name,
                      u.id as u_id, u.email as u_email, u.name as u_name,
                      u.bank_code as u_bank_code, u.account_number as u_account_number, u.account_name as u_account_name
               FROM payments p
               LEFT JOIN users u ON p.user_id = u.id
               WHERE 1=1"""
    params = []
    if user_id:
        query += " AND p.user_id = ?"
        params.append(user_id)
    if status:
        query += " AND p.status = ?"
        params.append(status)

    query += " ORDER BY p.created_at DESC LIMIT ? OFFSET ?"
    params.extend([page_size, offset])

    result_rows = await rows(db.prepare(query).bind(*params))
    return [_payment(r) for r in result_rows]


async def update_payment_status(
    db: Any, payment_id: str, new_status: str
) -> PaymentRecord | None:
    if new_status == "Completed":
        # Fetch current payment to know user_id
        payment_row = await first(
            db.prepare("SELECT user_id FROM payments WHERE id = ?").bind(payment_id)
        )
        if payment_row:
            u_id = row_value(payment_row, "user_id")
            # Fetch user's current live bank details to freeze snapshot
            user_row = await first(
                db.prepare("SELECT bank_code, account_number, account_name FROM users WHERE id = ?").bind(u_id)
            )
            u_bank_code = row_value(user_row, "bank_code") if user_row else None
            u_account_number = row_value(user_row, "account_number") if user_row else None
            u_account_name = row_value(user_row, "account_name") if user_row else None

            # Freeze bank details snapshot into payment record and set paid_at
            await db.prepare(
                """UPDATE payments
                   SET status = ?, bank_code = ?, account_number = ?, account_name = ?, paid_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?"""
            ).bind(new_status, u_bank_code, u_account_number, u_account_name, payment_id).run()
        else:
            await db.prepare(
                """UPDATE payments
                   SET status = ?, paid_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?"""
            ).bind(new_status, payment_id).run()
    else:
        await db.prepare(
            """UPDATE payments
               SET status = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?"""
        ).bind(new_status, payment_id).run()

    return await get_payment_by_id(db, payment_id)
