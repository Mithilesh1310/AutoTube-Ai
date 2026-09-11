import os
import random
import asyncio
import urllib.parse
import httpx
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from backend.config import settings

logger = logging.getLogger(__name__)

class ImageGenerationError(RuntimeError):
    """Raised when all real AI image generation providers fail in production."""
    pass

class ImageProviderResult:
    def __init__(
        self,
        image_path: str,
        provider_name: str,
        provider_type: str = "ai",
        is_fallback: bool = False,
        is_placeholder: bool = False
    ):
        self.image_path = image_path
        self.provider_name = provider_name
        self.provider_type = provider_type  # "ai" or "placeholder"
        self.is_fallback = is_fallback
        self.is_placeholder = is_placeholder

    def to_dict(self) -> dict:
        return {
            "image_path": self.image_path,
            "provider_name": self.provider_name,
            "provider_type": self.provider_type,
            "is_fallback": self.is_fallback,
            "is_placeholder": self.is_placeholder
        }

class ImageProvider(ABC):
    @abstractmethod
    async def generate_image(self, prompt: str, output_path: str, width: int = 1024, height: int = 1024) -> ImageProviderResult:
        pass

class VisualProvider(ABC):
    @abstractmethod
    async def generate_scene_visual(
        self,
        prompt: str,
        output_path: str,
        is_vertical: bool = False,
        allow_placeholder: Optional[bool] = None
    ) -> ImageProviderResult:
        pass

class HuggingFaceImageProvider(ImageProvider):
    """
    PRIMARY AI Image Provider using live Hugging Face Inference API.
    Model: black-forest-labs/FLUX.1-schnell (with SDXL fallbacks).
    """
    def __init__(self):
        self.models = [
            "black-forest-labs/FLUX.1-schnell",
            "ByteDance/SDXL-Lightning",
            "stabilityai/stable-diffusion-xl-base-1.0"
        ]

    async def generate_image(self, prompt: str, output_path: str, width: int = 1024, height: int = 1024) -> ImageProviderResult:
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        api_key = (settings.IMAGE_API_KEY or "").strip()
        if not api_key or not api_key.startswith("hf_"):
            raise ValueError("IMAGE_API_KEY is not configured with a valid HuggingFace token (must start with 'hf_').")

        from huggingface_hub import InferenceClient

        clean_prompt = prompt.replace("[", "").replace("]", "").strip()[:500]
        client = InferenceClient(token=api_key)

        last_error = None
        for model in self.models:
            try:
                # Run synchronous client.text_to_image in async thread pool
                img = await asyncio.to_thread(
                    client.text_to_image,
                    prompt=clean_prompt,
                    model=model,
                    width=width,
                    height=height
                )

                if img and hasattr(img, "save"):
                    # Target aspect ratio upscale
                    target_w = 1080 if width < height else 1920
                    target_h = 1920 if width < height else 1080
                    high_res = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    high_res.save(output_path, format="PNG", optimize=True)
                    
                    # Validate image with PIL
                    with Image.open(output_path) as val_img:
                        val_img.verify()
                    
                    file_size = os.path.getsize(output_path)
                    if file_size < 10000:
                        raise ValueError(f"Generated image too small: {file_size} bytes")

                    logger.info(f"[HuggingFace] Successfully generated AI image ({file_size} bytes, {target_w}x{target_h}) via '{model}' -> {output_path}")
                    return ImageProviderResult(
                        image_path=output_path,
                        provider_name="HuggingFaceImageProvider",
                        provider_type="ai",
                        is_fallback=False,
                        is_placeholder=False
                    )
            except Exception as e:
                logger.warning(f"[HuggingFace] Model '{model}' failed: {e}. Trying next...")
                last_error = e

        raise last_error or RuntimeError("All HuggingFace models failed.")

