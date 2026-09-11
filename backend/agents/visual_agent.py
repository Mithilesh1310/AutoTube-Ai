import os
import asyncio
import logging
from PIL import Image
from backend.config import settings
from backend.services.visual_provider import visual_provider, ImageGenerationError

logger = logging.getLogger(__name__)

async def run_visual_agent(state_dict: dict) -> dict:
    logger.info("[VisualAgent] Running Visual Generation Agent...")
    job_id = state_dict.get("job_id", "job_demo")
    scenes = state_dict.get("scenes", [])
    video_type = state_dict.get("video_type", "LONG")
    is_vertical = (video_type == "SHORT")
    
    # Global TEST_MODE takes precedence: if settings.TEST_MODE is False, it is NEVER test mode
    is_test_mode = getattr(settings, "TEST_MODE", False) and state_dict.get("test_mode", False)

    base_dir = f"./storage/renders/{job_id}/images"
    os.makedirs(base_dir, exist_ok=True)

    has_placeholder = False
    has_fallback = False

    async def generate_single_scene(scene):
        scene_num = scene.scene_number
        prompt = scene.visual_prompt
        image_path = os.path.join(base_dir, f"scene_{scene_num}.png")

        res_obj = await visual_provider.generate_scene_visual(
            prompt=prompt,
            output_path=image_path,
            is_vertical=is_vertical,
            allow_placeholder=is_test_mode
        )
        return scene_num, res_obj

    generated_images = {}
    scene_assets = {}

    try:
        for idx, s in enumerate(scenes):
            num, res_obj = await generate_single_scene(s)
            generated_images[num] = res_obj.image_path
            scene_assets[num] = {
                "image_path": res_obj.image_path,
                "provider_name": res_obj.provider_name,
                "provider_type": res_obj.provider_type,
                "is_fallback": res_obj.is_fallback,
                "is_placeholder": res_obj.is_placeholder,
                "file_size": os.path.getsize(res_obj.image_path) if os.path.exists(res_obj.image_path) else 0
            }
            if res_obj.is_placeholder:
                has_placeholder = True
            if res_obj.is_fallback:
                has_fallback = True

            # Polite delay between sequential requests
            if idx < len(scenes) - 1:
                await asyncio.sleep(1.2)

        # STRICT PRODUCTION IMAGE GATE VALIDATION
        for num, asset in scene_assets.items():
            img_path = asset["image_path"]
            if not os.path.exists(img_path):
                raise ImageGenerationError(f"Missing scene image file for scene {num}: {img_path}")
            
            # Check PIL decode
            try:
                with Image.open(img_path) as im:
                    im.verify()
                    w, h = im.size
                    if w <= 0 or h <= 0:
                        raise ValueError("Invalid image dimensions")
            except Exception as e:
                raise ImageGenerationError(f"Corrupt scene image file for scene {num}: {e}")

            # Production gate: strictly block placeholders
            if not is_test_mode:
                if asset["is_placeholder"] is True:
                    raise ImageGenerationError(f"Production Gate Block: Scene {num} used placeholder! Halting pipeline.")
                if asset["provider_type"] != "ai":
                    raise ImageGenerationError(f"Production Gate Block: Scene {num} provider_type is '{asset['provider_type']}', expected 'ai'. Halting pipeline.")

        state_dict["generated_images"] = generated_images
        state_dict["scene_assets"] = scene_assets
        state_dict["has_placeholder_images"] = has_placeholder
        state_dict["has_fallback_images"] = has_fallback
        state_dict["current_step"] = "VIDEO_EDITOR"
        state_dict["logs"].append({
            "agent": "VisualAgent",
            "level": "SUCCESS",
            "message": f"Generated {len(generated_images)} scene images (Provider: {scene_assets.get(1, {}).get('provider_name')}, Placeholder: {has_placeholder})."
        })
        return state_dict

    except Exception as e:
        logger.error(f"[VisualAgent] Image Generation Failed: {e}")
        state_dict["current_step"] = "FAILED_IMAGE_GENERATION"
        state_dict["error"] = str(e)
        state_dict["logs"].append({
            "agent": "VisualAgent",
            "level": "ERROR",
            "message": f"FAILED_IMAGE_GENERATION: {e}"
        })
        raise ImageGenerationError(str(e))
