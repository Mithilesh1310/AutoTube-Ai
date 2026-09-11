import os
import logging
from PIL import Image
from backend.config import settings
from backend.services.visual_provider import visual_provider, ImageGenerationError

logger = logging.getLogger(__name__)

async def run_thumbnail_agent(state_dict: dict) -> dict:
    logger.info("[ThumbnailAgent] Running Thumbnail Agent...")
    job_id = state_dict.get("job_id", "job_demo")
    title = state_dict.get("title", "Hindi Kids Story")
    
    is_test_mode = getattr(settings, "TEST_MODE", False) and state_dict.get("test_mode", False)
    
    output_dir = f"./storage/renders/{job_id}"
    os.makedirs(output_dir, exist_ok=True)
    thumbnail_path = os.path.join(output_dir, "thumbnail.png")

    # Award-winning 3D Disney Pixar YouTube thumbnail poster with iconic characters and 3D typography
    prompt = (
        f"Award winning 3D Disney Pixar kids cartoon YouTube thumbnail poster for animated story titled '{title}'. "
        f"Prominently centered cheerful cute boy Chintu with warm smile and sparkling eyes, "
        f"holding a glowing magical item, with his cute adorable baby blue elephant and cheerful animal friends. "
        f"Bold stylized 3D Hindi cartoon typography title text banner at top. "
        f"Lush colorful whimsical enchanted forest, bright sunny golden daylight, sparkling particles, "
        f"vibrant saturated pastel colors, ultra-detailed 8k, Octane Render, Disney Pixar studio CGI quality, "
        f"crisp clean sharp focus, cinematic studio lighting, masterpiece."
    )

    try:
        res_obj = await visual_provider.generate_scene_visual(
            prompt=prompt,
            output_path=thumbnail_path,
            is_vertical=False,
            allow_placeholder=is_test_mode
        )

        # STRICT PRODUCTION THUMBNAIL VALIDATION
        if not is_test_mode:
            if res_obj.is_placeholder is True:
                raise ImageGenerationError("Production Gate Block: Thumbnail was generated as placeholder! Halting upload.")
            if res_obj.provider_type != "ai":
                raise ImageGenerationError(f"Production Gate Block: Thumbnail provider_type is '{res_obj.provider_type}', expected 'ai'. Halting upload.")

        # Validate with PIL
        with Image.open(thumbnail_path) as im:
            im.verify()

        state_dict["thumbnail_path"] = res_obj.image_path
        state_dict["thumbnail_is_placeholder"] = res_obj.is_placeholder
        state_dict["thumbnail_provider"] = res_obj.provider_name
        state_dict["thumbnail_provider_type"] = res_obj.provider_type
        state_dict["current_step"] = "YOUTUBE_UPLOAD"
        state_dict["logs"].append({
            "agent": "ThumbnailAgent",
            "level": "SUCCESS",
            "message": f"Generated thumbnail (Provider: {res_obj.provider_name}, Placeholder: {res_obj.is_placeholder})."
        })
        return state_dict

    except Exception as e:
        logger.error(f"[ThumbnailAgent] Error generating thumbnail: {e}")
        if not is_test_mode:
            state_dict["current_step"] = "FAILED_IMAGE_GENERATION"
            state_dict["error"] = str(e)
            raise ImageGenerationError(f"Production Thumbnail Generation Failed: {e}")
        
        # Test mode fallback only
        state_dict["thumbnail_path"] = thumbnail_path
        state_dict["thumbnail_is_placeholder"] = True
        state_dict["thumbnail_provider"] = "LocalCanvasImageProvider"
        state_dict["thumbnail_provider_type"] = "placeholder"
        state_dict["current_step"] = "YOUTUBE_UPLOAD"
        return state_dict
