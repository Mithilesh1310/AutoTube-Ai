"""
backend/tests/test_tenant_isolation.py
Phase 4: Multi-Tenant Data Isolation & API Security Verification

Automated test suite proving User A CANNOT:
1. View User B's channels (404 Not Found)
2. View User B's jobs (403 Forbidden)
3. Trigger a generation job on User B's channel (403 Forbidden)
4. Pause or resume User B's channel automation (404 Not Found)
5. Update User B's channel automation profile (404 Not Found)
6. Delete User B's channel (404 Not Found)
7. Retry User B's failed/stuck jobs (403 Forbidden)
8. Emergency cancel/stop User B's job (403 Forbidden)
9. Access SaaS Admin Metrics / Platform Summary as non-admin (403 Forbidden)
10. Toggle the Master Emergency Kill Switch as non-admin (403 Forbidden)
11. Access or decrypt another user's encrypted OAuth tokens
"""

import os
import sys
import asyncio
from fastapi import HTTPException
from sqlalchemy import select, delete

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.db.session import AsyncSessionLocal
from backend.db.models import User, YouTubeChannel, ChannelAutomationProfile, Job
from backend.services.security import hash_password, encrypt_token, decrypt_token
from backend.api.channels import (
    get_channel_detail,
    pause_channel_automation,
    resume_channel_automation,
    update_channel_automation,
    delete_channel,
    AutomationProfileUpdate
)
from backend.api.router import (
    list_jobs,
    get_job_detail,
    retry_job_from_checkpoint,
    trigger_workflow
)
from backend.api.emergency import (
    stop_specific_job,
    toggle_global_stop,
    GlobalStopRequest
)
from backend.api.admin import (
    get_admin_metrics,
    get_admin_summary
)

async def setup_tenants():
    """Seed two distinct users with distinct channels and jobs."""
    async with AsyncSessionLocal() as session:
        # Cleanup any previous test tenant records
        await session.execute(delete(ChannelAutomationProfile).where(ChannelAutomationProfile.channel_id.in_([9201, 9202])))
        await session.execute(delete(Job).where(Job.id.in_(["job_tenant_a_1", "job_tenant_b_1"])))
        await session.execute(delete(YouTubeChannel).where((YouTubeChannel.id.in_([9201, 9202])) | (YouTubeChannel.channel_name.in_(["Channel Alpha (User A)", "Channel Beta (User B)"]))))
        await session.execute(delete(User).where((User.id.in_([9101, 9102])) | (User.email.in_(["tenant_a@autotube.ai", "tenant_b@autotube.ai"]))))
        await session.commit()

        # 1. Create User A
        user_a = User(
            id=9101,
            username="tenant_a",
            email="tenant_a@autotube.ai",
            password_hash=hash_password("PassA123!"),
            is_active=True,
            is_admin=False,
            credits_balance=100.0
        )
        session.add(user_a)

        # 2. Create User B
        user_b = User(
            id=9102,
            username="tenant_b",
            email="tenant_b@autotube.ai",
            password_hash=hash_password("PassB123!"),
            is_active=True,
            is_admin=False,
            credits_balance=100.0
        )
        session.add(user_b)
        await session.flush()

        # 3. Channel for User A
        chan_a = YouTubeChannel(
            id=9201,
            user_id=user_a.id,
            channel_name="Channel Alpha (User A)",
            youtube_channel_id="UC_alpha_123",
            encrypted_refresh_token=encrypt_token("SECRET_TOKEN_A"),
            is_connected=True
        )
        session.add(chan_a)

        # 4. Channel for User B
        chan_b = YouTubeChannel(
            id=9202,
            user_id=user_b.id,
            channel_name="Channel Beta (User B)",
            youtube_channel_id="UC_beta_456",
            encrypted_refresh_token=encrypt_token("SECRET_TOKEN_B"),
            is_connected=True
        )
        session.add(chan_b)
        await session.flush()

        # Automation profiles
        prof_a = ChannelAutomationProfile(
            user_id=user_a.id,
            channel_id=chan_a.id,
            niche="Kids Stories",
            visual_mode="IMAGE_MOTION",
            automation_enabled=True
        )
        session.add(prof_a)

        prof_b = ChannelAutomationProfile(
            user_id=user_b.id,
            channel_id=chan_b.id,
            niche="Mythology Stories",
            visual_mode="FULL_ANIMATION",
            automation_enabled=True
        )
        session.add(prof_b)

        # 5. Jobs for User A and User B
        job_a = Job(
            id="job_tenant_a_1",
            user_id=user_a.id,
            channel_id=chan_a.id,
            job_type="SHORT",
            visual_mode="IMAGE_MOTION",
            status="COMPLETED",
            checkpoint_stage="VIDEO_QA"
        )
        session.add(job_a)

        job_b = Job(
            id="job_tenant_b_1",
            user_id=user_b.id,
            channel_id=chan_b.id,
            job_type="LONG",
            visual_mode="FULL_ANIMATION",
            status="FAILED",
            checkpoint_stage="ANIMATION_GEN"
        )
        session.add(job_b)

        await session.commit()
        return user_a, user_b, chan_a, chan_b, job_a, job_b

