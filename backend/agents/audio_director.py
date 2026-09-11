import os
import logging
from typing import Dict, Any, List
from backend.config import settings

logger = logging.getLogger(__name__)

async def run_audio_director_agent(state_dict: dict) -> dict:
    """
    Audio Director Agent:
    Analyzes scene narrative cues to automatically pair sound effects (SFX) and background music (BGM)
    tracks with character dialogue, applying audio ducking and volume balancing.
    """
    logger.info("[AudioDirectorAgent] Analyzing narrative cues for BGM and SFX audio track mixing...")
    job_id = state_dict.get("job_id", "job_demo")
    scenes = state_dict.get("scenes", [])
    
    output_dir = f"./storage/renders/{job_id}/audio"
    os.makedirs(output_dir, exist_ok=True)

    sfx_map = {}
    bgm_mood = "Happy Playful Kids Cartoon"

    for idx, s in enumerate(scenes, 1):
        scene_dict = s.model_dump() if hasattr(s, "model_dump") else s
        stype = scene_dict.get("scene_type", "DIALOGUE")
        ref_action = scene_dict.get("character_actions", "").lower()
        
        # Classify SFX requirements
        if "run" in ref_action or "chase" in ref_action:
            sfx_type = "footsteps_fast"
        elif "fly" in ref_action or "jump" in ref_action:
            sfx_type = "whoosh_wind"
        elif "fall" in ref_action or "hit" in ref_action:
            sfx_type = "cartoon_impact"
        elif "funny" in ref_action or "laugh" in ref_action:
            sfx_type = "cartoon_boing"
        elif "scared" in ref_action or "mystery" in ref_action:
            sfx_type = "suspense_drone"
        else:
            sfx_type = "forest_ambient_birds"

        sfx_map[idx] = {
            "sfx_type": sfx_type,
            "volume_level": 0.6, # 60%
            "audio_ducking": True
        }

    # Set background music track mood
    bgm_track_path = os.path.join(output_dir, "bgm_playful_cartoon.mp3")
    
    state_dict["sfx_map"] = sfx_map
    state_dict["bgm_mood"] = bgm_mood
    state_dict["bgm_path"] = bgm_track_path if os.path.exists(bgm_track_path) else None
    
    state_dict["logs"].append({
        "agent": "AudioDirectorAgent",
        "level": "SUCCESS",
        "message": f"Created SFX and BGM mixing profile for {len(scenes)} scenes (BGM: {bgm_mood})."
    })
    return state_dict
