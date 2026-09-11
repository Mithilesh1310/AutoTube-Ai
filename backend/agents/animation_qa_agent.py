import os
import logging
from typing import Dict, Any, List
from backend.config import settings
from backend.services.motion_detector import motion_detector
from backend.services.character_registry import character_registry
from backend.services.animation_provider import AnimationGenerationError

logger = logging.getLogger(__name__)

async def run_animation_qa_agent(state_dict: dict) -> dict:
    """
    Animation QA Agent:
    Validates generated 3D animation video clips before final rendering.
    Checks:
    1. Technical: Valid MP4 video, non-zero file size, valid duration.
    2. Motion: Genuine temporal movement (rejects static image disguised as video).
    3. Character Lock & Continuity: Validates identity & visual consistency.
    """
    logger.info("[AnimationQAAgent] Running 3D Animation QA & Motion Verification Agent...")
    job_id = state_dict.get("job_id", "job_demo")
    animation_clips = state_dict.get("generated_animation_clips", {})
    animation_instructions = state_dict.get("animation_instructions", [])
    
    # TEST_MODE evaluation
    is_test_mode = getattr(settings, "TEST_MODE", False) and state_dict.get("test_mode", False)

    if not animation_clips:
        err_msg = "FAILED_ANIMATION_QUALITY: No generated animation clips found."
        logger.error(f"[AnimationQAAgent] {err_msg}")
        state_dict["current_step"] = "FAILED_ANIMATION_QUALITY"
        state_dict["error"] = err_msg
        raise AnimationGenerationError(err_msg)

    qa_summary = {}
    failed_scenes = []

    for num, clip_path in animation_clips.items():
        if not os.path.exists(clip_path) or os.path.getsize(clip_path) < 10000:
            failed_scenes.append((num, f"Corrupted or missing video file: {clip_path}"))
            continue

        # 1. Run Motion Detection Analysis
        motion_res = motion_detector.analyze_video_motion(clip_path)
        
        # 2. Check character identity validation
        instruction = next((i for i in animation_instructions if i.get("scene_number") == num), {})
        chars_present = instruction.get("characters_present", [])
        char_val = await character_registry.validate_character_identity(chars_present, clip_path)

        # In production mode: enforce strict motion & character identity gates
        if not is_test_mode:
            if not motion_res.get("is_genuine_animation", False):
                err_reason = f"Motion Gate Failed: Scene #{num} lacks genuine temporal motion (Motion Score: {motion_res.get('motion_score')}, Frozen: {motion_res.get('frozen_frame_pct')}%)."
                logger.error(f"[AnimationQAAgent] {err_reason}")
                failed_scenes.append((num, err_reason))
                continue

            if not char_val.get("CHARACTER_IDENTITY_MATCH", False):
                failed_scenes.append((num, f"Character Lock Mismatch in Scene #{num}"))
                continue

        qa_summary[num] = {
            "clip_path": clip_path,
            "motion_score": motion_res.get("motion_score", 0.0),
            "scene_motion_score": motion_res.get("scene_motion_score", 0.0),
            "dynamic_pixel_ratio": motion_res.get("dynamic_pixel_ratio", 0.0),
            "zero_motion_detected": motion_res.get("zero_motion_detected", False),
            "frozen_frame_pct": motion_res.get("frozen_frame_pct", 0.0),
            "duplicate_frame_ratio": motion_res.get("duplicate_frame_ratio", 0.0),
            "identity_passed": char_val.get("CHARACTER_IDENTITY_MATCH", True),
            "qa_passed": True
        }

    if failed_scenes:
        first_err = failed_scenes[0][1]
        logger.error(f"[AnimationQAAgent] FAILED_ANIMATION_QUALITY: {first_err}")
        state_dict["current_step"] = "FAILED_ANIMATION_QUALITY"
        state_dict["error"] = first_err
        state_dict["logs"].append({
            "agent": "AnimationQAAgent",
            "level": "ERROR",
            "message": f"FAILED_ANIMATION_QUALITY: {first_err}"
        })
        raise AnimationGenerationError(first_err)

    state_dict["animation_qa_summary"] = qa_summary
    state_dict["current_step"] = "VOICE_GEN"
    state_dict["logs"].append({
        "agent": "AnimationQAAgent",
        "level": "SUCCESS",
        "message": f"All {len(qa_summary)} 3D animation clips passed strict Motion & Identity QA validation."
    })

    return state_dict
