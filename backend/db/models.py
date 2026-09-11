import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    daily_credit_limit = Column(Float, default=100.0)
    monthly_credit_limit = Column(Float, default=2000.0)
    credits_balance = Column(Float, default=500.0)
    plan_tier = Column(String(50), default="STARTER") # FREE_TRIAL, STARTER, PRO, AGENCY
    subscription_status = Column(String(50), default="ACTIVE") # ACTIVE, PAST_DUE, CANCELED, TRIAL
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    channels = relationship("YouTubeChannel", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageLedger", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("PaymentTransaction", back_populates="user", cascade="all, delete-orphan")

class YouTubeChannel(Base):
    __tablename__ = "youtube_channels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    youtube_channel_id = Column(String(100), nullable=True, index=True)
    channel_name = Column(String(200), nullable=True)
    channel_thumbnail = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    encrypted_access_token = Column(Text, nullable=True)
    encrypted_refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    is_connected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="channels")
    profile = relationship("ChannelAutomationProfile", back_populates="channel", uselist=False, cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="channel")

    @property
    def access_token_encrypted(self):
        return self.encrypted_access_token

    @access_token_encrypted.setter
    def access_token_encrypted(self, val):
        self.encrypted_access_token = val

    @property
    def refresh_token_encrypted(self):
        return self.encrypted_refresh_token

    @refresh_token_encrypted.setter
    def refresh_token_encrypted(self, val):
        self.encrypted_refresh_token = val

    @property
    def name(self):
        return self.channel_name

    @name.setter
    def name(self, val):
        self.channel_name = val

# Backward compatibility alias
Channel = YouTubeChannel

