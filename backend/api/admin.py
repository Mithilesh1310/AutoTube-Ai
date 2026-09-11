import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from backend.db.session import get_db
from backend.db.models import User, YouTubeChannel, Job, UsageLedger, Video
from backend.services.provider_capability_registry import provider_capability_registry
from backend.config import settings

from backend.api.auth import get_current_user
from backend.services.observability import metrics_tracker
from fastapi import HTTPException

logger = logging.getLogger(__name__)
admin_router = APIRouter(prefix="/admin", tags=["SaaS Admin & Analytics"])

@admin_router.get("/metrics")
async def get_admin_metrics(current_user: User = Depends(get_current_user)):
    """Returns provider latencies, failure rates, and job durations (Admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required.")
    return metrics_tracker.get_summary()

@admin_router.get("/dashboard")
@admin_router.get("/summary")
async def get_admin_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns platform-wide metrics: channels, spend, queue depth, provider health, and failure rates (Admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required.")
    # Channel counts
    res_chan = await db.execute(select(func.count(YouTubeChannel.id)))
    total_channels = res_chan.scalar() or 0

    # User counts
    res_users = await db.execute(select(func.count(User.id)))
    total_users = res_users.scalar() or 0

    # Total spend & credits used from usage ledger
    res_ledger = await db.execute(
        select(
            func.sum(UsageLedger.actual_cost),
            func.sum(UsageLedger.credits_used)
        )
    )
    total_spend, total_credits = res_ledger.first()
    total_spend = total_spend or 0.0
    total_credits = total_credits or 0.0

    # Job metrics
    res_jobs = await db.execute(select(Job))
    jobs = res_jobs.scalars().all()
    total_jobs = len(jobs)
    running_jobs = sum(1 for j in jobs if j.status == "RUNNING")
    failed_jobs = sum(1 for j in jobs if "FAILED" in (j.status or ""))
    completed_jobs = sum(1 for j in jobs if j.status == "COMPLETED")
    failure_rate = round((failed_jobs / total_jobs * 100), 2) if total_jobs > 0 else 0.0

    # Visual Mode Breakdown
    visual_mode_counts = {
        "IMAGE_MOTION": sum(1 for j in jobs if j.visual_mode == "IMAGE_MOTION"),
        "FULL_ANIMATION": sum(1 for j in jobs if j.visual_mode == "FULL_ANIMATION"),
        "HYBRID": sum(1 for j in jobs if j.visual_mode == "HYBRID"),
        "AUTO": sum(1 for j in jobs if j.visual_mode == "AUTO")
    }

    return {
        "total_users": total_users,
        "total_channels": total_channels,
        "total_jobs": total_jobs,
        "queue_depth": running_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "failure_rate_pct": failure_rate,
        "total_spend_usd": round(total_spend, 4),
        "total_credits_used": round(total_credits, 2),
        "global_emergency_stop": getattr(settings, "GLOBAL_EMERGENCY_STOP", False),
        "visual_mode_breakdown": visual_mode_counts,
        "providers_status": provider_capability_registry.providers
    }

@admin_router.get("/usage-ledger")
async def get_usage_ledger(db: AsyncSession = Depends(get_db)):
    """Retrieve the recent immutable billing and provider calls ledger."""
    res = await db.execute(
        select(UsageLedger).order_by(desc(UsageLedger.timestamp)).limit(50)
    )
    records = res.scalars().all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "channel_id": r.channel_id,
            "job_id": r.job_id,
            "provider_name": r.provider_name,
            "model_name": r.model_name,
            "operation_type": r.operation_type,
            "actual_cost": r.actual_cost,
            "credits_used": r.credits_used,
            "timestamp": str(r.timestamp)
        }
        for r in records
    ]

@admin_router.get("/providers")
async def get_providers():
    """Retrieve real-time provider capabilities and latency metrics."""
    return provider_capability_registry.providers
