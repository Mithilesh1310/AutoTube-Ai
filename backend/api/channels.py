import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from pydantic import BaseModel
from backend.db.session import get_db
from backend.db.models import YouTubeChannel, ChannelAutomationProfile, User
from backend.api.auth import get_current_user

logger = logging.getLogger(__name__)
channels_router = APIRouter(prefix="/channels", tags=["Channel Management"])

class AutomationProfileUpdate(BaseModel):
    niche: Optional[str] = None
    sub_niche: Optional[str] = None
    language: Optional[str] = None
    target_audience: Optional[str] = None
    content_style: Optional[str] = None
    visual_mode: Optional[str] = None # IMAGE_MOTION, FULL_ANIMATION, HYBRID, AUTO
    video_format: Optional[str] = None # SHORT, LONG, BOTH
    videos_per_day: Optional[int] = None
    publish_times: Optional[List[str]] = None
    automation_enabled: Optional[bool] = None
    auto_publish: Optional[bool] = None
    voice_style: Optional[str] = None
    character_universe: Optional[str] = None

class CreateChannelRequest(BaseModel):
    channel_name: str
    description: Optional[str] = None
    youtube_channel_id: Optional[str] = None
    niche: Optional[str] = "Kids Cartoon Stories"
    visual_mode: Optional[str] = "FULL_ANIMATION"
    video_format: Optional[str] = "BOTH"
    videos_per_day: Optional[int] = 2
    publish_times: Optional[List[str]] = ["10:00", "18:00"]

