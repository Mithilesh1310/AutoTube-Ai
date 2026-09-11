import logging
from typing import List
from pydantic import BaseModel
from backend.services.gemini_service import gemini_service
from backend.services.character_bible import character_bible
from backend.agents.state import ScriptStructure, ScriptSection

logger = logging.getLogger(__name__)

async def run_script_writer(state_dict: dict) -> dict:
    logger.info("[ScriptWriter] Running High-Entertainment Story Writer Agent...")
    idea = state_dict.get("selected_idea", {})
    video_type = state_dict.get("video_type", "LONG")
    rewrite_attempts = state_dict.get("script_retries", 0)
    feedback = state_dict.get("script_qa_feedback", "")

    characters = await character_bible.get_all_characters()
    chars_info = "\n".join([f"- {c['name']} ({c['character_id']}): Species = {c['species']}. Physical traits = {c.get('physical_description', '')}. Personality = {c['personality']}" for c in characters])

    entertainment_rules = """
ENTERTAINMENT & RETENTION DIRECTIVES:
1. HOOK (FIRST 1-3 SECONDS): Must create instant high curiosity or surprise! Line 1 MUST start with high action or discovery (e.g., 'देखो दोस्तों!', 'रुको!', 'हवा में यह क्या उड़ रहा है?!'). DO NOT start Line 1 with generic greetings ('नमस्ते', 'आज की कहानी में...') or slow setups ('अरे सुनो!'). Start directly in the middle of action or mystery!
2. VISUAL DENSITY BEATS: DO NOT write consecutive dialogue lines where characters just stand and talk! Every 2nd line MUST involve a vivid physical animation action (running, chasing, funny physical comedy, surprising discoveries, flying, climbing, transformation, sudden environmental changes).
3. CURIOSITY LOOPS: Keep the child asking "What happens next?" with mystery, unexpected obstacles, or hidden secrets.
4. ZERO PREACHINESS: High fun, humor, and playfulness. The moral must be naturally demonstrated through character actions, NOT preached like a lecture.
5. EARNED RESOLUTION: Protagonists MUST actively work together to solve the problem (NO magic wand cop-outs, NO wise turtle instantly solving it for them).
"""

    if video_type == "SHORT":
        target_dur = 45
        target_words = "85 to 110 Hindi words"
        structure_rules = """
SHORT VIDEO FORMAT (30-60 SECONDS):
- Line Count Requirement: GENERATE EXACTLY 6 TO 8 DIALOGUE LINES!
- Word Count Target: 85 to 110 Hindi words (Devanagari). Spoken duration MUST be strictly between 30 and 60 seconds!
- Must include at least 2 visually active action/discovery moments.
"""
    else:  # LONG (100-140 seconds)
        target_dur = 120
        target_words = "230 to 300 Hindi words"
        structure_rules = """
LONG VIDEO FORMAT (~2 MINUTES / 100-140 SECONDS):
- Line Count Requirement: GENERATE EXACTLY 12 TO 16 DETAILED DIALOGUE LINES ACROSS ALL 5 STAGES!
- Word Count Target: 230 to 300 Hindi words (Devanagari script). Spoken duration MUST be strictly between 100 and 140 seconds!
- Must include at least 5 visually active action/discovery/comedy moments across the 5 stages.
- STAGE 1 (HOOK & GOAL): Lines 1-3. High-curiosity hook + clear goal for characters.
- STAGE 2 (INCITING INCIDENT): Lines 4-6. Mystery or obstacle arises.
- STAGE 3 (OBSTACLE 1 - ATTEMPT & FAILURE): Lines 7-9. First attempt fails or escalates!
- STAGE 4 (OBSTACLE 2 - TEAMWORK & CLIMAX): Lines 10-13. Teamwork, clever thinking, and action climax.
- STAGE 5 (RESOLUTION & EMBEDDED MORAL): Lines 14-16. Earned resolution + natural positive moral.
"""

    personality_guidance = """
REGISTERED CHARACTER SPECIES & DIALOGUE VOICES:
- Chintu (Elephant): Elephant character with a trunk! Brave, kind, helpful leader ("घबराओ मत दोस्तों, हम सब मिलकर हल निकालेंगे!")
- Momo (Monkey): Playful monkey! Energetic, curious, slightly mischievous ("अरे वाह! देखो मैं कैसे छलांग लगाता हूँ!")
- Titu (Rabbit): Intelligent rabbit! Thoughtful, quick planner ("रुको दोस्तों! पहले ध्यान से सोचते हैं!")
- Mithu (Parrot): Expressive parrot! Funny, observant ("टे-टे! ऊपर से सब दिख रहा है, उधर देखो!")
- Baba Turtle (Tortoise): Calm, wise tortoise! Encouraging mentor ("धीरज रखो बच्चों, समझदारी से काम लो!")
"""

    if feedback and rewrite_attempts > 0:
        rewrite_instruction = f"""
==================================================
TARGETED REWRITE INSTRUCTIONS (Rewrite #{rewrite_attempts} of 3):
The previous script failed Quality & Entertainment evaluation due to the following detected issues:

DETECTED ISSUES TO FIX:
{feedback}

REVISION REQUIREMENT:
Fix ONLY the detected issues listed above while preserving the successful narrative parts of the story!
Ensure first line is a high-curiosity hook (NO 'नमस्ते' or slow greetings). Add visual action beats!
==================================================
"""
    else:
        rewrite_instruction = ""

    prompt = f"""
Write an original, highly entertaining Hindi Children's Cartoon Script in Devanagari script.

Video Type: {video_type}
Topic Title: {idea.get('topic_title')}
Premise: {idea.get('summary')}
Target Word Count: {target_words} ({target_dur} seconds spoken).

Available Character Universe:
{chars_info}
- Narrator (Warm Hindi storyteller)

{structure_rules}
{entertainment_rules}
{personality_guidance}
{rewrite_instruction}

Return structured JSON matching ScriptStructure.
"""

    system_instruction = "You are a senior animation showrunner and YouTube Kids entertainment strategist."

    try:
        res_obj, meta = gemini_service.generate_structured(
            prompt=prompt,
            response_schema=ScriptStructure,
            system_instruction=system_instruction,
            temperature=0.75
        )
        script_data = res_obj.model_dump()
        state_dict["script_generated_by_fallback"] = False
        state_dict["script_provider_used"] = "GEMINI_LIVE"
    except Exception as e:
        logger.warning(f"[ScriptWriter] Gemini API fallback: {e}")
        script_data = {
            "title_idea": idea.get("topic_title", "चिंटू और जादुई अनुभव"),
            "story_summary": idea.get("summary", "चिंटू और दोस्तों की मजेदार कहानी।"),
            "characters": ["chintu", "momo", "baba_turtle"],
            "script": [
                {
                    "speaker": "Narrator",
                    "dialogue": "अरे सुनो! क्या तुमने कभी जंगल में कोई चमकती हुई जादुई चाबी देखी है?",
                    "emotional_tone": "Curious",
                    "scene_reference": "Scene 1: Hook & Mystery"
                },
                {
                    "speaker": "chintu",
                    "dialogue": "मोमो देखो! यह चाबी तो खुद-ब-खुद हवा में घूम रही है!",
                    "emotional_tone": "Excited",
                    "scene_reference": "Scene 2: Problem & Discovery"
                },
                {
                    "speaker": "momo",
                    "dialogue": "रुको चिंटू! इसे पकड़ने के लिए हमें मिलकर छलांग लगानी होगी!",
                    "emotional_tone": "Playful",
                    "scene_reference": "Scene 3: Fast Adventure"
                },
                {
                    "speaker": "baba_turtle",
                    "dialogue": "शाबाश बच्चों! समझदारी और एकता से ही हर रहस्य सुलझता है।",
                    "emotional_tone": "Wise",
                    "scene_reference": "Scene 4: Climax & Resolution"
                },
                {
                    "speaker": "Narrator",
                    "dialogue": "और इस तरह चिंटू और मोमो ने साबित कर दिया कि मिलकर काम करना ही सबसे बड़ी चाबी है!",
                    "emotional_tone": "Warm",
                    "scene_reference": "Scene 5: Ending & Moral"
                }
            ],
            "moral": "सच्ची एकता और समझदारी से हर मुश्किल सुलझ जाती है।",
            "estimated_duration": target_dur,
            "is_fallback": True,
            "provider_name": "structured_template_fallback"
        }
        state_dict["script_generated_by_fallback"] = True
        state_dict["script_provider_used"] = "GEMINI_FALLBACK"

    state_dict["script_data"] = script_data
    state_dict["current_step"] = "SCRIPT_QA"
    state_dict["logs"].append({
        "agent": "ScriptWriter",
        "level": "SUCCESS",
        "message": f"Generated high-entertainment script for format {video_type} (Rewrite #{rewrite_attempts})."
    })
    return state_dict
