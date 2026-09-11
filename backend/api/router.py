import uuid
import re
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, or_
from backend.db.session import get_db
from backend.db.models import Video, Job, JobLog, Character, Analytics, LearningInsight, Setting, YouTubeChannel, ChannelAutomationProfile, User
from backend.config import settings
from backend.agents.orchestrator import run_pipeline
from backend.services.character_bible import character_bible
from backend.services.analytics_service import analytics_service
from backend.api.auth import get_current_user

logger = logging.getLogger(__name__)
api_router = APIRouter(prefix="/api/v1")

from sqlalchemy import text
from backend.tasks.worker import job_queue

@api_router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": "AutoTube V1 SaaS",
        "agent_enabled": settings.AGENT_ENABLED,
        "global_emergency_stop": getattr(settings, "GLOBAL_EMERGENCY_STOP", False)
    }

@api_router.get("/health/db")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Verifies active database connection and measures round-trip query latency."""
    import time
    start = time.time()
    try:
        await db.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start) * 1000, 2)
        return {
            "status": "HEALTHY",
            "dialect": db.bind.dialect.name if hasattr(db, "bind") and db.bind else "sqlite",
            "latency_ms": latency_ms
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {e}")

@api_router.get("/health/queue")
async def queue_health_check():
    """Returns background worker queue depth and status."""
    return job_queue.get_metrics()

@api_router.get("/dashboard")
async def get_dashboard_summary(
    channel_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Total videos (scoped to user)
    video_query = select(Video)
    if not current_user.is_admin:
        video_query = video_query.where(Video.user_id == current_user.id)
    if channel_id:
        video_query = video_query.where(Video.channel_id == channel_id)
    res_videos = await db.execute(video_query)
    videos = res_videos.scalars().all()
    
    total_videos = len(videos)
    shorts_count = sum(1 for v in videos if v.video_type == "SHORT")
    long_count = sum(1 for v in videos if v.video_type == "LONG")
    
    # Active/Latest Job - prioritize currently running workflow
    job_query = select(Job)
    if not current_user.is_admin:
        job_query = job_query.where(Job.user_id == current_user.id)
    if channel_id:
        job_query = job_query.where(Job.channel_id == channel_id)
    
    res_running = await db.execute(job_query.where(Job.status == "RUNNING").order_by(desc(Job.created_at)).limit(1))
    running_job = res_running.scalar_one_or_none()

    res_latest = await db.execute(job_query.order_by(desc(Job.created_at)).limit(1))
    latest_job = res_latest.scalar_one_or_none()

    # Channels status (scoped to user)
    chan_query = select(YouTubeChannel).where(YouTubeChannel.is_connected == True)
    if not current_user.is_admin:
        chan_query = chan_query.where(YouTubeChannel.user_id == current_user.id)
    res_chan = await db.execute(chan_query)
    connected_channels = res_chan.scalars().all()
    active_channel = next((c for c in connected_channels if c.id == channel_id), connected_channels[0] if connected_channels else None)

    active_or_latest = running_job if running_job else latest_job

    return {
        "agent_status": "PAUSED" if getattr(settings, "GLOBAL_EMERGENCY_STOP", False) else ("ACTIVE" if settings.AGENT_ENABLED else "PAUSED"),
        "agent_enabled": settings.AGENT_ENABLED,
        "global_emergency_stop": getattr(settings, "GLOBAL_EMERGENCY_STOP", False),
        "total_videos": total_videos,
        "shorts_generated": shorts_count,
        "long_videos_generated": long_count,
        "total_connected_channels": len(connected_channels),
        "channel_connected": bool(active_channel),
        "channel_name": active_channel.channel_name if active_channel else "No Channel Connected",
        "channel_id": active_channel.id if active_channel else None,
        "publish_mode": settings.YOUTUBE_PUBLISH_MODE,
        "is_job_active": bool(running_job),
        "latest_job": {
            "id": active_or_latest.id if active_or_latest else None,
            "status": active_or_latest.status if active_or_latest else "IDLE",
            "current_step": active_or_latest.current_step if active_or_latest else "IDLE",
            "visual_mode": active_or_latest.visual_mode if active_or_latest else "IMAGE_MOTION",
            "checkpoint_stage": active_or_latest.checkpoint_stage if active_or_latest else "INIT",
            "progress": active_or_latest.progress_percentage if active_or_latest else 0.0,
            "created_at": str(active_or_latest.created_at) if active_or_latest else None
        } if active_or_latest else None
    }

def _normalize_media_url(path: Optional[str], youtube_video_id: Optional[str] = None, is_thumb: bool = False) -> str:
    if not path:
        if is_thumb and youtube_video_id and not youtube_video_id.startswith(("yt_demo", "NO_UPLOAD", "LOCAL_TEST")):
            return f"https://i.ytimg.com/vi/{youtube_video_id}/hqdefault.jpg"
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    clean = path.replace("\\", "/")
    clean = re.sub(r"^\.?/?storage/", "/storage/", clean)
    if not clean.startswith("/"):
        clean = "/" + clean
    return clean

@api_router.get("/videos")
async def list_videos(
    channel_id: Optional[int] = None,
    visual_mode: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Video).order_by(desc(Video.created_at))
    if not current_user.is_admin:
        query = query.where(Video.user_id == current_user.id)
    if channel_id:
        query = query.where(Video.channel_id == channel_id)
    if visual_mode:
        query = query.where(Video.visual_mode == visual_mode)
    
    result = await db.execute(query)
    videos = result.scalars().all()
    return [
        {
            "id": v.id,
            "channel_id": v.channel_id,
            "title": v.title,
            "video_type": v.video_type,
            "visual_mode": v.visual_mode or "IMAGE_MOTION",
            "status": v.status,
            "publish_mode": v.publish_mode,
            "video_path": _normalize_media_url(v.video_path),
            "thumbnail_path": _normalize_media_url(v.thumbnail_path, v.youtube_video_id, is_thumb=True),
            "youtube_video_id": v.youtube_video_id,
            "youtube_url": v.youtube_url or (f"https://youtu.be/{v.youtube_video_id}" if v.youtube_video_id and not v.youtube_video_id.startswith(("yt_demo", "NO_UPLOAD", "LOCAL_TEST")) else None),
            "qa_passed": v.qa_passed,
            "created_at": str(v.created_at)
        }
        for v in videos
    ]

@api_router.get("/videos/{video_id}")
async def get_video_detail(video_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return {
        "id": video.id,
        "channel_id": video.channel_id,
        "title": video.title,
        "video_type": video.video_type,
        "visual_mode": video.visual_mode or "IMAGE_MOTION",
        "status": video.status,
        "publish_mode": video.publish_mode,
        "video_path": _normalize_media_url(video.video_path),
        "thumbnail_path": _normalize_media_url(video.thumbnail_path, video.youtube_video_id, is_thumb=True),
        "youtube_video_id": video.youtube_video_id,
        "youtube_url": video.youtube_url or (f"https://youtu.be/{video.youtube_video_id}" if video.youtube_video_id and not video.youtube_video_id.startswith(("yt_demo", "NO_UPLOAD", "LOCAL_TEST")) else None),
        "qa_passed": video.qa_passed,
        "created_at": str(video.created_at)
    }

@api_router.get("/characters")
async def list_characters():
    return await character_bible.get_all_characters()

@api_router.get("/jobs")
async def list_jobs(
    channel_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Job).order_by(desc(Job.created_at)).limit(30)
    if not current_user.is_admin:
        query = query.where(Job.user_id == current_user.id)
    if channel_id:
        query = query.where(Job.channel_id == channel_id)
    result = await db.execute(query)
    jobs = result.scalars().all()
    return [
        {
            "id": j.id,
            "channel_id": j.channel_id,
            "job_type": j.job_type,
            "visual_mode": j.visual_mode,
            "status": j.status,
            "checkpoint_stage": j.checkpoint_stage,
            "current_step": j.current_step,
            "progress_percentage": j.progress_percentage,
            "estimated_cost": j.estimated_cost,
            "actual_cost": j.actual_cost,
            "error_message": j.error_message,
            "created_at": str(j.created_at)
        }
        for j in jobs
    ]

@api_router.get("/jobs/{job_id}")
async def get_job_detail(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.user_id and job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized: cannot access another user's job.")

    return {
        "id": job.id,
        "channel_id": job.channel_id,
        "user_id": job.user_id,
        "job_type": job.job_type,
        "visual_mode": job.visual_mode,
        "status": job.status,
        "checkpoint_stage": job.checkpoint_stage,
        "current_step": job.current_step,
        "progress_percentage": job.progress_percentage,
        "estimated_cost": job.estimated_cost,
        "actual_cost": job.actual_cost,
        "error_message": job.error_message,
        "created_at": str(job.created_at)
    }

@api_router.post("/jobs/{job_id}/retry")
async def retry_job_from_checkpoint(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resumes or retries a failed/stuck job from its persisted checkpoint stage via background worker."""
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Tenant isolation
    if job.user_id and job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized: cannot retry another user's job.")

    job.status = "QUEUED"
    job.error_message = None
    await db.commit()

    # Enqueue into high-priority background worker queue
    await job_queue.enqueue_job(
        job_id=job.id,
        task_type=job.job_type or "DAILY_WORKFLOW",
        user_id=job.user_id or current_user.id,
        channel_id=job.channel_id,
        visual_mode=job.visual_mode or "IMAGE_MOTION",
        priority="HIGH"
    )

    return {
        "status": "QUEUED",
        "job_id": job.id,
        "checkpoint_stage": job.checkpoint_stage,
        "message": f"Job {job.id} enqueued for resumption from checkpoint {job.checkpoint_stage}."
    }

