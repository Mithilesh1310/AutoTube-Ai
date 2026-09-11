import uuid
import datetime
import asyncio
import logging
from zoneinfo import ZoneInfo
from typing import List, Optional
from sqlalchemy import select, desc
from backend.db.session import AsyncSessionLocal
from backend.db.models import ChannelAutomationProfile, Job, Video
from backend.tasks.worker import job_queue

logger = logging.getLogger(__name__)

class MultiChannelScheduler:
    """
    Autonomous Timezone-Aware Multi-Channel Scheduler Service:
    - Evaluates each channel automation profile in its specific configured timezone.
    - Validates days_of_week and minimum_gap_between_uploads.
    - Uses restart-safe idempotency keys and offloads generation to the background worker queue.
    """
    def __init__(self):
        self._is_running = False
        self._task = None

    async def start(self):
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._schedule_loop())
        logger.info("[MultiChannelScheduler] Autonomous multi-channel scheduler started.")

    async def stop(self):
        self._is_running = False
        if self._task:
            self._task.cancel()
        logger.info("[MultiChannelScheduler] Scheduler stopped.")

    def _check_gap_constraint(
        self,
        last_published_at: Optional[datetime.datetime],
        gap_hours: float,
        current_time: Optional[datetime.datetime] = None
    ) -> bool:
        """Validates if minimum required gap has passed since the last publication."""
        if not last_published_at:
            return True
        now = current_time or datetime.datetime.now(datetime.timezone.utc)
        if last_published_at.tzinfo is None and now.tzinfo is not None:
            last_published_at = last_published_at.replace(tzinfo=datetime.timezone.utc)
        elif last_published_at.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=datetime.timezone.utc)
        elapsed_hours = abs((now - last_published_at).total_seconds()) / 3600.0
        return elapsed_hours >= gap_hours

    async def _schedule_loop(self):
        while self._is_running:
            try:
                await self.check_and_trigger_scheduled_jobs()
            except Exception as e:
                logger.error(f"[MultiChannelScheduler] Error in schedule loop: {e}")
            await asyncio.sleep(60) # Poll every minute

    async def check_and_trigger_scheduled_jobs(self):
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(ChannelAutomationProfile)
                .where(ChannelAutomationProfile.automation_enabled == True)
            )
            profiles = res.scalars().all()

            for profile in profiles:
                try:
                    tz = ZoneInfo(profile.timezone or "Asia/Kolkata")
                except Exception:
                    tz = ZoneInfo("Asia/Kolkata")

                # Local time for this channel's timezone
                channel_now = datetime.datetime.now(tz)
                current_time_str = channel_now.strftime("%H:%M")
                current_date_str = channel_now.strftime("%Y-%m-%d")
                current_day_name = channel_now.strftime("%A")

                # 1. Day of week filter
                allowed_days = profile.days_of_week or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                if current_day_name not in allowed_days:
                    continue

                # 2. Check scheduled times
                publish_times = profile.publish_times or ["10:00", "18:00"]
                for slot in publish_times:
                    if slot == current_time_str:
                        # 3. Minimum gap between uploads check
                        min_gap_hours = profile.minimum_gap_between_uploads_hours or 4
                        latest_vid_res = await session.execute(
                            select(Video)
                            .where(Video.channel_id == profile.channel_id)
                            .order_by(desc(Video.created_at))
                            .limit(1)
                        )
                        latest_vid = latest_vid_res.scalar_one_or_none()
                        if latest_vid and latest_vid.created_at:
                            if not self._check_gap_constraint(latest_vid.created_at, min_gap_hours):
                                logger.info(f"[MultiChannelScheduler] Skipping slot {slot} for Channel #{profile.channel_id}: minimum gap ({min_gap_hours}h) not met.")
                                continue

                        video_type = "SHORT" if profile.video_format == "SHORT" else "LONG"
                        idempotency_key = f"auto_{profile.channel_id}_{current_date_str}_{slot}_{video_type}"

                        # 4. Idempotency Check
                        res_job = await session.execute(select(Job).where(Job.idempotency_key == idempotency_key))
                        existing_job = res_job.scalar_one_or_none()

                        if not existing_job:
                            job_id = f"job_{uuid.uuid4().hex[:8]}"
                            logger.info(f"[MultiChannelScheduler] Triggering scheduled job '{job_id}' for Channel #{profile.channel_id} (Slot: {slot}, TZ: {profile.timezone})...")
                            
                            new_job = Job(
                                id=job_id,
                                user_id=profile.user_id,
                                channel_id=profile.channel_id,
                                job_type="SCHEDULED_AUTOMATION",
                                video_type=video_type,
                                visual_mode=profile.visual_mode,
                                status="QUEUED",
                                checkpoint_stage="INIT",
                                idempotency_key=idempotency_key,
                                priority="DEFAULT"
                            )
                            session.add(new_job)
                            await session.commit()

                            # Enqueue into background worker
                            await job_queue.enqueue_job(
                                job_id=job_id,
                                task_type=video_type,
                                user_id=profile.user_id,
                                channel_id=profile.channel_id,
                                visual_mode=profile.visual_mode,
                                priority="DEFAULT"
                            )

multi_channel_scheduler = MultiChannelScheduler()
