"""
verify_real_image_pipeline.py
Dedicated verification script for real Hugging Face AI image generation pipeline,
secondary Pollinations fallback, and strict production placeholder blocking gates.
"""

import os
import sys
import asyncio
from PIL import Image

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.config import settings
from backend.services.visual_provider import (
    visual_provider,
    HuggingFaceImageProvider,
    PollinationsImageProvider,
    LocalCanvasImageProvider,
    ImageGenerationError
)

# Output directory for test inspection assets
VERIFY_DIR = os.path.abspath("./storage/verification_assets")
os.makedirs(VERIFY_DIR, exist_ok=True)

async def run_verification():
    print("=" * 70)
    print("AUTOTUBE V1 - REAL IMAGE GENERATION PIPELINE VERIFICATION")
    print("=" * 70)

    # 1. Check API Key configuration (without exposing key value)
    has_key = bool(settings.IMAGE_API_KEY and len(settings.IMAGE_API_KEY.strip()) > 5)
    print(f"HUGGING_FACE_API_KEY_CONFIGURED: {'YES' if has_key else 'NO'}")
    if not has_key:
        print("[ERROR] Hugging Face API key is not configured in .env!")
        sys.exit(1)

    # 2. Define 3 realistic story scene prompts and 1 thumbnail prompt
    test_scenes = [
        {
            "id": "scene_1",
            "name": "Scene 1 (Hook)",
            "prompt": "3D Pixar animation style. Cute baby blue elephant Chintu finding a glowing magical seed on a mossy rock in a sunlit cartoon jungle. Vibrant colors, soft volumetric morning light, joyful expression, 8k render.",
            "is_vertical": True,
            "filename": "scene_1_chintu_seed.png"
        },
        {
            "id": "scene_2",
            "name": "Scene 2 (Action)",
            "prompt": "3D Pixar animation style. Playful brown monkey Momo swinging dynamically from a blooming vine holding a golden fruit, smiling happily. Sunny cartoon canopy, fluttering butterflies, cinematic angle, 8k render.",
            "is_vertical": True,
            "filename": "scene_2_momo_swing.png"
        },
        {
            "id": "scene_3",
            "name": "Scene 3 (Discovery)",
            "prompt": "3D Pixar animation style. Smart white rabbit Titu with tiny spectacles unrolling an ancient treasure map beside Chintu elephant under a giant mushroom. Soft golden hour lighting, expressive curious eyes, 8k render.",
            "is_vertical": True,
            "filename": "scene_3_titu_map.png"
        }
    ]

    thumbnail_spec = {
        "id": "thumbnail_main",
        "name": "YouTube Thumbnail",
        "prompt": "High CTR 3D Disney Pixar YouTube thumbnail for kids cartoon story titled 'Chintu Aur Jadui Beej'. Big cute expressive faces of baby elephant Chintu and monkey Momo, bright rainbow forest, cinematic studio lighting, 8k.",
        "is_vertical": False,
        "filename": "thumbnail_kids_story.png"
    }

    generated_assets = []
    primary_provider_used = None
    secondary_provider_used = None
    placeholder_count = 0

    print("\n>>> Phase 1: Generating 3 Story Scene Assets via AI Pipeline...")
    for scene in test_scenes:
        output_path = os.path.join(VERIFY_DIR, scene["filename"])
        print(f"\n[Generating {scene['name']}]")
        print(f"Prompt: {scene['prompt'][:85]}...")
        
        try:
            res = await visual_provider.generate_scene_visual(
                prompt=scene["prompt"],
                output_path=output_path,
                is_vertical=scene["is_vertical"],
                allow_placeholder=False  # Strict production rule: no placeholders
            )

            # Validate generated image
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"File was not created: {output_path}")

            with Image.open(output_path) as im:
                im.verify()
            
            with Image.open(output_path) as im:
                w, h = im.size

            file_size = os.path.getsize(output_path)
            if file_size < 20000:
                raise ValueError(f"File size too small for real AI image ({file_size} bytes)")

            if res.is_placeholder:
                placeholder_count += 1
                raise ValueError("Generated asset is marked as a placeholder!")

            if res.provider_type != "ai":
                raise ValueError(f"Provider type is '{res.provider_type}', expected 'ai'!")

            if res.provider_name == "HuggingFaceImageProvider":
                primary_provider_used = "HuggingFaceImageProvider"
            elif res.provider_name == "PollinationsImageProvider":
                secondary_provider_used = "PollinationsImageProvider"

            print(f"  [OK] SUCCESS: {res.provider_name} | {w}x{h} | {file_size:,} bytes")
            print(f"  [OK] Path: {output_path}")

            generated_assets.append({
                "id": scene["id"],
                "provider": res.provider_name,
                "provider_type": res.provider_type,
                "is_fallback": res.is_fallback,
                "is_placeholder": res.is_placeholder,
                "file_path": output_path,
                "resolution": f"{w}x{h}",
                "size_bytes": file_size,
                "status": "VALID_AI_IMAGE"
            })

            # Polite pause between generations
            await asyncio.sleep(1.0)

        except Exception as e:
            print(f"  [FAIL] FAILED: {e}")
            generated_assets.append({
                "id": scene["id"],
                "provider": "FAILED",
                "provider_type": "none",
                "is_fallback": False,
                "is_placeholder": False,
                "file_path": output_path,
                "resolution": "N/A",
                "size_bytes": 0,
                "status": f"ERROR: {e}"
            })

    print("\n>>> Phase 2: Generating Thumbnail Asset...")
    thumb_path = os.path.join(VERIFY_DIR, thumbnail_spec["filename"])
    try:
        thumb_res = await visual_provider.generate_scene_visual(
            prompt=thumbnail_spec["prompt"],
            output_path=thumb_path,
            is_vertical=False,
            allow_placeholder=False
        )

        with Image.open(thumb_path) as im:
            im.verify()
        with Image.open(thumb_path) as im:
            tw, th = im.size
        
        thumb_size = os.path.getsize(thumb_path)
        if thumb_res.is_placeholder:
            placeholder_count += 1

        print(f"  [OK] SUCCESS: {thumb_res.provider_name} | {tw}x{th} | {thumb_size:,} bytes")
        print(f"  [OK] Path: {thumb_path}")

        generated_assets.append({
            "id": thumbnail_spec["id"],
            "provider": thumb_res.provider_name,
            "provider_type": thumb_res.provider_type,
            "is_fallback": thumb_res.is_fallback,
            "is_placeholder": thumb_res.is_placeholder,
            "file_path": thumb_path,
            "resolution": f"{tw}x{th}",
            "size_bytes": thumb_size,
            "status": "VALID_AI_IMAGE"
        })
    except Exception as e:
        print(f"  [FAIL] FAILED Thumbnail: {e}")
        generated_assets.append({
            "id": thumbnail_spec["id"],
            "provider": "FAILED",
            "provider_type": "none",
            "is_fallback": False,
            "is_placeholder": False,
            "file_path": thumb_path,
            "resolution": "N/A",
            "size_bytes": 0,
            "status": f"ERROR: {e}"
        })

    # Phase 3: Verify Production Image Gate Enforcement
    print("\n>>> Phase 3: Verifying Production Image Gate Enforcement (Placeholders Blocked)...")
    gate_passed = False
    try:
        # Create simulated provider where both AI providers fail
        class FailingTestVisualProvider(visual_provider.__class__):
            pass
        
        dummy_provider = FailingTestVisualProvider()
        async def fail_primary(*a, **kw):
            raise RuntimeError("Simulated HF failure")
        async def fail_secondary(*a, **kw):
            raise RuntimeError("Simulated Pollinations failure")

        dummy_provider.primary_provider.generate_image = fail_primary
        dummy_provider.secondary_provider.generate_image = fail_secondary
        
        # When TEST_MODE=false, this MUST raise ImageGenerationError and NOT fallback to LocalCanvas
        try:
            await dummy_provider.generate_scene_visual(
                prompt="test prompt",
                output_path=os.path.join(VERIFY_DIR, "gate_test.png"),
                allow_placeholder=False
            )
            print("  [FAIL] Gate test failed: Did not raise ImageGenerationError!")
            gate_passed = False
        except ImageGenerationError:
            print("  [OK] Production Gate Verified: ImageGenerationError correctly raised. LocalCanvas blocked when TEST_MODE=false.")
            gate_passed = True
    except Exception as e:
        print(f"  [FAIL] Gate test unexpected error: {e}")
        gate_passed = False

    # 4. Generate Final Unified Report
    print("\n" + "=" * 70)
    print("FINAL UNIFIED VERIFICATION REPORT")
    print("=" * 70)
    
    hf_active = primary_provider_used == "HuggingFaceImageProvider"
    scenes_ok = sum(1 for a in generated_assets if "scene" in a["id"] and a["status"] == "VALID_AI_IMAGE")
    thumb_ok = any(a["id"] == "thumbnail_main" and a["status"] == "VALID_AI_IMAGE" for a in generated_assets)
    all_ok = hf_active and scenes_ok == 3 and thumb_ok and placeholder_count == 0 and gate_passed

    print(f"HUGGING_FACE_API_KEY_CONFIGURED: YES")
    print(f"HUGGING_FACE_LIVE_REQUEST:       {'SUCCESS' if hf_active else 'FAILED'}")
    print(f"PRIMARY_PROVIDER_USED:           {primary_provider_used or 'NONE'}")
    print(f"SECONDARY_PROVIDER_USED:         {secondary_provider_used or 'NONE'}")
    print(f"SCENE_IMAGES_GENERATED:          {scenes_ok}")
    print(f"THUMBNAIL_GENERATED:             {'YES' if thumb_ok else 'NO'}")
    print(f"PLACEHOLDER_IMAGES_DETECTED:     {placeholder_count}")
    print(f"PRODUCTION_IMAGE_GATE:           {'PASSED' if gate_passed else 'FAILED'}")
    print(f"FINAL_STATUS:                    {'LIVE_IMAGE_PIPELINE_VERIFIED' if all_ok else 'VERIFICATION_FAILED'}")
    print("=" * 70)

    print("\nGENERATED ASSET DETAILS (FOR MANUAL VISUAL INSPECTION):")
    print(f"{'Asset ID':<16} | {'Provider':<25} | {'Fallback':<8} | {'Placeholder':<11} | {'Size':<10} | {'Status':<16}")
    print("-" * 95)
    for a in generated_assets:
        print(f"{a['id']:<16} | {a['provider']:<25} | {str(a['is_fallback']):<8} | {str(a['is_placeholder']):<11} | {a['size_bytes']:<10} | {a['status']:<16}")
        print(f"  -> Path: {a['file_path']}")
    print("-" * 95)

if __name__ == "__main__":
    asyncio.run(run_verification())