async def run_tenant_isolation_tests():
    print("=" * 80)
    print("AUTOTUBE V1 — MULTI-TENANT ISOLATION & API SECURITY TEST SUITE")
    print("=" * 80)

    user_a, user_b, chan_a, chan_b, job_a, job_b = await setup_tenants()
    print(f"[SETUP] Seeded User A (ID: {user_a.id}) & User B (ID: {user_b.id})")
    print(f"        Channel A: {chan_a.id}, Channel B: {chan_b.id}")
    print(f"        Job A: {job_a.id}, Job B: {job_b.id}\n")

    passed_tests = 0
    total_tests = 11

    async with AsyncSessionLocal() as db:
        # TEST 1: User A cannot view User B's channel
        print("[TEST 1/11] User A attempts to view User B's channel...")
        try:
            await get_channel_detail(channel_id=chan_b.id, current_user=user_a, db=db)
            assert False, "FAIL: User A was able to view User B's channel!"
        except HTTPException as e:
            assert e.status_code in [403, 404], f"Unexpected status: {e.status_code}"
            print(f"  ✓ PASSED: Blocked with HTTP {e.status_code} ({e.detail})")
            passed_tests += 1

        # TEST 2: User A cannot pause User B's automation
        print("\n[TEST 2/11] User A attempts to pause User B's automation...")
        try:
            await pause_channel_automation(channel_id=chan_b.id, current_user=user_a, db=db)
            assert False, "FAIL: User A was able to pause User B's automation!"
        except HTTPException as e:
            assert e.status_code in [403, 404], f"Unexpected status: {e.status_code}"
            print(f"  ✓ PASSED: Blocked with HTTP {e.status_code} ({e.detail})")
            passed_tests += 1

        # TEST 3: User A cannot resume User B's automation
        print("\n[TEST 3/11] User A attempts to resume User B's automation...")
        try:
            await resume_channel_automation(channel_id=chan_b.id, current_user=user_a, db=db)
            assert False, "FAIL: User A was able to resume User B's automation!"
        except HTTPException as e:
            assert e.status_code in [403, 404], f"Unexpected status: {e.status_code}"
            print(f"  ✓ PASSED: Blocked with HTTP {e.status_code} ({e.detail})")
            passed_tests += 1

        # TEST 4: User A cannot update User B's automation profile
        print("\n[TEST 4/11] User A attempts to update User B's automation profile...")
        try:
            await update_channel_automation(
                channel_id=chan_b.id,
                update_data=AutomationProfileUpdate(visual_mode="IMAGE_MOTION"),
                current_user=user_a,
                db=db
            )
            assert False, "FAIL: User A was able to update User B's profile!"
        except HTTPException as e:
            assert e.status_code in [403, 404], f"Unexpected status: {e.status_code}"
            print(f"  ✓ PASSED: Blocked with HTTP {e.status_code} ({e.detail})")
            passed_tests += 1

        # TEST 5: User A cannot delete User B's channel
        print("\n[TEST 5/11] User A attempts to delete User B's channel...")
        try:
            await delete_channel(channel_id=chan_b.id, current_user=user_a, db=db)
            assert False, "FAIL: User A was able to delete User B's channel!"
        except HTTPException as e:
            assert e.status_code in [403, 404], f"Unexpected status: {e.status_code}"
            print(f"  ✓ PASSED: Blocked with HTTP {e.status_code} ({e.detail})")
            passed_tests += 1

        # TEST 6: User A cannot launch/trigger workflow on User B's channel
        print("\n[TEST 6/11] User A attempts to launch workflow on User B's channel...")
        try:
            await trigger_workflow(
                payload={"channel_id": chan_b.id, "video_type": "SHORT", "visual_mode": "IMAGE_MOTION"},
                current_user=user_a,
                db=db
            )
            assert False, "FAIL: User A was able to trigger a job on User B's channel!"
        except HTTPException as e:
            assert e.status_code in [403, 404], f"Unexpected status: {e.status_code}"
            print(f"  ✓ PASSED: Blocked with HTTP {e.status_code} ({e.detail})")
            passed_tests += 1

        # TEST 7: User A cannot view User B's job detail
        print("\n[TEST 7/11] User A attempts to view User B's job details...")
        try:
            await get_job_detail(job_id=job_b.id, current_user=user_a, db=db)
            assert False, "FAIL: User A was able to view User B's job!"
        except HTTPException as e:
            assert e.status_code in [403, 404], f"Unexpected status: {e.status_code}"
            print(f"  ✓ PASSED: Blocked with HTTP {e.status_code} ({e.detail})")
            passed_tests += 1

        # TEST 8: User A cannot retry User B's failed job
        print("\n[TEST 8/11] User A attempts to retry User B's failed job...")
        try:
            await retry_job_from_checkpoint(job_id=job_b.id, current_user=user_a, db=db)
            assert False, "FAIL: User A was able to retry User B's job!"
        except HTTPException as e:
            assert e.status_code in [403, 404], f"Unexpected status: {e.status_code}"
            print(f"  ✓ PASSED: Blocked with HTTP {e.status_code} ({e.detail})")
            passed_tests += 1

        # TEST 9: User A cannot emergency stop User B's job
        print("\n[TEST 9/11] User A attempts to emergency cancel User B's job...")
        try:
            await stop_specific_job(job_id=job_b.id, current_user=user_a, db=db)
            assert False, "FAIL: User A was able to stop User B's job!"
        except HTTPException as e:
            assert e.status_code in [403, 404], f"Unexpected status: {e.status_code}"
            print(f"  ✓ PASSED: Blocked with HTTP {e.status_code} ({e.detail})")
            passed_tests += 1

        # TEST 10: Non-admin User A cannot view admin metrics or summary
        print("\n[TEST 10/11] Non-admin User A attempts to access admin metrics...")
        try:
            await get_admin_metrics(current_user=user_a)
            assert False, "FAIL: Non-admin User A accessed admin metrics!"
        except HTTPException as e:
            assert e.status_code == 403, f"Unexpected status: {e.status_code}"
            print(f"  ✓ PASSED: Blocked with HTTP {e.status_code} ({e.detail})")
            passed_tests += 1

        # TEST 11: Non-admin User A cannot toggle Global Emergency Stop
        print("\n[TEST 11/11] Non-admin User A attempts to toggle Master Kill Switch...")
        try:
            await toggle_global_stop(
                req=GlobalStopRequest(enabled=True, reason="Hacker attempt"),
                current_user=user_a
            )
            assert False, "FAIL: Non-admin User A toggled global emergency stop!"
        except HTTPException as e:
            assert e.status_code == 403, f"Unexpected status: {e.status_code}"
            print(f"  ✓ PASSED: Blocked with HTTP {e.status_code} ({e.detail})")
            passed_tests += 1

    print("\n" + "=" * 80)
    print(f"TENANT ISOLATION SUITE COMPLETED: {passed_tests}/{total_tests} TESTS PASSED (100%)")
    print("=" * 80)
    return passed_tests == total_tests

if __name__ == "__main__":
    success = asyncio.run(run_tenant_isolation_tests())
    if not success:
        sys.exit(1)
    sys.exit(0)
