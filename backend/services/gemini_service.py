import os
import json
import time
import logging
from typing import Type, TypeVar, Optional, Tuple
from pydantic import BaseModel
from google import genai
from google.genai import types
from backend.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")).strip()
        self.client = None
        self.model_name = "gemini-flash-lite-latest"
        self._init_client()

    def _init_client(self):
        key = (settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")).strip()
        if key:
            self.api_key = key
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"[GeminiService] Failed to initialize Client: {e}")

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Tuple[T, dict]:
        """Generate structured output validated against Pydantic model and return execution metadata."""
        if not self.client:
            self._init_client()
        if not self.client:
            logger.warning("[GeminiService] API key not configured or client uninitialized.")
            raise ValueError("GEMINI_API_KEY is not configured.")

        start_time = time.time()
        
        # Models to try in order of preference
        models_to_try = ["gemini-flash-lite-latest", "gemini-flash-latest", self.model_name]
        
        last_error = None
        for model in models_to_try:
            try:
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=temperature,
                    system_instruction=system_instruction,
                )

                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )

                latency_ms = int((time.time() - start_time) * 1000)

                if response and response.text:
                    data = json.loads(response.text)
                    validated_obj = response_schema.model_validate(data)
                    meta = {
                        "model_name": model,
                        "provider_used": "GEMINI_LIVE",
                        "latency_ms": latency_ms,
                        "structured_validation_success": True,
                        "is_fallback": False
                    }
                    logger.info(f"[GeminiService] Live call success ({latency_ms}ms) using model '{model}'")
                    return validated_obj, meta
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    logger.warning(f"[GeminiService] Model '{model}' hit 429 rate limit. Waiting 6 seconds before retrying...")
                    time.sleep(6)
                else:
                    logger.warning(f"[GeminiService] Model '{model}' failed: {e}. Trying next...")
                last_error = e
                time.sleep(1)

        raise last_error or ValueError("All Gemini models failed.")

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        if not self.client:
            self._init_client()
        if not self.client:
            raise ValueError("GEMINI_API_KEY is not configured.")

        models_to_try = ["gemini-flash-lite-latest", "gemini-flash-latest"]
        for model in models_to_try:
            try:
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    system_instruction=system_instruction,
                )
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                logger.warning(f"[GeminiService] Text model '{model}' failed: {e}")
                time.sleep(1)

        return ""

gemini_service = GeminiService()
