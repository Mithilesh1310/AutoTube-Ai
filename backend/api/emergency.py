import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from backend.db.session import get_db
from backend.db.models import Job, User
from backend.config import settings
from backend.services.emergency_controls import emergency_control_service
from backend.api.auth import get_current_user

logger = logging.getLogger(__name__)
emergency_router = APIRouter(prefix="/emergency", tags=["Emergency Controls & Safety"])

class GlobalStopRequest(BaseModel):
    enabled: bool
    reason: Optional[str] = "Emergency stop initiated by operator"

@emergency_router.get("/status")
async def get_emergency_status(db: AsyncSession = Depends(get_db)):
    """Check system safety status, global stop flag, and currently running jobs."""
    global_stop = getattr(settings, "GLOBAL_EMERGENCY_STOP", False)

    res_jobs = await db.execute(
        select(Job).where(Job.status == "RUNNING")
    )
    running_jobs = res_jobs.scalars().all()

    return {
        "global_emergency_stop": global_stop,
        "running_jobs_count": len(running_jobs),
        "running_jobs": [
            {
                "id": j.id,
                "current_step": j.current_step,
                "job_type": j.job_type,
                "visual_mode": j.visual_mode,
                "progress_percentage": j.progress_percentage,
                "created_at": str(j.created_at)
            }
            for j in running_jobs
        ],
        "system_status": "LOCKED" if global_stop else ("BUSY" if running_jobs else "NORMAL")
    }

@emergency_router.post("/stop-job/{job_id}")
async def stop_specific_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Instantly cancel an active or queued generation job enforcing tenant ownership."""
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.user_id and job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized: cannot cancel another user's job.")

    await emergency_control_service.stop_job(job_id)
    return {
        "status": "success",
        "job_id": job_id,
        "message": f"Job {job_id} cancelled via emergency kill switch."
    }

@emergency_router.post("/global-stop")
async def toggle_global_stop(
    req: GlobalStopRequest,
    current_user: User = Depends(get_current_user)
):
    """Toggle the master SaaS kill switch (Admin Only). Halts all active and pending AI generation."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden: Only SaaS Administrators can toggle the master kill switch.")

    await emergency_control_service.global_emergency_stop(enabled=req.enabled)
    action = "ENGAGED" if req.enabled else "DISENGAGED"
    logger.warning(f"[EmergencyControl] Master kill switch {action} by admin '{current_user.username}'. Reason: {req.reason}")
    return {
        "status": "success",
        "global_emergency_stop": req.enabled,
        "message": f"Master kill switch {action}."
    }
