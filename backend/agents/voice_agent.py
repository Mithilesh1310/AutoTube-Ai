import os
import asyncio
import logging
from backend.services.tts_provider import voice_provider
from backend.services.character_bible import character_bible

logger = logging.getLogger(__name__)

async def run_voice_agent(state_dict: dict) -> dict:
    logger.info("[VoiceAgent] Running Voice Generation Agent...")
    job_id = state_dict.get("job_id", "job_demo")
    scenes = state_dict.get("scenes", [])
    
    base_dir = f"./storage/renders/{job_id}/audios"
    os.makedirs(base_dir, exist_ok=True)

    semaphore = asyncio.Semaphore(2)
    
    async def generate_single_voice(scene):
        async with semaphore:
            scene_num = scene.scene_number
            speaker = scene.speaker
            dialogue = scene.dialogue

            if not dialogue or not dialogue.strip():
                return scene_num, None

            voice_config = {
                "provider": "edge_tts",
                "voice_id": "hi-IN-SwaraNeural",
                "pitch": "+0Hz",
                "rate": "+0%"
            }
            
            char = await character_bible.get_character_by_id(speaker)
            if char and char.get("voice_config"):
                voice_config = char["voice_config"]

            audio_path = os.path.join(base_dir, f"scene_{scene_num}.mp3")
            try:
                await voice_provider.generate_speech(
                    text=dialogue.strip(),
                    voice_config=voice_config,
                    output_path=audio_path
                )
                await asyncio.sleep(0.2)
                return scene_num, audio_path
            except Exception as e:
                logger.error(f"Voice generation failed for scene {scene_num}: {e}")
                raise e

    results = await asyncio.gather(*[generate_single_voice(s) for s in scenes])
    generated_audios = {num: path for num, path in results if path}

    state_dict["generated_audios"] = generated_audios
    state_dict["current_step"] = "VISUAL_GEN"
    state_dict["logs"].append({
        "agent": "VoiceAgent",
        "level": "SUCCESS",
        "message": f"Generated {len(generated_audios)} Hindi character audio tracks."
    })
    return state_dict
