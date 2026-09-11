import logging
from sqlalchemy import select, update
from backend.db.session import AsyncSessionLocal
from backend.db.models import Job

logger = logging.getLogger(__name__)

class JobRecoveryService:
    """
    Checkpoint-Based Job Recovery:
    Detects crashed or stale jobs on backend startup and enables resuming execution
    from the last valid persisted checkpoint stage without repeating completed expensive steps.
    """
    @staticmethod
    async def recover_interrupted_jobs() -> int:
        """Detects crashed/interrupted jobs and resets them to CHECKPOINT_SAVED so they can resume."""
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(Job).where(Job.status == "RUNNING")
            )
            stale_jobs = res.scalars().all()
            count = len(stale_jobs)
            for job in stale_jobs:
                logger.warning(f"[JobRecovery] Interrupted job '{job.id}' detected in stage '{job.checkpoint_stage}'. Resetting to CHECKPOINT_SAVED.")
                await session.execute(
                    update(Job)
                    .where(Job.id == job.id)
                    .values(status="CHECKPOINT_SAVED")
                )
            await session.commit()
            return count

    recover_stale_jobs = recover_interrupted_jobs

job_recovery_service = JobRecoveryService()
