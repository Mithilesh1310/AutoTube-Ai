import logging
from sqlalchemy import update
from backend.db.session import AsyncSessionLocal
from backend.db.models import Job, ChannelAutomationProfile
from backend.config import settings

logger = logging.getLogger(__name__)

class EmergencyControlService:
    """
    Emergency Controls & Global Kill Switch:
    Supports STOP_CHANNEL_AUTOMATION, STOP_JOB, CANCEL_PROVIDER_JOB, and GLOBAL_EMERGENCY_STOP.
    """
    @staticmethod
    async def stop_job(job_id: str):
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(status="CANCELLED", error_message="Cancelled by user via Emergency Control.")
            )
            await session.commit()
            logger.info(f"[EmergencyControl] Cancelled Job #{job_id}")

    @staticmethod
    async def pause_channel_automation(channel_id: int):
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(ChannelAutomationProfile)
                .where(ChannelAutomationProfile.channel_id == channel_id)
                .values(automation_enabled=False)
            )
            await session.commit()
            logger.info(f"[EmergencyControl] Paused automation for Channel #{channel_id}")

    @staticmethod
    async def global_emergency_stop(enabled: bool = True):
        settings.GLOBAL_EMERGENCY_STOP = enabled
        logger.warning(f"[EmergencyControl] Global Emergency Stop set to: {enabled}")

emergency_control_service = EmergencyControlService()
