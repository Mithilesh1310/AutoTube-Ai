import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "autotube-v1-dev-secret-key-987654321"
    JWT_SECRET: str = "autotube-jwt-secret-key-998877665544332211"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080 # 7 days
    OAUTH_ENCRYPTION_KEY: str = "gAAAAABl-autotube-default-fernet-key-32bytes="

    AGENT_ENABLED: bool = True
    TIMEZONE: str = "Asia/Kolkata"

    GEMINI_API_KEY: str = ""

    DATABASE_URL: str = "sqlite+aiosqlite:///./autotube.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    STORAGE_PROVIDER: str = "local"
    STORAGE_LOCAL_DIR: str = "./storage"
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = "autotube-assets"

    VOICE_PROVIDER: str = "edge_tts"
    VOICE_API_KEY: str = ""
    IMAGE_PROVIDER: str = "huggingface"
    IMAGE_API_KEY: str = ""
    TEST_MODE: bool = False
    VISUAL_PROVIDER: str = "image_kenburns"
    VISUAL_API_KEY: str = ""

    # Pluggable Animation Provider Settings
    ANIMATION_PROVIDER: str = "fal_ai" # fal_ai, replicate, null
    ANIMATION_API_KEY: str = ""
    ANIMATION_FALLBACK_PROVIDER: str = "replicate"

    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_REFRESH_TOKEN: str = ""
    YOUTUBE_REDIRECT_URI: str = "http://localhost:8000/api/v1/youtube/callback"
    YOUTUBE_PUBLISH_MODE: str = "PUBLIC"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    WORKFLOW_GENERATE_TIME: str = "08:00"
    SHORTS_PUBLISH_TIME: str = "10:00"
    LONG_PUBLISH_TIME: str = "18:00"

    # Emergency Controls
    GLOBAL_EMERGENCY_STOP: bool = False

    # SaaS Billing & Payment Gateways (Razorpay)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    RAZORPAY_KEY_ID: str = "rzp_test_TZpxlk94xSaidY"
    RAZORPAY_KEY_SECRET: str = "bMOb4tz31ZSsdLtUkYyySdx8"
    BILLING_SANDBOX_MODE: bool = False


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