@channels_router.get("")
async def list_user_channels(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all YouTube channels owned by the user with their automation profiles."""
    result = await db.execute(
        select(YouTubeChannel).where(YouTubeChannel.user_id == current_user.id)
    )
    channels = result.scalars().all()

    output = []
    for ch in channels:
        # Fetch profile
        prof_res = await db.execute(
            select(ChannelAutomationProfile).where(ChannelAutomationProfile.channel_id == ch.id)
        )
        profile = prof_res.scalar_one_or_none()

        output.append({
            "id": ch.id,
            "channel_name": ch.channel_name,
            "youtube_channel_id": ch.youtube_channel_id,
            "description": ch.description,
            "channel_thumbnail": ch.channel_thumbnail,
            "is_connected": ch.is_connected,
            "created_at": str(ch.created_at),
            "profile": {
                "niche": profile.niche if profile else "Kids Cartoon Stories",
                "sub_niche": profile.sub_niche if profile else "Hindi Animated Stories",
                "language": profile.language if profile else "Hindi",
                "target_audience": profile.target_audience if profile else "Kids 3-10",
                "visual_mode": profile.visual_mode if profile else "FULL_ANIMATION",
                "video_format": profile.video_format if profile else "BOTH",
                "videos_per_day": profile.videos_per_day if profile else 2,
                "publish_times": profile.publish_times if profile else ["10:00", "18:00"],
                "automation_enabled": profile.automation_enabled if profile else True,
                "auto_publish": profile.auto_publish if profile else True,
                "voice_style": profile.voice_style if profile else "hi-IN-SwaraNeural",
                "character_universe": profile.character_universe if profile else "Chintu Universe"
            } if profile else None
        })
    return output

@channels_router.post("")
async def create_channel(
    req: CreateChannelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or connect a new channel for the user with an initial automation profile."""
    new_channel = YouTubeChannel(
        user_id=current_user.id,
        channel_name=req.channel_name,
        description=req.description or "AutoTube Autonomous Channel",
        youtube_channel_id=req.youtube_channel_id or f"UC_{req.channel_name.lower().replace(' ', '_')}",
        is_connected=True
    )
    db.add(new_channel)
    await db.flush()

    new_profile = ChannelAutomationProfile(
        user_id=current_user.id,
        channel_id=new_channel.id,
        niche=req.niche or "Kids Cartoon Stories",
        visual_mode=req.visual_mode or "FULL_ANIMATION",
        video_format=req.video_format or "BOTH",
        videos_per_day=req.videos_per_day or 2,
        publish_times=req.publish_times or ["10:00", "18:00"],
        automation_enabled=True,
        auto_publish=True
    )
    db.add(new_profile)
    await db.commit()

    return {
        "status": "success",
        "channel_id": new_channel.id,
        "channel_name": new_channel.channel_name,
        "message": f"Channel '{new_channel.channel_name}' created successfully with visual mode '{req.visual_mode}'."
    }

@channels_router.get("/{channel_id}")
async def get_channel_detail(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get channel details, connection status, and active automation profile."""
    res = await db.execute(
        select(YouTubeChannel).where(
            YouTubeChannel.id == channel_id,
            YouTubeChannel.user_id == current_user.id
        )
    )
    channel = res.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found or unauthorized.")

    prof_res = await db.execute(
        select(ChannelAutomationProfile).where(ChannelAutomationProfile.channel_id == channel.id)
    )
    profile = prof_res.scalar_one_or_none()

    return {
        "id": channel.id,
        "channel_name": channel.channel_name,
        "youtube_channel_id": channel.youtube_channel_id,
        "description": channel.description,
        "channel_thumbnail": channel.channel_thumbnail,
        "is_connected": channel.is_connected,
        "created_at": str(channel.created_at),
        "profile": profile
    }

@channels_router.put("/{channel_id}/automation")
async def update_channel_automation(
    channel_id: int,
    update_data: AutomationProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update automation settings for a channel (visual mode, publishing times, frequency, etc.)."""
    # Verify ownership
    res = await db.execute(
        select(YouTubeChannel).where(
            YouTubeChannel.id == channel_id,
            YouTubeChannel.user_id == current_user.id
        )
    )
    channel = res.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found or unauthorized.")

    prof_res = await db.execute(
        select(ChannelAutomationProfile).where(ChannelAutomationProfile.channel_id == channel_id)
    )
    profile = prof_res.scalar_one_or_none()
    if not profile:
        profile = ChannelAutomationProfile(
            user_id=current_user.id,
            channel_id=channel_id
        )
        db.add(profile)

    data = update_data.model_dump(exclude_unset=True)
    for field, val in data.items():
        if hasattr(profile, field) and val is not None:
            setattr(profile, field, val)

    await db.commit()
    logger.info(f"Updated automation profile for Channel #{channel_id}: {data}")
    return {"status": "success", "message": "Automation profile updated successfully."}

@channels_router.post("/{channel_id}/pause")
async def pause_channel_automation(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pause autonomous scheduled runs for this channel."""
    res = await db.execute(
        select(ChannelAutomationProfile).where(
            ChannelAutomationProfile.channel_id == channel_id,
            ChannelAutomationProfile.user_id == current_user.id
        )
    )
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Channel profile not found.")

    profile.automation_enabled = False
    await db.commit()
    return {"status": "success", "channel_id": channel_id, "automation_enabled": False}

@channels_router.post("/{channel_id}/resume")
async def resume_channel_automation(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resume autonomous scheduled runs for this channel."""
    res = await db.execute(
        select(ChannelAutomationProfile).where(
            ChannelAutomationProfile.channel_id == channel_id,
            ChannelAutomationProfile.user_id == current_user.id
        )
    )
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Channel profile not found.")

    profile.automation_enabled = True
    await db.commit()
    return {"status": "success", "channel_id": channel_id, "automation_enabled": True}

@channels_router.delete("/{channel_id}")
async def delete_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect and delete channel profile."""
    res = await db.execute(
        select(YouTubeChannel).where(
            YouTubeChannel.id == channel_id,
            YouTubeChannel.user_id == current_user.id
        )
    )
    channel = res.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    await db.delete(channel)
    await db.commit()
    return {"status": "success", "message": f"Channel #{channel_id} removed."}
