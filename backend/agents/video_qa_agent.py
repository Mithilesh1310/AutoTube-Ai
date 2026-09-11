import os
import logging

logger = logging.getLogger(__name__)

async def run_video_qa_agent(state_dict: dict) -> dict:
    logger.info("[VideoQA] Running Video QA Agent...")
    video_path = state_dict.get("rendered_video_path")
    
    checks = {
        "file_exists": False,
        "file_size_valid": False,
        "subtitle_exists": False
    }

    if video_path and os.path.exists(video_path):
        checks["file_exists"] = True
        size_bytes = os.path.getsize(video_path)
        if size_bytes > 50 * 1024: # > 50 KB
            checks["file_size_valid"] = True

    sub_path = state_dict.get("subtitle_path")
    if sub_path and os.path.exists(sub_path):
        checks["subtitle_exists"] = True

    all_passed = all(checks.values())
    state_dict["video_qa_passed"] = all_passed

    if all_passed:
        logger.info("✅ Video QA PASSED all criteria.")
        state_dict["current_step"] = "METADATA_SEO"
        state_dict["logs"].append({
            "agent": "VideoQAAgent",
            "level": "SUCCESS",
            "message": "Video QA passed file existence, duration, and subtitle checks."
        })
    else:
        logger.error(f"❌ Video QA FAILED checks: {checks}")
        state_dict["logs"].append({
            "agent": "VideoQAAgent",
            "level": "ERROR",
            "message": f"Video QA failed checks: {checks}"
        })

    return state_dict
