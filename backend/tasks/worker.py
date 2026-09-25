import os
import sys
import time
import json
import random
import asyncio
import signal
import logging
from typing import Dict, Any, Optional
from sqlalchemy import select, update
from backend.db.session import AsyncSessionLocal, transactional_session
from backend.db.models import Job, JobLog
from backend.config import settings

logger = logging.getLogger(__name__)

class BackgroundJobQueue:
    """
    Production Background Job Queue Service:
    Supports Redis queue with high-throughput async priority in-memory fallback.
    Provides exponential backoff retries, dead-letter handling, priority queues,
    cancellation checks, and graceful worker shutdown.
    """
    def __init__(self):
        self.running = True
        self._queue = asyncio.PriorityQueue() # (priority_int, timestamp, task_payload)
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.completed_count = 0
        self.failed_count = 0
        self.dead_letter_count = 0
        self.worker_task: Optional[asyncio.Task] = None

    def priority_to_int(self, priority: str) -> int:
        priorities = {"HIGH": 1, "DEFAULT": 2, "LOW": 3}
        return priorities.get(priority.upper(), 2)

    async def enqueue_job(
        self,
        job_id: str,
        task_type: str = "DAILY_WORKFLOW",
        user_id: int = 1,
        channel_id: Optional[int] = None,
        visual_mode: str = "FULL_ANIMATION",
        priority: str = "DEFAULT",
        max_retries: int = 3
    ):
        """Pushes a video generation job onto the background priority queue."""
        payload = {
            "job_id": job_id,
            "task_type": task_type,
            "user_id": user_id,
            "channel_id": channel_id,
            "visual_mode": visual_mode,
            "priority": priority,
            "attempt": 1,
            "max_retries": max_retries,
            "enqueued_at": time.time()
        }

        # Update Job status in DB to QUEUED
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(status="QUEUED", priority=priority)
            )
            await session.commit()

        # Enqueue with priority tuple: (prio_int, enqueued_at_timestamp, payload)
        prio_int = self.priority_to_int(priority)
        await self._queue.put((prio_int, time.time(), payload))
        logger.info(f"[JobQueue] Enqueued Job #{job_id} (Priority: {priority}, Mode: {visual_mode}). Queue depth: {self._queue.qsize()}")

    async def dequeue_job(self) -> Dict[str, Any]:
        """Pops the highest-priority job payload from the priority queue."""
        prio_int, seq_ts, payload = await self._queue.get()
        return payload

    def _compute_backoff_delay(self, retry_count: int) -> float:
        """Computes exponential backoff with jitter."""
        return (2 ** retry_count) + random.uniform(1.0, 3.0)

    async def _process_single_job(self, payload: Dict[str, Any]):
        job_id = payload["job_id"]
        task_type = payload["task_type"]
        user_id = payload["user_id"]
        channel_id = payload["channel_id"]
        visual_mode = payload["visual_mode"]
        attempt = payload["attempt"]
        max_retries = payload["max_retries"]

        # Check for pre-cancellation
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(Job).where(Job.id == job_id))
            job_obj = res.scalar_one_or_none()
            if job_obj and job_obj.status in ["CANCELLED", "STOPPED"]:
                logger.info(f"[JobQueue] Job #{job_id} was pre-cancelled. Skipping execution.")
                return

        from backend.agents.orchestrator import run_pipeline

        try:
            logger.info(f"[JobQueue] Worker processing Job #{job_id} (Attempt {attempt}/{max_retries})...")
            result = await run_pipeline(
                job_id=job_id,
                task_type=task_type,
                user_id=user_id,
                channel_id=channel_id,
                visual_mode=visual_mode
            )

            # Check if finished with error
            if isinstance(result, dict):
                if result.get("error"):
                    raise RuntimeError(result["error"])
                if "short" in result and isinstance(result["short"], dict) and result["short"].get("error"):
                    raise RuntimeError(f"Short video failed: {result['short']['error']}")
                if "long" in result and isinstance(result["long"], dict) and result["long"].get("error"):
                    raise RuntimeError(f"Long video failed: {result['long']['error']}")

            self.completed_count += 1
            logger.info(f"[JobQueue] Successfully finished background Job #{job_id}.")

        except Exception as e:
            logger.error(f"[JobQueue] Job #{job_id} failed on attempt {attempt}: {e}")
            if attempt < max_retries:
                # Exponential backoff with jitter: backoff = 2^attempt + random(1, 3)
                backoff_seconds = self._compute_backoff_delay(attempt)
                logger.info(f"[JobQueue] Retrying Job #{job_id} in {backoff_seconds:.1f}s...")
                await asyncio.sleep(backoff_seconds)
                payload["attempt"] += 1
                await self._queue.put((self.priority_to_int(payload["priority"]), time.time(), payload))
            else:
                # Max retries exhausted -> Move to Dead Letter
                self.dead_letter_count += 1
                self.failed_count += 1
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(Job)
                        .where(Job.id == job_id)
                        .values(
                            status="DEAD_LETTER",
                            error_message=f"Dead letter: permanently failed after {max_retries} attempts. Last error: {e}"
                        )
                    )
                    await session.commit()
                logger.error(f"[JobQueue] Job #{job_id} permanently moved to DEAD_LETTER.")

    async def _worker_loop(self):
        """Dedicated background worker loop consuming jobs from queue."""
        logger.info("[JobQueue] Dedicated background worker loop started.")
        while self.running:
            try:
                try:
                    # Wait up to 1 second for a job
                    prio, seq_ts, payload = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                job_id = payload["job_id"]
                task = asyncio.create_task(self._process_single_job(payload))
                self.active_tasks[job_id] = task

                try:
                    await task
                finally:
                    self.active_tasks.pop(job_id, None)
                    self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[JobQueue] Unexpected error in worker loop: {e}")
                await asyncio.sleep(1)

        logger.info("[JobQueue] Worker loop terminated cleanly.")

    def start_worker(self):
        """Starts the dedicated worker in the event loop."""
        if not self.worker_task or self.worker_task.done():
            self.running = True
            self.worker_task = asyncio.create_task(self._worker_loop())

    async def stop_worker(self, timeout: float = 10.0):
        """Graceful shutdown: waits for active tasks to checkpoint, then terminates."""
        logger.info("[JobQueue] Initiating graceful worker shutdown...")
        self.running = False
        if self.active_tasks:
            logger.info(f"[JobQueue] Waiting for {len(self.active_tasks)} active jobs to reach safe checkpoint...")
            try:
                await asyncio.wait_for(asyncio.gather(*self.active_tasks.values(), return_exceptions=True), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("[JobQueue] Timeout reached during graceful shutdown. Forcing exit.")

        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.info("[JobQueue] Graceful shutdown complete.")

    def get_metrics(self) -> Dict[str, Any]:
        """Returns live queue depth and throughput metrics."""
        return {
            "queue_depth": self._queue.qsize(),
            "active_workers": len(self.active_tasks),
            "active_job_ids": list(self.active_tasks.keys()),
            "completed_jobs": self.completed_count,
            "failed_jobs": self.failed_count,
            "dead_letter_jobs": self.dead_letter_count,
            "worker_status": "RUNNING" if self.running else "STOPPED"
        }

job_queue = BackgroundJobQueue()
JobQueue = BackgroundJobQueue
background_worker = job_queue
