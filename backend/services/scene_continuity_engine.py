import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SceneContinuityState:
    def __init__(self):
        self.last_scene_number: int = 0
        self.last_character_positions: Dict[str, str] = {} # e.g. {"chintu": "screen_right"}
        self.last_motion_direction: str = "right_to_left" # or "left_to_right", "toward_camera", "stationary"
        self.environment: str = "Vibrant 3D Cartoon Forest"
        self.time_of_day: str = "Sunny Daytime"
        self.lighting_mood: str = "Golden Warm Shimmer"
        self.active_props: List[str] = []

class SceneContinuityEngine:
    """
    Scene Continuity Engine:
    Tracks movement direction, character positions, lighting, time of day, camera angles,
    and passes continuity context to sequential scene animation instructions.
    """
    def __init__(self):
        self.state = SceneContinuityState()

    def reset_for_new_story(self):
        self.state = SceneContinuityState()

    def process_scene_continuity(self, scene_number: int, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        speaker = scene_data.get("speaker", "Narrator")
        ref_action = scene_data.get("character_actions", "") or scene_data.get("visual_prompt", "")
        
        # Calculate continuous entry/exit motion direction
        if "run" in ref_action.lower() or "chase" in ref_action.lower():
            if self.state.last_motion_direction == "left_to_right":
                entry_motion = "Entering frame from left, continuing motion toward right"
                self.state.last_motion_direction = "left_to_right"
            else:
                entry_motion = "Moving from right to left across lush background"
                self.state.last_motion_direction = "right_to_left"
        elif "fly" in ref_action.lower():
            entry_motion = "Soaring gracefully from sky toward foreground"
            self.state.last_motion_direction = "top_to_bottom"
        else:
            entry_motion = "Standing expressively with dynamic gesturing"
            self.state.last_motion_direction = "stationary"

        continuity_context = {
            "scene_number": scene_number,
            "inherited_time_of_day": self.state.time_of_day,
            "inherited_lighting": self.state.lighting_mood,
            "inherited_environment": self.state.environment,
            "motion_vector": entry_motion,
            "previous_scene": self.state.last_scene_number
        }

        # Update state
        self.state.last_scene_number = scene_number
        return continuity_context

scene_continuity_engine = SceneContinuityEngine()
