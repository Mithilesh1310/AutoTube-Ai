import os
import asyncio
import httpx
import logging
import urllib.parse
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from backend.config import settings

logger = logging.getLogger(__name__)

class AnimationGenerationError(RuntimeError):
    """Raised when animation provider generation fails or produces invalid output."""
    pass

class AnimationResult:
    def __init__(
        self,
        video_clip_path: str,
        provider_name: str,
        duration: float,
        provider_job_id: str = "",
        cost: float = 0.0,
        is_fallback: bool = False
    ):
        self.video_clip_path = video_clip_path
        self.provider_name = provider_name
        self.duration = duration
        self.provider_job_id = provider_job_id
        self.cost = cost
        self.is_fallback = is_fallback

class ProviderJobStatus:
    def __init__(self, status: str, progress: float = 0.0, video_url: Optional[str] = None, error: Optional[str] = None):
        self.status = status # IN_QUEUE, IN_PROGRESS, COMPLETED, FAILED
        self.progress = progress
        self.video_url = video_url
        self.error = error

class AnimationProvider(ABC):
    @abstractmethod
    async def generate_from_text(
        self,
        prompt: str,
        output_path: str,
        duration: float = 5.0,
        aspect_ratio: str = "16:9"
    ) -> AnimationResult:
        pass

    @abstractmethod
    async def generate_from_image(
        self,
        image_path: str,
        prompt: str,
        output_path: str,
        duration: float = 5.0,
        aspect_ratio: str = "16:9"
    ) -> AnimationResult:
        pass

    @abstractmethod
    async def get_job_status(self, provider_job_id: str) -> ProviderJobStatus:
        pass

    @abstractmethod
    async def download_result(self, video_url: str, output_path: str) -> str:
        pass

    @abstractmethod
    async def estimate_cost(self, duration: float, is_img2vid: bool = True) -> float:
        pass

