import logging
from typing import Dict, Any, List
from backend.services.character_registry import character_registry
from backend.services.scene_continuity_engine import scene_continuity_engine

logger = logging.getLogger(__name__)

async def run_animation_director_agent(state_dict: dict) -> dict:
    """
    Animation Director Agent:
    Converts script scenes into detailed 3D animation instructions, incorporating character reference
    lock standards and scene continuity vectors.
    """
    logger.info("[AnimationDirectorAgent] Translating story breakdown into structured 3D animation instructions...")
    scenes = state_dict.get("scenes", [])
    video_type = state_dict.get("video_type", "LONG")
    is_vertical = (video_type == "SHORT")
    aspect_ratio = "9:16" if is_vertical else "16:9"

    scene_continuity_engine.reset_for_new_story()
    animation_instructions = []

    for idx, s in enumerate(scenes, 1):
        scene_dict = s.model_dump() if hasattr(s, "model_dump") else s
        speaker = scene_dict.get("speaker", "Narrator")
        chars_present = scene_dict.get("characters_present", [speaker.lower()])
        stype = scene_dict.get("scene_type", "DIALOGUE")
        duration = scene_dict.get("duration_seconds", 6.0)

        # Process continuity vector
        continuity_ctx = scene_continuity_engine.process_scene_continuity(idx, scene_dict)
        motion_vector = continuity_ctx.get("motion_vector")

        # Determine motion intensity & animation style
        if stype == "ACTION":
            motion_intensity = "HIGH_DYNAMIC_MOVEMENT"
            cam_movement = "Fast tracking camera shot following character movement"
            anim_style = "3D Pixar high-action animation"
        elif stype == "DISCOVERY":
            motion_intensity = "MEDIUM_EXPRESSIVE"
            cam_movement = "Slow zoom close-up focusing on magical discovery"
            anim_style = "3D Pixar discovery lighting animation"
        elif stype == "COMEDY":
            motion_intensity = "PLAYFUL_EXAGGERATED"
            cam_movement = "Low angle funny reaction tracking"
            anim_style = "3D cartoon comedy motion"
        else:
            motion_intensity = "MEDIUM_DIALOGUE"
            cam_movement = "Medium establish pan shot"
            anim_style = "3D Pixar story animation"

        # Build character lock prompt
        scene_action_desc = f"{speaker} {motion_vector}. Performing action: {scene_dict.get('character_actions', 'speaking')}"
        anim_prompt = await character_registry.build_animation_character_prompt(
            scene_action=scene_action_desc,
            character_ids=chars_present,
            location=continuity_ctx.get("inherited_environment")
        )

        instruction = {
            "scene_number": idx,
            "scene_id": f"scene_{idx}",
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "characters_present": chars_present,
            "motion_vector": motion_vector,
            "motion_intensity": motion_intensity,
            "camera_movement": cam_movement,
            "animation_style": anim_style,
            "animation_prompt": anim_prompt,
            "continuity_context": continuity_ctx
        }
        animation_instructions.append(instruction)

    state_dict["animation_instructions"] = animation_instructions
    state_dict["logs"].append({
        "agent": "AnimationDirectorAgent",
        "level": "SUCCESS",
        "message": f"Generated {len(animation_instructions)} 3D animation scene instructions with character lock & continuity."
    })
    return state_dict
