import json
from test_cashbacks import CashbackTestClient
from core.auth import generate_jwt


def test_banks_api():
    tc = CashbackTestClient()
    with tc as client:
        res = client.get("/api/banks")
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        banks = data["data"]
        assert isinstance(banks, list)
        assert len(banks) > 0
        # Check first item contains required properties
        mb_bank = next((b for b in banks if b["code"] == "MB"), None)
        assert mb_bank is not None
        assert mb_bank["short_name"] == "MBBank"
        assert mb_bank["bin"] == "970422"


def test_user_payment_info_workflow():
    tc = CashbackTestClient()
    u1_id = "00000000000000000000000000000001"

    cursor = tc.db.conn.cursor()
    cursor.execute("INSERT INTO users (id, email, role) VALUES (?, 'user1@test.com', 'user')", (u1_id,))
    tc.db.conn.commit()

    with tc as client:
        token = generate_jwt({"sub": u1_id, "email": "user1@test.com", "role": "user"}, "secret_jwt")
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Get payment info (initially empty)
        res = client.get("/api/user/payment-info", headers=headers)
        assert res.status_code == 200
        assert res.json()["ok"] is True
        assert res.json()["data"].get("bankCode") is None

        # 2. Update payment info (without bank_name, system resolves bankName dynamically)
        payload = {
            "bank_code": "MB",
            "account_number": "0987654321",
            "account_name": "NGUYEN VAN A"
        }
        res_update = client.put("/api/user/payment-info", json=payload, headers=headers)
        assert res_update.status_code == 200
        data = res_update.json()["data"]
        assert data["bankCode"] == "MB"
        assert data["bankName"] == "Ngân hàng TMCP Quân Đội"
        assert data["accountNumber"] == "0987654321"
        assert data["accountName"] == "NGUYEN VAN A"

        # 3. Get payment info again
        res_check = client.get("/api/user/payment-info", headers=headers)
        assert res_check.status_code == 200
        assert res_check.json()["data"]["bankCode"] == "MB"
        assert res_check.json()["data"]["bankName"] == "Ngân hàng TMCP Quân Đội"


def test_bank_snapshot_on_completed_payment():
    """
    Tests that:
    1. Pending payment reflects LIVE user bank account info.
    2. When admin updates status to 'Completed', payment freezes SNAPSHOT of user bank account.
    3. Subsequent changes to user bank account do NOT alter the Completed payment snapshot.
    """
    tc = CashbackTestClient()
    u_id = "00000000000000000000000000000099"
    cursor = tc.db.conn.cursor()
    cursor.execute(
        "INSERT INTO users (id, email, role, bank_code, account_number, account_name) VALUES (?, 'snapshot@test.com', 'user', 'MB', '111111111', 'ORIGINAL OWNER')",
        (u_id,)
    )
    cursor.execute(
        "INSERT INTO payments (id, user_id, amount, cashback_count, status) VALUES ('pay_snap', ?, 100000.0, 2, 'Pending')",
        (u_id,)
    )
    tc.db.conn.commit()

    with tc as client:
        admin_headers = {"Authorization": "Bearer secret_admin"}
        user_headers = {"Authorization": f"Bearer {generate_jwt({'sub': u_id, 'email': 'snapshot@test.com', 'role': 'user'}, 'secret_jwt')}"}

        # 1. Pending payment shows live bank info (MB / 111111111) and paidAt is None (excluded when None)
        res_p1 = client.get("/api/admin/payments/pay_snap", headers=admin_headers)
        assert res_p1.status_code == 200
        assert res_p1.json()["data"].get("paidAt") is None
        p_info = res_p1.json()["data"]["userPaymentInfo"]
        assert p_info["bankCode"] == "MB"
        assert p_info["accountNumber"] == "111111111"
        assert p_info["accountName"] == "ORIGINAL OWNER"

        # 2. Transition status to Completed -> Triggers Snapshot freezing & sets paidAt
        res_comp = client.patch("/api/admin/payments/pay_snap/status", json={"status": "Completed"}, headers=admin_headers)
        assert res_comp.status_code == 200
        assert res_comp.json()["data"]["paidAt"] is not None
        p_comp = res_comp.json()["data"]["userPaymentInfo"]
        assert p_comp["bankCode"] == "MB"
        assert p_comp["accountNumber"] == "111111111"

        # 3. User updates their current bank account info to VCB / 999999999
        res_upd = client.put(
            "/api/user/payment-info",
            json={"bank_code": "VCB", "account_number": "999999999", "account_name": "NEW OWNER"},
            headers=user_headers
        )
        assert res_upd.status_code == 200

        # 4. User profile live info is now VCB / 999999999
        res_user_info = client.get("/api/user/payment-info", headers=user_headers)
        assert res_user_info.json()["data"]["bankCode"] == "VCB"

        # 5. Completed payment detail STILL reflects frozen snapshot (MB / 111111111)
        res_p2 = client.get("/api/admin/payments/pay_snap", headers=admin_headers)
        assert res_p2.status_code == 200
        p_info2 = res_p2.json()["data"]["userPaymentInfo"]
        assert p_info2["bankCode"] == "MB"
        assert p_info2["accountNumber"] == "111111111"
        assert p_info2["accountName"] == "ORIGINAL OWNER"
        assert p_info2["bankName"] == "Ngân hàng TMCP Quân Đội"