class FalAIAnimationProvider(AnimationProvider):
    """
    PRIMARY AI Animation Provider calling Fal AI (Luma Dream Machine / Kling / Minimax API).
    """
    def __init__(self, api_key: str = None):
        self.api_key = (api_key or settings.ANIMATION_API_KEY or "").strip()
        self.base_url = "https://queue.fal.run/fal-ai/luma-dream-machine"

    async def generate_from_image(
        self,
        image_path: str,
        prompt: str,
        output_path: str,
        duration: float = 5.0,
        aspect_ratio: str = "16:9"
    ) -> AnimationResult:
        if not self.api_key:
            raise AnimationGenerationError("Fal AI API key (ANIMATION_API_KEY) is not configured.")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload
        payload = {
            "prompt": prompt[:400],
            "aspect_ratio": "9:16" if aspect_ratio == "9:16" else "16:9",
            "loop": False
        }

        logger.info(f"[FalAI] Triggering Fal AI Image-to-Video generation for: {prompt[:60]}...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.base_url, json=payload, headers=headers)
            if resp.status_code not in [200, 201, 202]:
                raise AnimationGenerationError(f"Fal AI API error ({resp.status_code}): {resp.text}")

            res_data = resp.json()
            request_id = res_data.get("request_id")
            
            # Poll status until completed (max 90 seconds)
            status_url = res_data.get("status_url") or f"https://queue.fal.run/fal-ai/luma-dream-machine/requests/{request_id}/status"
            video_url = None
            
            for _ in range(30):
                await asyncio.sleep(3)
                st_resp = await client.get(status_url, headers=headers)
                if st_resp.status_code == 200:
                    st_data = st_resp.json()
                    status = st_data.get("status")
                    if status == "COMPLETED":
                        payload_res = st_data.get("payload", {})
                        video_url = payload_res.get("video", {}).get("url") or payload_res.get("video_url")
                        break
                    elif status == "FAILED":
                        raise AnimationGenerationError(f"Fal AI job failed: {st_data.get('error')}")

            if not video_url:
                raise AnimationGenerationError("Fal AI job timed out or returned no video URL.")

            # Download clip
            await self.download_result(video_url, output_path)
            cost = await self.estimate_cost(duration, is_img2vid=True)

            return AnimationResult(
                video_clip_path=output_path,
                provider_name="FalAIAnimationProvider",
                duration=duration,
                provider_job_id=request_id or "",
                cost=cost,
                is_fallback=False
            )

    async def generate_from_text(
        self,
        prompt: str,
        output_path: str,
        duration: float = 5.0,
        aspect_ratio: str = "16:9"
    ) -> AnimationResult:
        return await self.generate_from_image("", prompt, output_path, duration, aspect_ratio)

    async def get_job_status(self, provider_job_id: str) -> ProviderJobStatus:
        return ProviderJobStatus(status="COMPLETED")

    async def download_result(self, video_url: str, output_path: str) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(video_url)
            if resp.status_code == 200 and len(resp.content) > 10000:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return output_path
            else:
                raise AnimationGenerationError(f"Failed to download video from {video_url}")

    async def estimate_cost(self, duration: float, is_img2vid: bool = True) -> float:
        # Conceptual pricing ~$0.05 per 5 sec video clip
        return round((duration / 5.0) * 0.05, 4)

class ReplicateAnimationProvider(AnimationProvider):
    """
    SECONDARY FALLBACK AI Animation Provider calling Replicate API.
    """
    def __init__(self, api_key: str = None):
        self.api_key = (api_key or settings.ANIMATION_API_KEY or "").strip()

    async def generate_from_image(
        self,
        image_path: str,
        prompt: str,
        output_path: str,
        duration: float = 5.0,
        aspect_ratio: str = "16:9"
    ) -> AnimationResult:
        if not self.api_key:
            raise AnimationGenerationError("Replicate API key is not configured.")

        # Trigger Replicate API via httpx
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"input": {"prompt": prompt, "duration": duration}}
        
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post("https://api.replicate.com/v1/predictions", json=payload, headers=headers)
            if resp.status_code not in [200, 201]:
                raise AnimationGenerationError(f"Replicate API error: {resp.text}")
            
            res_data = resp.json()
            video_url = res_data.get("output")
            if isinstance(video_url, list):
                video_url = video_url[0]
                
            if not video_url:
                raise AnimationGenerationError("Replicate API did not return output video URL.")

            await self.download_result(video_url, output_path)
            return AnimationResult(
                video_clip_path=output_path,
                provider_name="ReplicateAnimationProvider",
                duration=duration,
                cost=0.06,
                is_fallback=True
            )

    async def generate_from_text(self, prompt: str, output_path: str, duration: float = 5.0, aspect_ratio: str = "16:9") -> AnimationResult:
        return await self.generate_from_image("", prompt, output_path, duration, aspect_ratio)

    async def get_job_status(self, provider_job_id: str) -> ProviderJobStatus:
        return ProviderJobStatus(status="COMPLETED")

    async def download_result(self, video_url: str, output_path: str) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(video_url)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return output_path
            raise AnimationGenerationError("Failed to download replicate output.")

    async def estimate_cost(self, duration: float, is_img2vid: bool = True) -> float:
        return 0.06

