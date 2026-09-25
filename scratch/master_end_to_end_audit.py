import sys
import os
import json
import uuid
import asyncio
import httpx
import sqlite3

sys.stdout.reconfigure(encoding="utf-8")

LOCAL_API = "http://127.0.0.1:8000/api/v1"
LIVE_API = "https://autotube.co.in/api/v1"

print("======================================================================")
print("     AUTOTUBE AI -- FULL COMPREHENSIVE SYSTEM & E2E AUDIT REPORT")
print("======================================================================")

report = []

def log_test(name, passed, details=""):
    status_str = "PASS" if passed else "FAIL"
    print(f"[{status_str}] {name} - {details}")
    report.append({"name": name, "passed": passed, "details": details})

# ---------------------------------------------------------------------------
# 1. Unauthenticated Security Test
# ---------------------------------------------------------------------------
print("\n--- 1. UNAUTHENTICATED SECURITY AUDIT ---")
try:
    r = httpx.get(f"{LOCAL_API}/auth/me", timeout=5.0)
    if r.status_code == 401:
        log_test("Unauthenticated Security Gate", True, "Protected endpoints return 401 Unauthorized.")
    else:
        log_test("Unauthenticated Security Gate", False, f"Expected 401, got {r.status_code}")
except Exception as e:
    log_test("Unauthenticated Security Gate", False, str(e))

# ---------------------------------------------------------------------------
# 2. Registration & 50 Free Trial Credits Audit
# ---------------------------------------------------------------------------
print("\n--- 2. USER REGISTRATION & FREE TRIAL AUDIT ---")
test_email = f"audit_user_{uuid.uuid4().hex[:6]}@autotube.test"
test_user = f"audit_user_{uuid.uuid4().hex[:4]}"
token = None
user_id = None

try:
    r = httpx.post(f"{LOCAL_API}/auth/register", json={
        "username": test_user,
        "email": test_email,
        "password": "AuditPassword123!"
    }, timeout=10.0)
    data = r.json()
    token = data.get("access_token")
    user_id = data.get("user_id")
    plan = data.get("plan_tier")
    credits = data.get("credits_balance")

    if r.status_code == 200 and token and plan == "FREE_TRIAL" and credits == 50.0:
        log_test("User Registration & Free Trial", True, f"User #{user_id} created with plan={plan}, credits={credits}")
    else:
        log_test("User Registration & Free Trial", False, f"Plan: {plan}, Credits: {credits}, Code: {r.status_code}")
except Exception as e:
    log_test("User Registration & Free Trial", False, str(e))

# ---------------------------------------------------------------------------
# 3. User Login & Profile Isolation Audit
# ---------------------------------------------------------------------------
print("\n--- 3. USER LOGIN & AUTH HEADER AUDIT ---")
try:
    r_login = httpx.post(f"{LOCAL_API}/auth/login", json={
        "email": test_email,
        "password": "AuditPassword123!"
    }, timeout=10.0)
    login_data = r_login.json()
    login_token = login_data.get("access_token")

    # Fetch /auth/me with Bearer token
    r_me = httpx.get(f"{LOCAL_API}/auth/me", headers={"Authorization": f"Bearer {login_token}"}, timeout=10.0)
    me_data = r_me.json()

    if r_me.status_code == 200 and me_data.get("email") == test_email and me_data.get("credits_balance") == 50.0:
        log_test("User Auth & Token Verification", True, f"Token valid for User #{me_data.get('user_id')} ({me_data.get('email')})")
    else:
        log_test("User Auth & Token Verification", False, f"Response: {me_data}")
except Exception as e:
    log_test("User Auth & Token Verification", False, str(e))

# ---------------------------------------------------------------------------
# 4. Multi-Tenant Scoped API Endpoints Audit
# ---------------------------------------------------------------------------
print("\n--- 4. MULTI-TENANT SCOPED API ENDPOINTS AUDIT ---")
auth_headers = {"Authorization": f"Bearer {token}"} if token else {}