@api_router.get("/logs")
async def list_logs(job_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(JobLog).order_by(desc(JobLog.timestamp)).limit(100)
    if job_id:
        query = query.where(JobLog.job_id == job_id)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "job_id": l.job_id,
            "agent_name": l.agent_name,
            "log_level": l.log_level,
            "message": l.message,
            "timestamp": str(l.timestamp)
        }
        for l in logs
    ]

@api_router.get("/analytics")
async def get_analytics_summary():
    return await analytics_service.get_real_channel_analytics()

@api_router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting))
    settings_list = result.scalars().all()
    db_dict = {s.key: s.value for s in settings_list}
    
    # Merge with config.py / .env defaults
    merged = {
        "AGENT_ENABLED": db_dict.get("AGENT_ENABLED") or str(settings.AGENT_ENABLED).lower(),
        "PUBLISH_MODE": db_dict.get("PUBLISH_MODE") or settings.YOUTUBE_PUBLISH_MODE,
        "YOUTUBE_PUBLISH_MODE": db_dict.get("YOUTUBE_PUBLISH_MODE") or settings.YOUTUBE_PUBLISH_MODE,
        "VOICE_PROVIDER": db_dict.get("VOICE_PROVIDER") or settings.VOICE_PROVIDER,
        "IMAGE_PROVIDER": db_dict.get("IMAGE_PROVIDER") or settings.IMAGE_PROVIDER,
        "VISUAL_PROVIDER": db_dict.get("VISUAL_PROVIDER") or settings.VISUAL_PROVIDER,
        "STORAGE_PROVIDER": db_dict.get("STORAGE_PROVIDER") or settings.STORAGE_PROVIDER,
        "WORKFLOW_GENERATE_TIME": db_dict.get("WORKFLOW_GENERATE_TIME") or settings.WORKFLOW_GENERATE_TIME,
        "SHORTS_PUBLISH_TIME": db_dict.get("SHORTS_PUBLISH_TIME") or settings.SHORTS_PUBLISH_TIME,
        "LONG_PUBLISH_TIME": db_dict.get("LONG_PUBLISH_TIME") or settings.LONG_PUBLISH_TIME,
        "ANIMATION_PROVIDER": db_dict.get("ANIMATION_PROVIDER") or settings.ANIMATION_PROVIDER,
        "GEMINI_API_KEY": db_dict.get("GEMINI_API_KEY") or settings.GEMINI_API_KEY,
        "YOUTUBE_CLIENT_ID": db_dict.get("YOUTUBE_CLIENT_ID") or settings.YOUTUBE_CLIENT_ID,
        "YOUTUBE_CLIENT_SECRET": db_dict.get("YOUTUBE_CLIENT_SECRET") or settings.YOUTUBE_CLIENT_SECRET,
        "YOUTUBE_REFRESH_TOKEN": db_dict.get("YOUTUBE_REFRESH_TOKEN") or settings.YOUTUBE_REFRESH_TOKEN,
    }
    return merged

