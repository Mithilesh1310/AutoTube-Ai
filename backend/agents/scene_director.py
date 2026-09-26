import logging
from typing import List
from backend.services.character_bible import character_bible
from backend.services.gemini_service import gemini_service
from backend.agents.state import SceneData

logger = logging.getLogger(__name__)

def _synthesize_english_action(speaker: str, scene_ref: str, dialogue: str, chars: List[str]) -> str:
    """Translates and enriches Hindi scene actions into a vivid English visual sentence for 3D AI image generation."""
    has_devanagari = any('\u0900' <= ch <= '\u097f' for ch in (scene_ref + dialogue + speaker))
    if not has_devanagari and scene_ref:
        return f"{speaker}: {scene_ref}"

    char_names = ", ".join(c.capitalize() for c in chars)
    prompt = (
        f"You are a 3D animation director. Convert this Hindi animation scene note into ONE concise, vivid English visual action sentence for a 3D Pixar render.\n"
        f"Characters involved: {char_names}\n"
        f"Speaker: {speaker}\n"
        f"Hindi Action Note: {scene_ref}\n"
        f"Dialogue Context: {dialogue}\n"
        f"Strict Rule: Output ONLY one descriptive English action sentence showing what the characters look like and what active physical gesture or expression they are doing. No quotes, no preamble, no markdown."
    )
    try:
        en_desc = gemini_service.generate_text(prompt, temperature=0.3)
        en_desc = en_desc.strip().replace('"', '').replace('*', '').strip()
        if len(en_desc) > 15:
            return en_desc
    except Exception as e:
        logger.warning(f"[SceneDirector] Translation fallback: {e}")

    # Rule-based fallback if API is unavailable
    if "बांस" in scene_ref or "यंत्र" in scene_ref:
        return f"{char_names} playfully discovering and interacting with a glowing magical musical bamboo flute"
    if "उछल" in scene_ref or "छलांग" in scene_ref:
        return f"{char_names} leaping excitedly into the air with energetic cartoon gestures"
    if "बारिश" in scene_ref:
        return f"{char_names} dancing joyfully under sweet sparkling rain drops in a lush magical forest"
    return f"{char_names} actively exploring and expressing wonder in a colorful whimsical forest"

async def run_scene_director(state_dict: dict) -> dict:
    logger.info("[SceneDirector] Running Scene Density & Visual Enrichment Agent...")
    script_data = state_dict.get("script_data", {})
    script_lines = script_data.get("script", [])
    video_type = state_dict.get("video_type", "LONG")
    
    max_consecutive_dialogue = 1 if video_type == "SHORT" else 2

    scenes_list = []
    consecutive_dialogue_count = 0
    total_lines = len(script_lines)

    for idx, line in enumerate(script_lines, 1):
        speaker = line.get("speaker", "Narrator")
        dialogue = line.get("dialogue", "")
        tone = line.get("emotional_tone", "Happy").lower()
        ref = line.get("scene_reference", "").lower()
        
        # 1. Classify Primary Narrative Function
        if idx == 1:
            narrative_fn = "Hook & Instant Curiosity"
        elif idx <= max(2, total_lines // 4):
            narrative_fn = "Goal & Inciting Incident"
        elif idx <= max(3, (total_lines * 3) // 4):
            narrative_fn = "Obstacle Escalation & Teamwork"
        else:
            narrative_fn = "Earned Climax & Resolution"

        # 2. Determine Scene Type
        if "action" in ref or "run" in ref or "jump" in ref or "chase" in ref or "fly" in ref or "उछल" in ref:
            stype = "ACTION"
        elif "find" in ref or "discover" in ref or "map" in ref or "key" in ref or "riddle" in ref or "secret" in ref or "खोज" in ref or "चमक" in ref:
            stype = "DISCOVERY"
        elif "funny" in ref or "laugh" in ref or "joke" in ref or "trick" in ref or "prank" in ref or "हंस" in ref or "मजाक" in ref:
            stype = "COMEDY"
        elif "cry" in ref or "sad" in ref or "scared" in ref or "worry" in ref or "hug" in ref or "डर" in ref or "चिंता" in ref:
            stype = "EMOTIONAL"
        elif "ending" in ref or "resolution" in ref or "transition" in ref or "बारिश" in ref:
            stype = "TRANSITION"
        else:
            stype = "DIALOGUE"

        # 3. Handle Dialogue Density Limit
        if stype == "DIALOGUE":
            consecutive_dialogue_count += 1
            if consecutive_dialogue_count > max_consecutive_dialogue:
                activity_level = "HIGH"
                consecutive_dialogue_count = 0
                logger.info(f"[SceneDirector] Enriched visual activity for Scene #{idx} (Max consecutive DIALOGUE = {max_consecutive_dialogue}).")
            else:
                activity_level = "MEDIUM"
        else:
            activity_level = "HIGH"
            consecutive_dialogue_count = 0

        # 4. Identify Present Characters with Multi-Language Support
        line_combined_text = f"{speaker} {dialogue} {line.get('scene_reference', '')}"
        detected_chars = await character_bible.resolve_character_ids_async(line_combined_text, fallback=[])

        # If speaker is a character, prioritize them in front
        if speaker.lower() not in ["narrator", "कथावाचक"]:
            spk_chars = await character_bible.resolve_character_ids_async([speaker], fallback=[])
            for sc in spk_chars:
                if sc in detected_chars:
                    detected_chars.remove(sc)
                detected_chars.insert(0, sc)

        # Fallback to script characters or latest custom character
        if not detected_chars:
            script_chars = script_data.get("characters", [])
            detected_chars = await character_bible.resolve_character_ids_async(script_chars, fallback=[])

        chars_present = detected_chars

        # 5. Generate Vivid English Visual Action Description
        scene_ref = line.get("scene_reference", "").strip()
        english_action = _synthesize_english_action(
            speaker=speaker,
            scene_ref=scene_ref,
            dialogue=dialogue,
            chars=chars_present
        )

        # 6. Inject Character Bible Profiles
        visual_prompt = await character_bible.build_injected_visual_prompt(
            scene_description=english_action,
            character_ids=chars_present,
            location="lush magical cartoon forest with colorful giant flowers and golden sunlight"
        )

        cam = "Fast tracking medium shot" if stype == "ACTION" else ("Close-up discovery shot" if stype == "DISCOVERY" else "Wide vibrant establishing shot")

        scenes_list.append(
            SceneData(
                scene_number=idx,
                duration_seconds=6.0,
                location="Magical Cartoon Forest",
                characters_present=chars_present,
                visual_prompt=visual_prompt,
                camera_direction=cam,
                character_actions=english_action,
                dialogue=dialogue,
                speaker=speaker,
                scene_type=stype,
                primary_narrative_function=narrative_fn,
                visual_activity_level=activity_level,
                character_movement=english_action,
                environment_interaction="Lush vibrant foliage, sparkling sunlight and glowing flora",
                audio_mood=line.get("emotional_tone", "Happy")
            )
        )

    state_dict["scenes"] = scenes_list
    state_dict["current_step"] = "VOICE_GEN"
    state_dict["logs"].append({
        "agent": "SceneDirector",
        "level": "SUCCESS",
        "message": f"Created {len(scenes_list)} scene breakdowns with Visual Enrichment & Character Bible injection."
    })
    return state_dict