class PollinationsImageProvider(ImageProvider):
    """
    AI Image Provider using Pollinations unified API with API key authentication & fallback.
    """
    async def generate_image(self, prompt: str, output_path: str, width: int = 1024, height: int = 1024) -> ImageProviderResult:
        import io
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        clean_prompt = prompt.replace("[", "").replace("]", "").strip()
        encoded_prompt = urllib.parse.quote(clean_prompt[:450])
        
        api_key = (settings.IMAGE_API_KEY or "").strip()
        headers = {}
        if api_key.startswith("sk_") or api_key.startswith("pk_"):
            headers["Authorization"] = f"Bearer {api_key}"

        last_error = None
        for attempt in range(3):
            seed = random.randint(1000, 999999)
            urls_to_try = []
            if api_key:
                urls_to_try.append(f"https://gen.pollinations.ai/image/{encoded_prompt}?key={api_key}&width={width}&height={height}&seed={seed}&model=flux&nologo=true")
            urls_to_try.append(f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&model=flux&nologo=true")

            for url in urls_to_try:
                try:
                    async with httpx.AsyncClient(timeout=45.0) as client:
                        resp = await client.get(url, headers=headers)
                        if resp.status_code == 200 and len(resp.content) > 5000:
                            raw_img = Image.open(io.BytesIO(resp.content))
                            
                            # For thumbnails: keep native 1024x1024 square (perfect for YouTube Shorts & cards)
                            if "thumbnail" in output_path.lower():
                                raw_img.save(output_path, format="PNG", optimize=True)
                            else:
                                target_w = 1080 if width < height else 1920
                                target_h = 1920 if width < height else 1080
                                # High-quality Lanczos upscale to full HD canvas
                                high_res = raw_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                                high_res.save(output_path, format="PNG", optimize=True)
                            
                            file_size = os.path.getsize(output_path)
                            logger.info(f"[Pollinations] Saved High-Res AI scene image ({file_size} bytes, {raw_img.size}) -> {output_path}")
                            return ImageProviderResult(
                                image_path=output_path,
                                provider_name="PollinationsImageProvider",
                                provider_type="ai",
                                is_fallback=True,
                                is_placeholder=False
                            )
                        elif resp.status_code == 429:
                            logger.warning(f"[Pollinations] Rate limited (429). Retrying...")
                            await asyncio.sleep(2)
                        else:
                            logger.warning(f"[Pollinations] Status {resp.status_code} for {url[:60]}. Trying next...")
                except Exception as fetch_err:
                    logger.warning(f"[Pollinations] Request error for {url[:60]}: {fetch_err}")
                    last_error = fetch_err
            
            await asyncio.sleep(2)

        raise last_error or RuntimeError("Pollinations generation failed after all attempts.")

class LocalCanvasImageProvider(ImageProvider):
    """
    Development/Test placeholder canvas generator.
    CRITICAL RULE: MUST NEVER BE USED WHEN TEST_MODE=false.
    """
    async def generate_image(self, prompt: str, output_path: str, width: int = 1024, height: int = 1024) -> ImageProviderResult:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        img = Image.new("RGB", (width, height), color=(41, 128, 185))
        draw = ImageDraw.Draw(img)

        # Sun & Hills
        draw.ellipse([width - 300, 50, width - 100, 250], fill=(241, 196, 15))
        draw.ellipse([-200, height - 400, width // 2 + 200, height + 400], fill=(46, 204, 113))
        draw.ellipse([width // 3, height - 450, width + 300, height + 400], fill=(39, 174, 96))

        draw.rectangle([50, 50, width - 50, 150], fill=(0, 0, 0, 128))
        
        try:
            font = ImageFont.truetype("arial.ttf", 32)
        except Exception:
            font = ImageFont.load_default()

        draw.text((80, 80), f"[TEST CANVAS PLACEHOLDER]: {prompt[:50]}...", fill=(255, 255, 255), font=font)
        img.save(output_path)
        logger.warning(f"[LocalCanvas] Generated Placeholder Image (TEST ONLY) -> {output_path}")
        
        return ImageProviderResult(
            image_path=output_path,
            provider_name="LocalCanvasImageProvider",
            provider_type="placeholder",
            is_fallback=True,
            is_placeholder=True
        )

class KenBurnsVisualProvider(VisualProvider):
    """
    Orchestrates:
    PRIMARY:   HuggingFaceImageProvider
    SECONDARY: PollinationsImageProvider
    FALLBACK:  STOP PIPELINE (LocalCanvas ONLY IF settings.TEST_MODE is True)
    """
    def __init__(self):
        self.primary_provider = HuggingFaceImageProvider()
        self.secondary_provider = PollinationsImageProvider()
        self.fallback_provider = LocalCanvasImageProvider()

    @property
    def hf_provider(self) -> HuggingFaceImageProvider:
        return self.primary_provider

    @property
    def pollinations_provider(self) -> PollinationsImageProvider:
        return self.secondary_provider

    async def generate_scene_visual(
        self,
        prompt: str,
        output_path: str,
        is_vertical: bool = False,
        allow_placeholder: Optional[bool] = None
    ) -> ImageProviderResult:
        # Native 1024x1024 square generation produces maximum model accuracy and zero distortion
        width = 1024
        height = 1024

        # Strict Test Mode evaluation:
        # TEST_MODE=false completely forbids LocalCanvasImageProvider regardless of caller
        is_test_mode = getattr(settings, "TEST_MODE", False)
        can_use_placeholder = is_test_mode and (allow_placeholder is True if allow_placeholder is not None else False)

        hf_error = None
        pollinations_error = None

        # 1. PRIMARY: Hugging Face
        try:
            return await self.primary_provider.generate_image(prompt, output_path, width, height)
        except Exception as e:
            logger.warning(f"Primary HuggingFace ImageProvider failed: {e}. Falling back to Pollinations...")
            hf_error = e

        # 2. SECONDARY: Pollinations
        try:
            return await self.secondary_provider.generate_image(prompt, output_path, width, height)
        except Exception as e:
            logger.warning(f"Secondary Pollinations ImageProvider failed: {e}.")
            pollinations_error = e

        # 3. IF BOTH AI PROVIDERS FAIL:
        if not can_use_placeholder:
            err_msg = (
                f"PRODUCTION IMAGE GATE VIOLATION: All AI Image Providers failed! "
                f"HuggingFace: {hf_error} | Pollinations: {pollinations_error}. "
                f"Placeholders strictly blocked when TEST_MODE=false."
            )
            logger.error(f"[VisualProvider] {err_msg}")
            raise ImageGenerationError(err_msg)

        # 4. ONLY if TEST_MODE is explicitly True
        logger.warning("[VisualProvider] TEST_MODE=true is active. Falling back to LocalCanvas placeholder.")
        return await self.fallback_provider.generate_image(prompt, output_path, width, height)

visual_provider = KenBurnsVisualProvider()
image_provider = visual_provider.primary_provider