@api_router.put("/settings")
async def update_settings(payload: Dict[str, str], db: AsyncSession = Depends(get_db)):
    for key, val in payload.items():
        result = await db.execute(select(Setting).where(Setting.key == key))
        existing = result.scalar_one_or_none()
        if existing:
            existing.value = val
        else:
            new_setting = Setting(key=key, value=val)
            db.add(new_setting)
        
        if key in ["PUBLISH_MODE", "YOUTUBE_PUBLISH_MODE"]:
            settings.YOUTUBE_PUBLISH_MODE = val
        elif key == "YOUTUBE_REFRESH_TOKEN":
            settings.YOUTUBE_REFRESH_TOKEN = val.strip() if val else ""
            if val and val.strip():
                from backend.services.security import encrypt_token
                enc = encrypt_token(val.strip())
                chan_res = await db.execute(select(YouTubeChannel).where(YouTubeChannel.id == 1))
                chan1 = chan_res.scalar_one_or_none()
                if chan1:
                    chan1.encrypted_refresh_token = enc
                    chan1.is_connected = True
        elif key == "YOUTUBE_CLIENT_ID":
            settings.YOUTUBE_CLIENT_ID = val.strip() if val else ""
        elif key == "YOUTUBE_CLIENT_SECRET":
            settings.YOUTUBE_CLIENT_SECRET = val.strip() if val else ""
        elif key == "GEMINI_API_KEY":
            settings.GEMINI_API_KEY = val.strip() if val else ""
    await db.commit()
    return {"status": "success", "message": "Settings updated."}

