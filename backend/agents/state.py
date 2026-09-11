from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SceneData(BaseModel):
    scene_number: int
    duration_seconds: float = 6.0
    location: str = "Magical Forest"
    characters_present: List[str] = Field(default_factory=list)
    visual_prompt: str
    camera_direction: str = "Wide shot"
    character_actions: str = "Talking"
    dialogue: str = ""
    speaker: str = "Narrator"
    scene_type: str = "DIALOGUE" # ACTION, DISCOVERY, COMEDY, DIALOGUE, EMOTIONAL, TRANSITION
    primary_narrative_function: str = "Story Progression"
    visual_activity_level: str = "MEDIUM" # HIGH, MEDIUM, LOW
    character_movement: str = "Speaking expressively"
    environment_interaction: str = "Vibrant Forest environment"
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    is_placeholder: bool = False
    is_fallback: bool = False
    provider_name: str = "image_provider"

class ScriptSection(BaseModel):
    speaker: str
    dialogue: str
    emotional_tone: str
    scene_reference: str

class ScriptStructure(BaseModel):
    title_idea: str
    story_summary: str
    characters: List[str]
    script: List[ScriptSection]
    moral: str
    estimated_duration: int
    is_fallback: bool = False
    provider_name: str = "gemini"

class AssetMetadata(BaseModel):
    file_path: str
    asset_type: str # IMAGE, AUDIO, MUSIC, SUBTITLE, RENDER, THUMBNAIL
    provider_name: str
    provider_type: str # ai, tts, ffmpeg, canvas_fallback
    is_fallback: bool = False
    is_placeholder: bool = False
    file_size: int = 0

class PipelineState(BaseModel):
    job_id: str
    video_type: str = "LONG" # 'SHORT' or 'LONG'
    current_step: str = "RESEARCH"
    verification_status: str = "IMPLEMENTED" # IMPLEMENTED, TESTED_WITH_FALLBACK, LIVE_API_VERIFIED, PRODUCTION_VERIFIED
    
    # Mode
    test_mode: bool = True # If True, allows fallback visual upload for local testing
    
    # Idea Research
    candidate_ideas: List[Dict[str, Any]] = Field(default_factory=list)
    selected_idea: Optional[Dict[str, Any]] = None
    research_is_fallback: bool = False
    
    # Script & QA
    script_data: Optional[ScriptStructure] = None
    script_qa_score: float = 0.0
    script_qa_feedback: str = ""
    script_retries: int = 0
    script_generated_by_fallback: bool = False
    script_provider_used: str = "GEMINI_LIVE"
    
    # Scene Breakdown
    scenes: List[SceneData] = Field(default_factory=list)
    
    # Render Assets
    generated_images: Dict[int, str] = Field(default_factory=dict)
    generated_audios: Dict[int, str] = Field(default_factory=dict)
    asset_metadata_map: Dict[str, AssetMetadata] = Field(default_factory=dict)
    has_placeholder_images: bool = False
    has_fallback_images: bool = False
    
    bgm_path: Optional[str] = None
    subtitle_path: Optional[str] = None
    
    # Output Video & QA
    rendered_video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    thumbnail_is_placeholder: bool = False
    thumbnail_provider: str = "image_provider"
    video_qa_passed: bool = False
    
    # Strict Production Gate Validation
    production_gate_passed: bool = False
    production_gate_reasons: List[str] = Field(default_factory=list)
    
    # SEO & Metadata
    title: str = ""
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    
    # YouTube Upload
    youtube_video_id: Optional[str] = None
    youtube_url: Optional[str] = None
    publish_status: str = "PENDING"
    
    # Execution Tracking
    error: Optional[str] = None
    logs: List[Dict[str, Any]] = Field(default_factory=list)