class ChannelAutomationProfile(Base):
    __tablename__ = "channel_automation_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("youtube_channels.id"), nullable=False, unique=True, index=True)
    niche = Column(String(100), default="Kids Cartoon Stories")
    sub_niche = Column(String(100), default="Hindi Animated Stories")
    language = Column(String(50), default="Hindi")
    target_audience = Column(String(100), default="Kids 3-10")
    content_style = Column(String(100), default="Vibrant 3D Animation")
    visual_mode = Column(String(50), default="FULL_ANIMATION") # IMAGE_MOTION, FULL_ANIMATION, HYBRID, AUTO
    video_format = Column(String(20), default="SHORT") # SHORT, LONG, BOTH
    videos_per_day = Column(Integer, default=2)
    publish_times = Column(JSON, default=["10:00", "18:00"]) # Array of HH:MM strings
    automation_enabled = Column(Boolean, default=True)
    auto_publish = Column(Boolean, default=True)
    voice_style = Column(String(50), default="hi-IN-SwaraNeural")
    character_universe = Column(String(100), default="Chintu Universe")
    timezone = Column(String(50), default="Asia/Kolkata")
    days_of_week = Column(JSON, default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    minimum_gap_between_uploads_hours = Column(Integer, default=4)
    content_rules = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    channel = relationship("YouTubeChannel", back_populates="profile")

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    channel_id = Column(Integer, ForeignKey("youtube_channels.id"), nullable=True, index=True)
    character_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    species = Column(String(50), nullable=False)
    personality = Column(Text, nullable=False)
    physical_description = Column(Text, nullable=False)
    clothing = Column(Text, nullable=True)
    color_palette = Column(String(200), nullable=True)
    visual_prompt_base = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    voice_config = Column(JSON, nullable=False)
    # Character Reference Asset Registry
    master_ref_image = Column(Text, nullable=True)
    front_view_img = Column(Text, nullable=True)
    side_view_img = Column(Text, nullable=True)
    three_quarter_view_img = Column(Text, nullable=True)
    expression_refs = Column(JSON, nullable=True)
    pose_refs = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ContentMemory(Base):
    __tablename__ = "content_memory"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("youtube_channels.id"), nullable=False, index=True)
    topic_title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    conflict_type = Column(String(100), nullable=True)
    resolution_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ContentIdea(Base):
    __tablename__ = "content_ideas"

    id = Column(Integer, primary_key=True, index=True)
    topic_title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    target_audience = Column(String(100), default="Kids 3-10")
    reasoning = Column(Text, nullable=True)
    is_selected = Column(Boolean, default=False)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("content_ideas.id"), nullable=True)
    video_type = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    script_json = Column(JSON, nullable=False)
    moral = Column(Text, nullable=True)
    estimated_duration = Column(Integer, default=60)
    qa_score = Column(Float, default=0.0)
    qa_feedback = Column(Text, nullable=True)
    retries_count = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)
    script_generated_by_fallback = Column(Boolean, default=False)
    provider_used = Column(String(50), default="GEMINI_LIVE")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    scenes = relationship("Scene", back_populates="script", cascade="all, delete-orphan")

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    scene_number = Column(Integer, nullable=False)
    duration_seconds = Column(Float, default=5.0)
    location = Column(String(255), nullable=True)
    characters_present = Column(JSON, nullable=True)
    visual_prompt = Column(Text, nullable=False)
    camera_direction = Column(String(100), nullable=True)
    character_actions = Column(Text, nullable=True)
    dialogue = Column(Text, nullable=True)
    speaker = Column(String(50), nullable=True)
    audio_mood = Column(String(50), nullable=True)
    image_url = Column(Text, nullable=True)
    audio_url = Column(Text, nullable=True)
    is_placeholder = Column(Boolean, default=False)
    is_fallback = Column(Boolean, default=False)
    provider_name = Column(String(50), default="image_provider")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    script = relationship("Script", back_populates="scenes")

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    channel_id = Column(Integer, ForeignKey("youtube_channels.id"), nullable=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=True)
    video_type = Column(String(20), nullable=False)
    visual_mode = Column(String(50), default="IMAGE_MOTION")
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    hashtags = Column(JSON, nullable=True)
    category_id = Column(String(20), default="15")
    is_made_for_kids = Column(Boolean, default=True)
    publish_mode = Column(String(20), default="UNLISTED")
    video_path = Column(Text, nullable=True)
    thumbnail_path = Column(Text, nullable=True)
    youtube_video_id = Column(String(100), nullable=True)
    youtube_url = Column(String(255), nullable=True)
    status = Column(String(50), default="PENDING")
    verification_status = Column(String(50), default="TESTED_WITH_FALLBACK")
    qa_passed = Column(Boolean, default=False)
    production_gate_passed = Column(Boolean, default=False)
    is_placeholder_assets = Column(Boolean, default=False)
    production_gate_details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    channel = relationship("YouTubeChannel", back_populates="videos")
    assets = relationship("VideoAsset", back_populates="video", cascade="all, delete-orphan")

class VideoAsset(Base):
    __tablename__ = "video_assets"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    asset_type = Column(String(50), nullable=False) # IMAGE, ANIMATION_CLIP, AUDIO, MUSIC, SUBTITLE, RENDER, THUMBNAIL
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, default=0)
    provider_name = Column(String(100), nullable=False, default="unknown")
    provider_type = Column(String(50), nullable=False, default="ai") # ai, animation, tts, ffmpeg, canvas_fallback
    is_fallback = Column(Boolean, default=False)
    is_placeholder = Column(Boolean, default=False)
    generation_job_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    video = relationship("Video", back_populates="assets")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    channel_id = Column(Integer, ForeignKey("youtube_channels.id"), nullable=True, index=True)
    job_type = Column(String(50), nullable=False)
    video_type = Column(String(20), nullable=True)
    visual_mode = Column(String(50), default="IMAGE_MOTION")
    status = Column(String(50), default="PENDING") # PENDING, QUEUED, RUNNING, COMPLETED, FAILED, FAILED_SCRIPT_QUALITY, FAILED_IMAGE_GENERATION, FAILED_ANIMATION_GENERATION, FAILED_ANIMATION_QUALITY, FAILED_RENDERING, FAILED_UPLOAD, INSUFFICIENT_CREDITS
    checkpoint_stage = Column(String(100), default="INIT")
    checkpoint_data = Column(JSON, nullable=True)
    estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    current_step = Column(String(100), nullable=True)
    total_steps = Column(Integer, default=14)
    progress_percentage = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    result_data = Column(JSON, nullable=True)
    idempotency_key = Column(String(255), unique=True, nullable=True, index=True)
    upload_idempotency_key = Column(String(255), unique=True, nullable=True, index=True)
    youtube_video_id = Column(String(100), nullable=True, index=True)
    upload_status = Column(String(50), default="NOT_STARTED") # NOT_STARTED, IN_PROGRESS, UPLOADED, FAILED
    upload_attempts = Column(Integer, default=0)
    priority = Column(String(20), default="DEFAULT") # HIGH, DEFAULT, LOW
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="jobs")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")

