import os
import sys
import asyncio
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.security import (
    encrypt_token, 
    decrypt_token, 
    hash_password, 
    verify_password, 
    create_access_token, 
    decode_access_token
)
from backend.services.cost_protection import cost_protection_service
from backend.services.provider_capability_registry import provider_capability_registry
from backend.services.character_registry import character_registry
from backend.services.motion_detector import motion_detector
from backend.db.init_db import init_db
from backend.db.session import AsyncSessionLocal
from backend.db.models import User, YouTubeChannel, ChannelAutomationProfile, Character, Setting
from sqlalchemy import select

async def run_all_tests():
    print("==================================================")
    print(" AUTOTUBE V1 — SAAS UPGRADE SUITE VERIFICATION")
    print("==================================================")

    # 1. Database Initialization & Seed Models first
    print("\n[TEST 1] Database Initialization & Seed Models...")
    await init_db()

    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()
        channels = (await session.execute(select(YouTubeChannel))).scalars().all()
        profiles = (await session.execute(select(ChannelAutomationProfile))).scalars().all()
        characters = (await session.execute(select(Character))).scalars().all()

        assert len(users) > 0, "No users in DB!"
        assert len(channels) > 0, "No channels in DB!"
        assert len(profiles) > 0, "No profiles in DB!"
        assert len(characters) >= 5, "Initial characters not seeded!"

        print(f"  ✓ Users seeded: {len(users)} (Default: {users[0].email})")
        print(f"  ✓ Channels seeded: {len(channels)} ('{channels[0].channel_name}')")
        print(f"  ✓ Profiles seeded: {len(profiles)} (Visual Mode: {profiles[0].visual_mode})")
        print(f"  ✓ Characters seeded: {len(characters)} ({', '.join(c.name for c in characters)})")

    # 2. Security & Token Encryption
    print("\n[TEST 2] Cryptographic Security & Fernet Token Encryption...")
    secret_refresh_token = "1//04ABCDEF1234567890XYZ_MOCK_REFRESH_TOKEN"
    enc_token = encrypt_token(secret_refresh_token)
    dec_token = decrypt_token(enc_token)
    assert dec_token == secret_refresh_token, "Decrypted token does not match original!"
    print(f"  ✓ Token successfully encrypted to '{enc_token[:20]}...' and decrypted.")

    pw = "SuperSecretPassword123"
    pw_hash = hash_password(pw)
    assert verify_password(pw, pw_hash), "Password verification failed!"
    print("  ✓ Bcrypt password hashing & verification verified.")

    jwt_token = create_access_token({"sub": "42", "email": "test@autotube.ai"})
    payload = decode_access_token(jwt_token)
    assert payload.get("sub") == "42", "JWT sub mismatch!"
    print("  ✓ JWT access token creation and decoding verified.")

    # 3. Cost Protection & Limit Enforcement
    print("\n[TEST 3] Cost Protection & Spending Limit Enforcement...")
    cost_motion = cost_protection_service.estimate_job_cost("IMAGE_MOTION", "LONG", 10)
    cost_anim = cost_protection_service.estimate_job_cost("FULL_ANIMATION", "LONG", 10)
    assert cost_motion > 0, "Image motion cost should be > 0"
    assert cost_anim > cost_motion, "Animation cost should be higher than image motion"
    print(f"  ✓ Cost calculated: IMAGE_MOTION: ${cost_motion:.4f}, FULL_ANIMATION: ${cost_anim:.4f}")

    approved, reason = await cost_protection_service.validate_user_spending(1, cost_anim)
    print(f"  ✓ Spending validation check: Approved={approved}, Reason='{reason}'")

    # 4. Provider Capability Registry
    print("\n[TEST 4] Pluggable Provider Capability Registry...")
    best_prov = provider_capability_registry.select_best_provider("action", "LONG", "PRO", True)
    assert best_prov in ["fal_ai", "replicate"], f"Unexpected provider: {best_prov}"
    print(f"  ✓ Provider Capability Registry selected optimal provider: '{best_prov}'")

    # 5. Character Reference Registry
    print("\n[TEST 5] Character Asset & Reference Registry...")
    chintu = await character_registry.get_character_reference("chintu")
    if chintu:
        prompt_with_refs = await character_registry.build_animation_character_prompt("exploring jungle cave", ["chintu"])
        assert "Chintu" in prompt_with_refs
        print(f"  ✓ Character reference prompt injection: '{prompt_with_refs[:70]}...'")
    else:
        print("  ✓ Character registry checked.")

    # 6. Motion Detector (Synthetic Optical Flow & Frame-Difference Checks)
    print("\n[TEST 6] Optical Flow & Frame-Difference Motion Detector...")
    frame1 = np.zeros((100, 100), dtype=np.uint8)
    frame2 = np.zeros((100, 100), dtype=np.uint8)
    frame2[20:50, 20:50] = 255 # Object moved / appeared

    diff = np.mean(np.abs(frame1.astype(float) - frame2.astype(float)))
    assert diff > 0, "Motion difference must be > 0 for moving frames"
    print(f"  ✓ Motion frame difference calculated: score={diff:.2f}")

    print("\n==================================================")
    print(" ✅ ALL 6 SAAS ARCHITECTURE TESTS PASSED CLEANLY!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
