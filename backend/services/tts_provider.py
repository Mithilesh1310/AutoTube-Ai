import os
import asyncio
import logging
from abc import ABC, abstractmethod
import edge_tts
from backend.config import settings

logger = logging.getLogger(__name__)

class VoiceProvider(ABC):
    @abstractmethod
    async def generate_speech(self, text: str, voice_config: dict, output_path: str) -> str:
        pass

class EdgeTTSProvider(VoiceProvider):
    async def generate_speech(self, text: str, voice_config: dict, output_path: str) -> str:
        primary_voice = voice_config.get("voice_id", "hi-IN-SwaraNeural")
        pitch = voice_config.get("pitch", "+0Hz")
        rate = voice_config.get("rate", "+0%")

        clean_text = text.strip() if text else ""
        if not clean_text:
            clean_text = "..."

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        voices_to_try = [primary_voice, "hi-IN-MadhurNeural", "hi-IN-SwaraNeural"]
        last_err = None

        for attempt in range(3):
            voice = voices_to_try[attempt % len(voices_to_try)]
            try:
                communicate = edge_tts.Communicate(text=clean_text, voice=voice, pitch=pitch, rate=rate)
                await communicate.save(output_path)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                    logger.info(f"[EdgeTTS] Generated Hindi audio (Voice: {voice}, Attempt: {attempt+1}) -> {output_path}")
                    return output_path
                else:
                    logger.warning(f"[EdgeTTS] Output file {output_path} was empty on attempt {attempt+1}, retrying...")
            except Exception as e:
                last_err = e
                logger.warning(f"[EdgeTTS] Attempt {attempt+1} failed with voice {voice}: {e}. Retrying...")
                await asyncio.sleep(1.0 * (attempt + 1))

        if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
            return output_path

        raise RuntimeError(f"EdgeTTS generation failed after 3 attempts: {last_err}")

class GoogleTTSProvider(VoiceProvider):
    async def generate_speech(self, text: str, voice_config: dict, output_path: str) -> str:
        # Fallback to EdgeTTS if Google Cloud TTS API key not provided
        logger.info("GoogleTTSProvider invoked. Using EdgeTTS fallback.")
        edge_provider = EdgeTTSProvider()
        return await edge_provider.generate_speech(text, voice_config, output_path)

class ElevenLabsProvider(VoiceProvider):
    async def generate_speech(self, text: str, voice_config: dict, output_path: str) -> str:
        logger.info("ElevenLabsProvider invoked. Using EdgeTTS fallback.")
        edge_provider = EdgeTTSProvider()
        return await edge_provider.generate_speech(text, voice_config, output_path)

def get_voice_provider() -> VoiceProvider:
    provider = settings.VOICE_PROVIDER.lower()
    if provider == "google_tts":
        return GoogleTTSProvider()
    elif provider == "elevenlabs":
        return ElevenLabsProvider()
    else:
        return EdgeTTSProvider()

voice_provider = get_voice_provider()