class PollinationsAnimationProvider(AnimationProvider):
    """
    AI Video Animation Provider calling Pollinations (Nova Reel model) API.
    """
    def __init__(self, api_key: str = None):
        self.api_key = (api_key or settings.IMAGE_API_KEY or "").strip()
        self.base_url = "https://gen.pollinations.ai/image"

    async def generate_from_text(
        self,
        prompt: str,
        output_path: str,
        duration: float = 6.0,
        aspect_ratio: str = "9:16"
    ) -> AnimationResult:
        if not self.api_key:
            raise AnimationGenerationError("Pollinations API key is not configured.")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        clean_prompt = prompt.replace("[", "").replace("]", "").strip()[:400]
        encoded_prompt = urllib.parse.quote(clean_prompt)
        dur = max(6, int(duration))
        url = f"{self.base_url}/{encoded_prompt}?model=nova-reel&duration={dur}"

        logger.info(f"[PollinationsVideo] Requesting Nova Reel video generation for: {clean_prompt[:60]}...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200 and len(resp.content) > 10000:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                cost = round(dur * 0.08, 4)
                return AnimationResult(
                    video_clip_path=output_path,
                    provider_name="PollinationsAnimationProvider",
                    duration=float(dur),
                    provider_job_id="pollinations_nova_reel",
                    cost=cost,
                    is_fallback=False
                )
            elif resp.status_code == 402:
                raise AnimationGenerationError(f"Pollinations 402 Payment Required: {resp.text}")
            else:
                raise AnimationGenerationError(f"Pollinations Video API error ({resp.status_code}): {resp.text}")

    async def generate_from_image(self, image_path: str, prompt: str, output_path: str, duration: float = 6.0, aspect_ratio: str = "9:16") -> AnimationResult:
        return await self.generate_from_text(prompt, output_path, duration, aspect_ratio)

    async def get_job_status(self, provider_job_id: str) -> ProviderJobStatus:
        return ProviderJobStatus(status="COMPLETED")

    async def download_result(self, video_url: str, output_path: str) -> str:
        return output_path

    async def estimate_cost(self, duration: float, is_img2vid: bool = True) -> float:
        return round(duration * 0.08, 4)

class NullAnimationProvider(AnimationProvider):
    """
    PRODUCTION SAFETY FALLBACK: Fails cleanly with clear status when credentials missing.
    """
    async def generate_from_image(self, image_path: str, prompt: str, output_path: str, duration: float = 5.0, aspect_ratio: str = "16:9") -> AnimationResult:
        raise AnimationGenerationError(
            "FAILED_ANIMATION_GENERATION: No live animation provider API keys configured (ANIMATION_API_KEY). "
            "Please set ANIMATION_API_KEY in environment variables."
        )

    async def generate_from_text(self, prompt: str, output_path: str, duration: float = 5.0, aspect_ratio: str = "16:9") -> AnimationResult:
        return await self.generate_from_image("", prompt, output_path, duration, aspect_ratio)

    async def get_job_status(self, provider_job_id: str) -> ProviderJobStatus:
        return ProviderJobStatus(status="FAILED", error="Unconfigured provider")

    async def download_result(self, video_url: str, output_path: str) -> str:
        raise AnimationGenerationError("Null provider cannot download result.")

    async def estimate_cost(self, duration: float, is_img2vid: bool = True) -> float:
        return 0.0

class PluggableAnimationProviderManager:
    """
    Orchestrates provider selection:
    PRIMARY: Pollinations / Fal AI
    FALLBACK: Replicate / Kling
    NULL: Production safety failure (never outputs fake placeholder MP4 in production).
    """
    def __init__(self):
        self.pollinations_provider = PollinationsAnimationProvider()
        self.fal_provider = FalAIAnimationProvider()
        self.replicate_provider = ReplicateAnimationProvider()
        self.null_provider = NullAnimationProvider()

    async def generate_scene_animation(
        self,
        prompt: str,
        output_path: str,
        source_image_path: Optional[str] = None,
        duration: float = 5.0,
        aspect_ratio: str = "16:9"
    ) -> AnimationResult:
        last_error = None

        # Check Pollinations Nova Reel if configured
        if self.pollinations_provider.api_key:
            try:
                return await self.pollinations_provider.generate_from_text(prompt, output_path, duration, aspect_ratio)
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[AnimationProvider] Pollinations Nova Reel failed: {e}. Trying next provider...")

        # Check Fal AI
        try:
            if source_image_path and os.path.exists(source_image_path):
                return await self.fal_provider.generate_from_image(source_image_path, prompt, output_path, duration, aspect_ratio)
            else:
                return await self.fal_provider.generate_from_text(prompt, output_path, duration, aspect_ratio)
        except Exception as e:
            last_error = f"{last_error} | Fal AI: {str(e)}" if last_error else str(e)
            logger.warning(f"[AnimationProvider] Primary Fal AI failed: {e}. Trying Replicate fallback...")

        # Fallback to Replicate
        try:
            if source_image_path and os.path.exists(source_image_path):
                return await self.replicate_provider.generate_from_image(source_image_path, prompt, output_path, duration, aspect_ratio)
            else:
                return await self.replicate_provider.generate_from_text(prompt, output_path, duration, aspect_ratio)
        except Exception as e:
            last_error = f"{last_error} | Replicate: {str(e)}"
            logger.error(f"[AnimationProvider] Secondary Replicate failed: {e}.")

        # If all AI providers fail, invoke null provider or raise exact upstream failure
        if last_error:
            raise AnimationGenerationError(f"FAILED_ANIMATION_GENERATION: All AI Video Providers failed. {last_error}")

        return await self.null_provider.generate_from_image("", prompt, output_path, duration, aspect_ratio)

animation_provider_manager = PluggableAnimationProviderManager()
