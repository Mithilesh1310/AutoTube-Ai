import asyncio
from sqlalchemy import select
from backend.db.session import engine, AsyncSessionLocal, Base
from backend.db.models import Character, Setting, User, YouTubeChannel, ChannelAutomationProfile
from backend.config import settings

INITIAL_CHARACTERS = [
    {
        "character_id": "chintu",
        "name": "Chintu",
        "species": "Elephant",
        "personality": "Kind, curious, adventurous, sometimes scared but brave",
        "physical_description": "Small cute baby blue elephant with big expressive brown eyes and soft rounded ears.",
        "clothing": "Red bandana neckerchief around neck",
        "color_palette": "Pastel light blue (#7EC8E3), vibrant red accent (#FF3B30)",
        "visual_prompt_base": "3D Pixar style cute baby elephant named Chintu, pastel light blue skin, big expressive brown eyes, wearing a small red bandana neckerchief, friendly smile, children's cartoon 3D render, vibrant lighting, highly detailed",
        "negative_prompt": "scary, dark, realistic elephant, ugly, distorted, grainy, adult elephant",
        "voice_config": {
            "provider": "edge_tts",
            "voice_id": "hi-IN-MadhurNeural",
            "pitch": "+4Hz",
            "rate": "+5%"
        }
    },
    {
        "character_id": "momo",
        "name": "Momo",
        "species": "Monkey",
        "personality": "Funny, energetic, mischievous but helpful and loyal",
        "physical_description": "Energetic young brown monkey with a long curly tail and bright wide smile.",
        "clothing": "Bright yellow sleeveless shirt",
        "color_palette": "Warm brown (#8B5A2B), vivid yellow (#FFCC00)",
        "visual_prompt_base": "3D Pixar style playful young monkey named Momo, warm brown fur, cheerful wide smile, wearing a bright yellow sleeveless shirt, curly long tail, 3D children animation render, colorful background",
        "negative_prompt": "scary, aggressive, dark, realistic monkey, distorted hands, low quality",
        "voice_config": {
            "provider": "edge_tts",
            "voice_id": "hi-IN-MadhurNeural",
            "pitch": "+10Hz",
            "rate": "+15%"
        }
    },
    {
        "character_id": "titu",
        "name": "Titu",
        "species": "Rabbit",
        "personality": "Intelligent, calm, smart problem solver, loves reading",
        "physical_description": "Fluffy white rabbit with long upright pink-tinted ears and tiny round reading glasses.",
        "clothing": "Sky blue vest",
        "color_palette": "Pure white (#FFFFFF), sky blue (#4A90E2)",
        "visual_prompt_base": "3D Pixar style smart fluffy white rabbit named Titu, long upright pink-inner ears, tiny round spectacles, wearing a sky blue vest, intelligent calm expression, 3D kids animation, soft lighting",
        "negative_prompt": "scary, wild rabbit, distorted face, blurry, low resolution",
        "voice_config": {
            "provider": "edge_tts",
            "voice_id": "hi-IN-SwaraNeural",
            "pitch": "+2Hz",
            "rate": "+0%"
        }
    },
    {
        "character_id": "mithu",
        "name": "Mithu",
        "species": "Parrot",
        "personality": "Funny, talkative, cheerful, makes jokes and laughs",
        "physical_description": "Vibrant emerald green parrot with a ruby red beak and bright yellow wing tips.",
        "clothing": "Small orange bow tie",
        "color_palette": "Emerald green (#2ECC71), ruby red (#E74C3C), orange (#E67E22)",
        "visual_prompt_base": "3D Pixar style funny colorful parrot named Mithu, emerald green feathers, shiny red beak, orange bow tie, talkative cheerful open beak expression, 3D kids cartoon render",
        "negative_prompt": "scary, dark, realistic bird, dirty feathers, ugly beak",
        "voice_config": {
            "provider": "edge_tts",
            "voice_id": "hi-IN-MadhurNeural",
            "pitch": "+15Hz",
            "rate": "+20%"
        }
    },
    {
        "character_id": "baba_turtle",
        "name": "Baba Turtle",
        "species": "Turtle",
        "personality": "Old wise turtle, calm, patient, teaches valuable moral lessons",
        "physical_description": "Elderly wise green turtle with a beautifully carved brown patterned shell.",
        "clothing": "Tiny reading glasses on nose, small wooden walking stick",
        "color_palette": "Forest green (#27AE60), dark wood brown (#5D4037)",
        "visual_prompt_base": "3D Pixar style wise old turtle named Baba Turtle, gentle wrinkled face, carved patterned dark brown shell, tiny reading glasses, holding wooden walking stick, peaceful warm smile, 3D children render",
        "negative_prompt": "scary, sea turtle, dirty shell, aggressive, low quality",
        "voice_config": {
            "provider": "edge_tts",
            "voice_id": "hi-IN-MadhurNeural",
            "pitch": "-10Hz",
            "rate": "-15%"
        }
    }
]