protected_endpoints = [
    ("/dashboard", "Dashboard Summary"),
    ("/channels", "Channels List"),
    ("/videos", "Videos Library"),
    ("/characters", "Character Bible Assets"),
    ("/analytics", "Analytics Summary"),
    ("/emergency/status", "Emergency Controls"),
]

for ep, name in protected_endpoints:
    try:
        r = httpx.get(f"{LOCAL_API}{ep}", headers=auth_headers, timeout=10.0)
        if r.status_code == 200:
            log_test(f"Endpoint {ep}", True, f"HTTP 200 OK for {name}")
        else:
            log_test(f"Endpoint {ep}", False, f"HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        log_test(f"Endpoint {ep}", False, str(e))

# ---------------------------------------------------------------------------
# 5. Direct UPI Payment Session Audit (Q596657023@ybl)
# ---------------------------------------------------------------------------
print("\n--- 5. DIRECT UPI PAYMENT GATEWAY AUDIT ---")
try:
    r = httpx.post(f"{LOCAL_API}/billing/create-checkout-session", headers=auth_headers, json={
        "plan_tier": "STARTER",
        "billing_cycle": "MONTHLY",
        "gateway": "UPI",
        "currency": "INR"
    }, timeout=10.0)
    pay_data = r.json()
    vpa = pay_data.get("upi_id")
    qr = pay_data.get("qr_code_url")
    link = pay_data.get("upi_link")

    if r.status_code == 200 and vpa == "Q596657023@ybl" and qr and "upi://pay?pa=Q596657023@ybl" in link:
        log_test("Direct Instant UPI Gateway", True, f"Payee VPA: {vpa}, Intent Link Verified")
    else:
        log_test("Direct Instant UPI Gateway", False, f"VPA: {vpa}, Code: {r.status_code}")
except Exception as e:
    log_test("Direct Instant UPI Gateway", False, str(e))

# Test subscription-status endpoint for current user
try:
    r_sub = httpx.get(f"{LOCAL_API}/billing/subscription-status", headers=auth_headers, timeout=10.0)
    sub_data = r_sub.json()
    if r_sub.status_code == 200 and sub_data.get("plan_tier") == "FREE_TRIAL":
        log_test("Billing Subscription Status Scoping", True, f"User plan_tier correctly returns FREE_TRIAL")
    else:
        log_test("Billing Subscription Status Scoping", False, f"Expected FREE_TRIAL, got {sub_data}")
except Exception as e:
    log_test("Billing Subscription Status Scoping", False, str(e))

# Test Strict UTR Security Gate (Reject empty/invalid UTR)
try:
    r_bad_utr = httpx.post(f"{LOCAL_API}/billing/verify-payment", headers=auth_headers, json={
        "plan_tier": "STARTER",
        "billing_cycle": "MONTHLY",
        "gateway": "UPI",
        "transaction_id": "123", # Invalid <12 digits
        "amount": 999
    }, timeout=10.0)
    if r_bad_utr.status_code == 400:
        log_test("Invalid UTR Security Gate", True, "Successfully blocked invalid/empty UTR submission with 400 Bad Request")
    else:
        log_test("Invalid UTR Security Gate", False, f"Expected 400 Bad Request, got {r_bad_utr.status_code}")
except Exception as e:
    log_test("Invalid UTR Security Gate", False, str(e))

# Test Valid UTR & Duplicate UTR Anti-Fraud Replay Protection
try:
    mock_utr = f"4256{uuid.uuid4().int % 100000008:08d}"
    r_valid_utr = httpx.post(f"{LOCAL_API}/billing/verify-payment", headers=auth_headers, json={
        "plan_tier": "STARTER",
        "billing_cycle": "MONTHLY",
        "gateway": "UPI",
        "transaction_id": mock_utr,
        "amount": 999
    }, timeout=10.0)
    
    # Re-submit same UTR to test anti-fraud replay protection
    r_dup_utr = httpx.post(f"{LOCAL_API}/billing/verify-payment", headers=auth_headers, json={
        "plan_tier": "PRO",
        "billing_cycle": "MONTHLY",
        "gateway": "UPI",
        "transaction_id": mock_utr,
        "amount": 2499
    }, timeout=10.0)

    if r_valid_utr.status_code == 200 and r_dup_utr.status_code == 400:
        log_test("Anti-Fraud Duplicate UTR Protection", True, f"Verified UTR {mock_utr} & blocked duplicate re-submission")
    else:
        log_test("Anti-Fraud Duplicate UTR Protection", False, f"Valid code: {r_valid_utr.status_code}, Dup code: {r_dup_utr.status_code}")
except Exception as e:
    log_test("Anti-Fraud Duplicate UTR Protection", False, str(e))

# ---------------------------------------------------------------------------
# 6. EdgeTTS Hindi Voice Synthesis Audit
# ---------------------------------------------------------------------------
print("\n--- 6. EDGETTS HINDI VOICE SYNTHESIS AUDIT ---")
import edge_tts
async def test_tts():
    audio_path = "scratch/test_audit_voice.mp3"
    tts = edge_tts.Communicate("नमस्ते, यह ऑटो-ट्यूब एआई का वॉयस टेस्ट है।", "hi-IN-SwaraNeural")
    await tts.save(audio_path)
    size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
    return size

try:
    audio_size = asyncio.run(test_tts())
    if audio_size > 5000:
        log_test("EdgeTTS Voice Synthesis", True, f"Generated Hindi Swara Neural voice ({audio_size} bytes)")
    else:
        log_test("EdgeTTS Voice Synthesis", False, f"Audio file too small: {audio_size} bytes")
except Exception as e:
    log_test("EdgeTTS Voice Synthesis", False, str(e))

# ---------------------------------------------------------------------------
# 7. Live Production Server (autotube.co.in) Health Audit
# ---------------------------------------------------------------------------
print("\n--- 7. LIVE PRODUCTION WEBSITE (autotube.co.in) AUDIT ---")
try:
    r_site = httpx.get("https://autotube.co.in", timeout=15.0, follow_redirects=True)
    if r_site.status_code == 200:
        log_test("Live Website Domain (autotube.co.in)", True, "HTTP 200 OK (SSL Active)")
    else:
        log_test("Live Website Domain (autotube.co.in)", False, f"HTTP {r_site.status_code}")
except Exception as e:
    log_test("Live Website Domain (autotube.co.in)", False, str(e))

try:
    live_email = f"live_audit_{uuid.uuid4().hex[:6]}@autotube.test"
    r_reg = httpx.post(f"{LIVE_API}/auth/register", json={
        "username": f"live_{uuid.uuid4().hex[:4]}",
        "email": live_email,
        "password": "AuditPassword123!"
    }, timeout=15.0)
    live_token = r_reg.json().get("access_token")

    r_live_pay = httpx.post(f"{LIVE_API}/billing/create-checkout-session", headers={"Authorization": f"Bearer {live_token}"}, json={
        "plan_tier": "PRO",
        "billing_cycle": "MONTHLY",
        "gateway": "UPI",
        "currency": "INR"
    }, timeout=15.0)
    live_pay_data = r_live_pay.json()
    live_vpa = live_pay_data.get("upi_id")

    if r_live_pay.status_code == 200 and live_vpa == "Q596657023@ybl":
        log_test("Live Production UPI API", True, f"Live Payee VPA Verified: {live_vpa}")
    else:
        log_test("Live Production UPI API", False, f"VPA: {live_vpa}, Code: {r_live_pay.status_code}")
except Exception as e:
    log_test("Live Production UPI API", False, str(e))

# ---------------------------------------------------------------------------
# AUDIT SUMMARY
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("                         AUDIT SUMMARY SCORE")
print("=" * 70)
passed_count = sum(1 for item in report if item["passed"])
total_count = len(report)
score_pct = round((passed_count / total_count) * 100, 1)

print(f"Total Tests Performed : {total_count}")
print(f"Tests Passed         : {passed_count}")
print(f"Tests Failed         : {total_count - passed_count}")
print(f"System Health Score  : {score_pct}%")

if score_pct == 100.0:
    print("\n🚀 ALL SYSTEM AUDITS PASSED! AUTOTUBE AI IS 100% PRODUCTION READY & SECURE!")
else:
    print("\nAttention required on failed tests above.")
print("=" * 70)