class JobLog(Base):
    __tablename__ = "job_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), ForeignKey("jobs.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    log_level = Column(String(20), default="INFO")
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    job = relationship("Job", back_populates="logs")

class AnimationAsset(Base):
    __tablename__ = "animation_assets"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), ForeignKey("jobs.id"), nullable=False, index=True)
    scene_number = Column(Integer, nullable=False)
    video_clip_path = Column(Text, nullable=False)
    provider_name = Column(String(100), nullable=False)
    motion_score = Column(Float, default=0.0)
    frozen_frame_pct = Column(Float, default=0.0)
    duplicate_frame_ratio = Column(Float, default=0.0)
    character_consistency_score = Column(Float, default=1.0)
    qa_passed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class UsageLedger(Base):
    __tablename__ = "usage_ledger"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("youtube_channels.id"), nullable=True, index=True)
    job_id = Column(String(100), nullable=True, index=True)
    provider_name = Column(String(100), nullable=False)
    model_name = Column(String(100), nullable=False)
    operation_type = Column(String(50), nullable=False) # IMAGE_GEN, ANIMATION_GEN, SCRIPT_GEN, TTS_GEN
    estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    credits_used = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="usage_records")

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("youtube_channels.id"), nullable=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    views = Column(Integer, default=0)
    watch_time_minutes = Column(Float, default=0.0)
    avg_view_duration_seconds = Column(Float, default=0.0)
    likes = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    subscribers_gained = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr_percentage = Column(Float, default=0.0)
    metrics_available = Column(JSON, nullable=True)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

class LearningInsight(Base):
    __tablename__ = "learning_insights"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("youtube_channels.id"), nullable=True, index=True)
    timeframe_days = Column(Integer, default=7)
    best_topics = Column(JSON, nullable=True)
    worst_topics = Column(JSON, nullable=True)
    retention_insights = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id = Column(Integer, primary_key=True, index=True)
    memory_key = Column(String(100), unique=True, nullable=False, index=True)
    memory_value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    category = Column(String(50), default="general")
    is_secret = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_tier = Column(String(50), nullable=False) # STARTER, PRO, AGENCY
    billing_cycle = Column(String(20), default="MONTHLY") # MONTHLY, ANNUAL
    currency = Column(String(10), default="USD") # USD, INR
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="ACTIVE") # ACTIVE, PAST_DUE, CANCELED, EXPIRED
    payment_gateway = Column(String(50), default="STRIPE") # STRIPE, RAZORPAY, MANUAL
    external_subscription_id = Column(String(150), nullable=True, index=True)
    external_customer_id = Column(String(150), nullable=True)
    current_period_start = Column(DateTime, default=datetime.datetime.utcnow)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    gateway = Column(String(50), nullable=False) # STRIPE, RAZORPAY
    transaction_id = Column(String(150), unique=True, nullable=False, index=True)
    order_id = Column(String(150), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(String(50), default="SUCCESS") # PENDING, SUCCESS, FAILED, REFUNDED
    plan_tier = Column(String(50), nullable=False)
    payment_method = Column(String(50), nullable=True) # card, upi, netbanking
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="payments")