INITIAL_SETTINGS = [
    {"key": "AGENT_ENABLED", "value": "true", "category": "general"},
    {"key": "PUBLISH_MODE", "value": "UNLISTED", "category": "youtube"},
    {"key": "VOICE_PROVIDER", "value": "edge_tts", "category": "voice"},
    {"key": "IMAGE_PROVIDER", "value": "huggingface", "category": "image"},
    {"key": "VISUAL_PROVIDER", "value": "image_kenburns", "category": "visual"},
    {"key": "ANIMATION_PROVIDER", "value": "fal_ai", "category": "animation"},
    {"key": "STORAGE_PROVIDER", "value": "local", "category": "storage"},
    {"key": "WORKFLOW_GENERATE_TIME", "value": "08:00", "category": "schedule"},
    {"key": "SHORTS_PUBLISH_TIME", "value": "10:00", "category": "schedule"},
    {"key": "LONG_PUBLISH_TIME", "value": "18:00", "category": "schedule"}
]

from sqlalchemy import text

async def _migrate_sqlite_columns(conn):
    def sync_migrate(sync_conn):
        migrations = [
            ("users", "is_active", "BOOLEAN DEFAULT 1"),
            ("users", "is_admin", "BOOLEAN DEFAULT 0"),
            ("users", "daily_credit_limit", "FLOAT DEFAULT 100.0"),
            ("users", "monthly_credit_limit", "FLOAT DEFAULT 2000.0"),
            ("users", "credits_balance", "FLOAT DEFAULT 500.0"),
            ("users", "plan_tier", "VARCHAR(50) DEFAULT 'STARTER'"),
            ("users", "subscription_status", "VARCHAR(50) DEFAULT 'ACTIVE'"),
            ("characters", "user_id", "INTEGER"),
            ("characters", "channel_id", "INTEGER"),
            ("characters", "clothing", "TEXT"),
            ("characters", "color_palette", "VARCHAR(200)"),
            ("characters", "negative_prompt", "TEXT"),
            ("characters", "master_ref_image", "TEXT"),
            ("characters", "front_view_img", "TEXT"),
            ("characters", "side_view_img", "TEXT"),
            ("characters", "three_quarter_view_img", "TEXT"),
            ("characters", "expression_refs", "JSON"),
            ("characters", "pose_refs", "JSON"),
            ("videos", "user_id", "INTEGER"),
            ("videos", "channel_id", "INTEGER"),
            ("videos", "visual_mode", "VARCHAR(50) DEFAULT 'IMAGE_MOTION'"),
            ("videos", "verification_status", "VARCHAR(50) DEFAULT 'TESTED_WITH_FALLBACK'"),
            ("videos", "qa_passed", "BOOLEAN DEFAULT 0"),
            ("videos", "production_gate_passed", "BOOLEAN DEFAULT 0"),
            ("videos", "is_placeholder_assets", "BOOLEAN DEFAULT 0"),
            ("videos", "production_gate_details", "JSON"),
            ("jobs", "user_id", "INTEGER"),
            ("jobs", "channel_id", "INTEGER"),
            ("jobs", "visual_mode", "VARCHAR(50) DEFAULT 'IMAGE_MOTION'"),
            ("jobs", "checkpoint_stage", "VARCHAR(100) DEFAULT 'INIT'"),
            ("jobs", "checkpoint_data", "JSON"),
            ("jobs", "estimated_cost", "FLOAT DEFAULT 0.0"),
            ("jobs", "actual_cost", "FLOAT DEFAULT 0.0"),
            ("jobs", "idempotency_key", "VARCHAR(255)"),
            ("jobs", "upload_idempotency_key", "VARCHAR(255)"),
            ("jobs", "youtube_video_id", "VARCHAR(100)"),
            ("jobs", "upload_status", "VARCHAR(50) DEFAULT 'NOT_STARTED'"),
            ("jobs", "upload_attempts", "INTEGER DEFAULT 0"),
            ("jobs", "priority", "VARCHAR(20) DEFAULT 'DEFAULT'"),
            ("channel_automation_profiles", "timezone", "VARCHAR(50) DEFAULT 'Asia/Kolkata'"),
            ("channel_automation_profiles", "days_of_week", "JSON"),
            ("channel_automation_profiles", "minimum_gap_between_uploads_hours", "INTEGER DEFAULT 4"),
            ("animation_assets", "character_consistency_score", "FLOAT DEFAULT 1.0"),
        ]
        for table, col, col_type in migrations:
            try:
                sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
            except Exception:
                pass # Column already exists or table doesn't exist yet
    await conn.run_sync(sync_migrate)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_sqlite_columns(conn)

    async with AsyncSessionLocal() as session:
        # Seed Demo User
        res_user = await session.execute(select(User).where(User.email == "demo@autotube.ai"))
        demo_user = res_user.scalar_one_or_none()
        if not demo_user:
            demo_user = User(
                username="demouser",
                email="demo@autotube.ai",
                password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeg6Lruj3vjPGga31lW", # "password"
                is_admin=True,
                credits_balance=1000.0
            )
            session.add(demo_user)
            await session.flush()

        # Seed Primary Channel
        res_chan = await session.execute(select(YouTubeChannel).where(YouTubeChannel.user_id == demo_user.id))
        primary_chan = res_chan.scalar_one_or_none()
        if not primary_chan:
            primary_chan = YouTubeChannel(
                user_id=demo_user.id,
                channel_name="AutoTube Kids Stories",
                description="Default Hindi Animated Kids Cartoon Channel",
                is_connected=True
            )
            session.add(primary_chan)
            await session.flush()

            # Seed Profile
            profile = ChannelAutomationProfile(
                user_id=demo_user.id,
                channel_id=primary_chan.id,
                niche="Kids Cartoon Stories",
                sub_niche="Hindi Animated Stories",
                visual_mode="FULL_ANIMATION",
                video_format="BOTH",
                videos_per_day=2,
                publish_times=["10:00", "18:00"],
                automation_enabled=True
            )
            session.add(profile)

        # Seed Characters
        for char_data in INITIAL_CHARACTERS:
            result = await session.execute(
                select(Character).where(Character.character_id == char_data["character_id"])
            )
            existing = result.scalar_one_or_none()
            if not existing:
                char_obj = Character(**char_data)
                session.add(char_obj)

        # Seed Settings
        for setting_data in INITIAL_SETTINGS:
            result = await session.execute(
                select(Setting).where(Setting.key == setting_data["key"])
            )
            existing = result.scalar_one_or_none()
            if not existing:
                setting_obj = Setting(**setting_data)
                session.add(setting_obj)

        await session.commit()
    print("[OK] Database tables created, Demo User, Channel Profile & Character Bible initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
