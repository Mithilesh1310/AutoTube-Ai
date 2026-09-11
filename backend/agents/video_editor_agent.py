import os
import logging
from backend.config import settings
from backend.services.video_editor import video_editor_service
from backend.services.visual_provider import ImageGenerationError

logger = logging.getLogger(__name__)

async def run_video_editor_agent(state_dict: dict) -> dict:
    logger.info("[VideoEditor] Running Video Editor Agent...")
    job_id = state_dict.get("job_id", "job_demo")
    scenes = [s.model_dump() if hasattr(s, "model_dump") else s for s in state_dict.get("scenes", [])]
    images_dict = state_dict.get("generated_images", {})
    audios_dict = state_dict.get("generated_audios", {})
    animation_clips_dict = state_dict.get("generated_animation_clips", {})
    video_type = state_dict.get("video_type", "LONG")
    visual_mode = state_dict.get("visual_mode", "IMAGE_MOTION")
    is_vertical = (video_type == "SHORT")

    is_test_mode = getattr(settings, "TEST_MODE", False) and state_dict.get("test_mode", False)
    scene_assets = state_dict.get("scene_assets", {})

    # STRICT PRE-RENDERING PRODUCTION GATE FOR IMAGE_MOTION MODE
    if visual_mode == "IMAGE_MOTION" and not is_test_mode:
        for num, asset in scene_assets.items():
            img_path = asset.get("image_path")
            if not img_path or not os.path.exists(img_path):
                raise ImageGenerationError(f"Pre-Render Gate Block: Missing image file for scene {num}: {img_path}")
            if asset.get("is_placeholder") is True:
                raise ImageGenerationError(f"Pre-Render Gate Block: Scene {num} is a placeholder image! Rendering blocked.")
            if asset.get("provider_type") != "ai":
                raise ImageGenerationError(f"Pre-Render Gate Block: Scene {num} provider_type is '{asset.get('provider_type')}', expected 'ai'. Rendering blocked.")

    output_dir = f"./storage/renders/{job_id}"
    output_video_path = os.path.join(output_dir, f"final_{video_type.lower()}.mp4")
    srt_subtitle_path = os.path.join(output_dir, "subtitles_hi.srt")

    try:
        # Generate SRT Subtitles
        video_editor_service.generate_srt_subtitles(scenes, srt_subtitle_path)
        state_dict["subtitle_path"] = srt_subtitle_path

        # Assemble MP4
        res_video = await video_editor_service.assemble_video(
            job_id=job_id,
            scenes=scenes,
            images_dict=images_dict,
            audios_dict=audios_dict,
            output_video_path=output_video_path,
            is_vertical=is_vertical,
            animation_clips_dict=animation_clips_dict
        )
        state_dict["rendered_video_path"] = res_video
        state_dict["current_step"] = "VIDEO_QA"
        state_dict["logs"].append({
            "agent": "VideoEditorAgent",
            "level": "SUCCESS",
            "message": f"Successfully rendered {video_type} ({visual_mode}) video MP4."
        })
    except Exception as e:
        logger.error(f"Video Editor failed: {e}")
        state_dict["error"] = str(e)
        state_dict["logs"].append({
            "agent": "VideoEditorAgent",
            "level": "ERROR",
            "message": f"Video Editor Error: {e}"
        })
        raise e

    return state_dict
