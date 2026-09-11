import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ProviderCapabilityRegistry:
    """
    Registry tracking AI animation provider capabilities, costs, and availability.
    Used by AUTO visual generation mode to select optimal provider.
    """
    def __init__(self):
        self.providers: Dict[str, Dict[str, Any]] = {
            "fal_ai": {
                "name": "Fal AI (Luma Dream Machine)",
                "supports_text_to_video": True,
                "supports_image_to_video": True,
                "supports_reference_images": True,
                "max_duration": 10.0,
                "supported_resolutions": ["1080x1920", "1920x1080", "1024x1024"],
                "estimated_cost_per_5s": 0.05,
                "queue_time_avg_sec": 15,
                "is_healthy": True
            },
            "replicate": {
                "name": "Replicate (Kling / SVD)",
                "supports_text_to_video": True,
                "supports_image_to_video": True,
                "supports_reference_images": False,
                "max_duration": 5.0,
                "supported_resolutions": ["1080x1920", "1920x1080"],
                "estimated_cost_per_5s": 0.06,
                "queue_time_avg_sec": 30,
                "is_healthy": True
            },
            "runway": {
                "name": "Runway Gen-2/Gen-3",
                "supports_text_to_video": True,
                "supports_image_to_video": True,
                "supports_reference_images": True,
                "max_duration": 10.0,
                "supported_resolutions": ["1920x1080", "1080x1920"],
                "estimated_cost_per_5s": 0.10,
                "queue_time_avg_sec": 20,
                "is_healthy": True
            }
        }

    def select_best_provider(
        self,
        scene_type: str,
        video_type: str = "LONG",
        user_budget_class: str = "PRO",
        requires_image_to_video: bool = True
    ) -> str:
        """Selects optimal provider based on scene requirements and provider health."""
        if requires_image_to_video:
            healthy_candidates = [
                pid for pid, info in self.providers.items()
                if info.get("is_healthy") and info.get("supports_image_to_video")
            ]
            if "fal_ai" in healthy_candidates:
                return "fal_ai"
            elif healthy_candidates:
                return healthy_candidates[0]
        
        return "fal_ai"

    def get_provider_details(self, provider_id: str) -> Dict[str, Any]:
        return self.providers.get(provider_id, {
            "name": provider_id,
            "supports_text_to_video": True,
            "supports_image_to_video": True,
            "estimated_cost_per_5s": 0.05
        })

provider_capability_registry = ProviderCapabilityRegistry()