def test_payment_reconciliation_threshold_and_status():
    tc = CashbackTestClient()
    u_eligible = "00000000000000000000000000000002"
    u_ineligible = "00000000000000000000000000000003"

    cursor = tc.db.conn.cursor()
    cursor.execute("INSERT INTO users (id, email, role, bank_code, account_number, account_name) VALUES (?, 'eligible@test.com', 'user', 'VCB', '1234567890', 'LE VAN B')", (u_eligible,))
    cursor.execute("INSERT INTO users (id, email, role) VALUES (?, 'ineligible@test.com', 'user')", (u_ineligible,))

    # u_eligible has 2 approved cashbacks of 30,000 each -> total 60,000 >= 50,000 VNĐ
    cursor.execute("""
    INSERT INTO cashbacks (id, user_id, platform, cashback_amount, status, checkout_id, conversion)
    VALUES ('cb_1', ?, 'Shopee API', 30000.0, 'Approved', 'chk_1', '{}')
    """, (u_eligible,))
    cursor.execute("""
    INSERT INTO cashbacks (id, user_id, platform, cashback_amount, status, checkout_id, conversion)
    VALUES ('cb_2', ?, 'Shopee API', 30000.0, 'Approved', 'chk_2', '{}')
    """, (u_eligible,))

    # u_ineligible has 1 approved cashback of 40,000 < 50,000 VNĐ
    cursor.execute("""
    INSERT INTO cashbacks (id, user_id, platform, cashback_amount, status, checkout_id, conversion)
    VALUES ('cb_3', ?, 'Shopee API', 40000.0, 'Approved', 'chk_3', '{}')
    """, (u_ineligible,))

    tc.db.conn.commit()

    with tc as client:
        admin_headers = {"Authorization": "Bearer secret_admin"}

        # 1. Run reconciliation
        res = client.post("/api/admin/payments/reconcile", headers=admin_headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["createdPaymentsCount"] == 1
        assert data["totalAmount"] == 60000.0
        assert data["totalCashbacksProcessed"] == 2

        # 2. Check admin list payments
        res_list = client.get("/api/admin/payments", headers=admin_headers)
        assert res_list.status_code == 200
        payments = res_list.json()["data"]
        assert len(payments) == 1
        payment = payments[0]
        assert payment["userId"] == u_eligible
        assert payment["amount"] == 60000.0
        assert payment["cashbackCount"] == 2
        assert payment["status"] == "Pending"
        # Check VietQR user payment profile included
        assert payment["userPaymentInfo"]["bankCode"] == "VCB"
        assert payment["userPaymentInfo"]["accountNumber"] == "1234567890"
        assert payment["userPaymentInfo"]["accountName"] == "LE VAN B"

        payment_id = payment["id"]

        # 3. Get admin payment detail with cashbacks
        res_detail = client.get(f"/api/admin/payments/{payment_id}", headers=admin_headers)
        assert res_detail.status_code == 200
        detail = res_detail.json()["data"]
        assert len(detail["cashbacks"]) == 2
        for cb in detail["cashbacks"]:
            assert cb["status"] == "Completed"
            assert cb["paymentId"] == payment_id

        # 4. Check ineligible user has no payments
        user_ineligible_token = generate_jwt({"sub": u_ineligible, "email": "ineligible@test.com", "role": "user"}, "secret_jwt")
        res_user_p = client.get("/api/payments", headers={"Authorization": f"Bearer {user_ineligible_token}"})
        assert res_user_p.status_code == 200
        assert len(res_user_p.json()["data"]) == 0

        # 5. Check eligible user sees their payment
        user_eligible_token = generate_jwt({"sub": u_eligible, "email": "eligible@test.com", "role": "user"}, "secret_jwt")
        res_user_p2 = client.get("/api/payments", headers={"Authorization": f"Bearer {user_eligible_token}"})
        assert res_user_p2.status_code == 200
        assert len(res_user_p2.json()["data"]) == 1
        assert res_user_p2.json()["data"][0]["id"] == payment_id


def test_payment_status_transitions():
    tc = CashbackTestClient()
    u_id = "00000000000000000000000000000004"
    cursor = tc.db.conn.cursor()
    cursor.execute("INSERT INTO users (id, email, role) VALUES (?, 'transition@test.com', 'user')", (u_id,))

    cursor.execute("""
    INSERT INTO payments (id, user_id, amount, cashback_count, status)
    VALUES ('pay_100', ?, 100000.0, 3, 'Pending')
    """, (u_id,))
    tc.db.conn.commit()

    with tc as client:
        admin_headers = {"Authorization": "Bearer secret_admin"}

        # Invalid transition: Pending -> InvalidStatus
        res_inv = client.patch("/api/admin/payments/pay_100/status", json={"status": "Unknown"}, headers=admin_headers)
        assert res_inv.status_code == 400
        assert res_inv.json()["code"] == "invalid_status_transition"

        # Valid transition: Pending -> Cancelled
        res_can = client.patch("/api/admin/payments/pay_100/status", json={"status": "Cancelled"}, headers=admin_headers)
        assert res_can.status_code == 200
        assert res_can.json()["data"]["status"] == "Cancelled"

        # Valid transition: Cancelled -> Pending
        res_pen = client.patch("/api/admin/payments/pay_100/status", json={"status": "Pending"}, headers=admin_headers)
        assert res_pen.status_code == 200
        assert res_pen.json()["data"]["status"] == "Pending"

        # Valid transition: Pending -> Completed
        res_comp = client.patch("/api/admin/payments/pay_100/status", json={"status": "Completed"}, headers=admin_headers)
        assert res_comp.status_code == 200
        assert res_comp.json()["data"]["status"] == "Completed"

        # Terminal state check: Completed -> Cancelled (should be forbidden)
        res_block = client.patch("/api/admin/payments/pay_100/status", json={"status": "Cancelled"}, headers=admin_headers)
        assert res_block.status_code == 400
        assert res_block.json()["code"] == "payment_already_completed"


def test_payment_permissions():
    tc = CashbackTestClient()
    u1_id = "00000000000000000000000000000005"
    u2_id = "00000000000000000000000000000006"

    cursor = tc.db.conn.cursor()
    cursor.execute("INSERT INTO users (id, email, role) VALUES (?, 'u5@test.com', 'user')", (u1_id,))
    cursor.execute("INSERT INTO users (id, email, role) VALUES (?, 'u6@test.com', 'user')", (u2_id,))
    cursor.execute("INSERT INTO payments (id, user_id, amount, cashback_count, status) VALUES ('pay_u1', ?, 50000.0, 1, 'Pending')", (u1_id,))
    tc.db.conn.commit()

    with tc as client:
        u1_token = generate_jwt({"sub": u1_id, "email": "u5@test.com", "role": "user"}, "secret_jwt")
        u2_token = generate_jwt({"sub": u2_id, "email": "u6@test.com", "role": "user"}, "secret_jwt")

        # Admin routes forbidden for normal user
        res_admin = client.get("/api/admin/payments", headers={"Authorization": f"Bearer {u1_token}"})
        assert res_admin.status_code == 403

        # User 1 can view their payment detail
        res_p1 = client.get("/api/payments/pay_u1", headers={"Authorization": f"Bearer {u1_token}"})
        assert res_p1.status_code == 200

        # User 2 cannot view User 1's payment detail
        res_p2 = client.get("/api/payments/pay_u1", headers={"Authorization": f"Bearer {u2_token}"})
        assert res_p2.status_code == 404


def test_dashboard_stats_user_and_admin():
    tc = CashbackTestClient()
    u1_id = "00000000000000000000000000000010"
    u2_id = "00000000000000000000000000000011"

    cursor = tc.db.conn.cursor()
    cursor.execute("INSERT INTO users (id, email, role) VALUES (?, 'dash1@test.com', 'user')", (u1_id,))
    cursor.execute("INSERT INTO users (id, email, role) VALUES (?, 'dash2@test.com', 'user')", (u2_id,))

    # User 1 has 2 cashbacks (total 50,000) and 1 pending payment (amount 50,000)
    cursor.execute("INSERT INTO cashbacks (id, user_id, platform, cashback_amount, status, checkout_id, conversion) VALUES ('cb_d1', ?, 'Shopee', 30000.0, 'Approved', 'chk_d1', '{}')", (u1_id,))
    cursor.execute("INSERT INTO cashbacks (id, user_id, platform, cashback_amount, status, checkout_id, conversion) VALUES ('cb_d2', ?, 'Shopee', 20000.0, 'Approved', 'chk_d2', '{}')", (u1_id,))
    cursor.execute("INSERT INTO payments (id, user_id, amount, cashback_count, status) VALUES ('pay_d1', ?, 50000.0, 2, 'Pending')", (u1_id,))

    # User 2 has 1 cashback (total 100,000) and 1 completed payment (amount 100,000)
    cursor.execute("INSERT INTO cashbacks (id, user_id, platform, cashback_amount, status, checkout_id, conversion) VALUES ('cb_d3', ?, 'Shopee', 100000.0, 'Approved', 'chk_d3', '{}')", (u2_id,))
    cursor.execute("INSERT INTO payments (id, user_id, amount, cashback_count, status) VALUES ('pay_d2', ?, 100000.0, 1, 'Completed')", (u2_id,))
    tc.db.conn.commit()

    with tc as client:
        u1_token = generate_jwt({"sub": u1_id, "email": "dash1@test.com", "role": "user"}, "secret_jwt")
        admin_token = generate_jwt({"sub": "admin_id", "email": "admin@test.com", "role": "admin"}, "secret_jwt")

        # 1. User 1 Dashboard Stats
        res_u1 = client.get("/api/user/dashboard", headers={"Authorization": f"Bearer {u1_token}"})
        assert res_u1.status_code == 200
        u1_data = res_u1.json()["data"]
        assert u1_data["countOrders"] == 2
        assert u1_data["totalCashback"] == 50000.0
        assert u1_data["totalPaymentsPending"] == 50000.0
        assert u1_data["totalPaymentsCompleted"] == 0.0

        # 2. Admin Dashboard Stats (System-wide)
        res_admin = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_admin.status_code == 200
        admin_data = res_admin.json()["data"]
        assert admin_data["countOrders"] == 3
        assert admin_data["totalCashback"] == 150000.0
        assert admin_data["totalPaymentsPending"] == 50000.0
        assert admin_data["totalPaymentsCompleted"] == 100000.0


def test_payment_min_amount_env_configuration():
    from core.settings import AppSettings
    from types import SimpleNamespace
    env = SimpleNamespace(PAYMENT_MIN_AMOUNT="100000")
    settings = AppSettings.from_env(env)
    assert settings.payment_min_amount == 100000.0