@api_router.post("/workflow/run")
async def trigger_workflow(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    video_type = payload.get("video_type", "DAILY_WORKFLOW")
    visual_mode = payload.get("visual_mode")
    channel_id = payload.get("channel_id")
    user_id = current_user.id
    priority = payload.get("priority", "DEFAULT")

    # If no channel_id provided, pick user's primary connected channel
    if not channel_id:
        chan_res = await db.execute(
            select(YouTubeChannel).where(
                YouTubeChannel.user_id == user_id,
                YouTubeChannel.is_connected == True
            ).limit(1)
        )
        chan = chan_res.scalar_one_or_none()
        if chan:
            channel_id = chan.id

    # If visual_mode not specified or AUTO, infer from channel automation profile
    if not visual_mode or visual_mode in ["AUTO", "DEFAULT"]:
        if channel_id:
            prof_res = await db.execute(select(ChannelAutomationProfile).where(ChannelAutomationProfile.channel_id == channel_id))
            prof = prof_res.scalar_one_or_none()
            if prof and prof.visual_mode and prof.visual_mode != "AUTO":
                visual_mode = prof.visual_mode
        if not visual_mode or visual_mode in ["AUTO", "DEFAULT"]:
            visual_mode = "IMAGE_MOTION"

    # Validate channel ownership if channel_id provided
    if channel_id:
        chan_res = await db.execute(
            select(YouTubeChannel).where(
                YouTubeChannel.id == channel_id,
                YouTubeChannel.user_id == user_id
            )
        )
        if not chan_res.scalar_one_or_none() and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Unauthorized: cannot launch jobs on another user's channel.")

    job_id = f"job_{uuid.uuid4().hex[:8]}"

    # Offload to dedicated background worker queue
    await job_queue.enqueue_job(
        job_id=job_id,
        task_type=video_type,
        user_id=user_id,
        channel_id=channel_id,
        visual_mode=visual_mode,
        priority=priority
    )

    return {
        "status": "QUEUED",
        "job_id": job_id,
        "channel_id": channel_id,
        "visual_mode": visual_mode,
        "video_type": video_type,
        "priority": priority,
        "message": f"Autonomous pipeline enqueued for {video_type} content ({visual_mode} mode)."
    }
