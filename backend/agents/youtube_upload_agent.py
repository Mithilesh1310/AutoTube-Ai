import os
import logging
from sqlalchemy import select, update
from backend.services.youtube_service import youtube_service
from backend.db.session import AsyncSessionLocal
from backend.db.models import Job, YouTubeChannel, ContentMemory
from backend.config import settings

logger = logging.getLogger(__name__)

def pre_upload_gate(state_dict: dict) -> tuple[bool, str]:
    """Validates video readiness before initiating YouTube upload."""
    video_path = state_dict.get("rendered_video_path")
    thumbnail_path = state_dict.get("thumbnail_path")
    title = state_dict.get("title", "")
    description = state_dict.get("description", "")
    test_mode = state_dict.get("test_mode", False)

    gate_failures = []
    if not video_path or not os.path.exists(video_path):
        gate_failures.append("Rendered MP4 video file does not exist.")
    elif os.path.getsize(video_path) < 50000:
        gate_failures.append(f"Rendered video size is suspiciously small: {os.path.getsize(video_path)} bytes.")

    if not thumbnail_path or not os.path.exists(thumbnail_path):
        gate_failures.append("Thumbnail asset does not exist.")

    if not title or len(str(title).strip()) < 3:
        gate_failures.append("Video title is missing or too short.")
    if not description:
        gate_failures.append("Video description is missing.")

    if not test_mode:
        if state_dict.get("has_placeholder_images"):
            gate_failures.append("Scene visuals contain placeholder assets.")
        if state_dict.get("thumbnail_is_placeholder"):
            gate_failures.append("Thumbnail is a placeholder asset.")

    if not state_dict.get("video_qa_passed", True):
        gate_failures.append("Video QA check failed.")

    if gate_failures:
        return False, "; ".join(gate_failures)
    return True, ""


async def run_youtube_upload_agent(state_dict: dict) -> dict:
    logger.info("[YouTubeUploadAgent] Running YouTube Upload Agent, PRE_UPLOAD_GATE & Idempotency Safeguards...")
    
    job_id = state_dict.get("job_id", "demo_job")
    channel_id = state_dict.get("channel_id")
    user_id = state_dict.get("user_id", 1)
    video_path = state_dict.get("rendered_video_path")
    title = state_dict.get("title", "Hindi Kids Story")
    description = state_dict.get("description", "")
    tags = state_dict.get("tags", [])
    thumbnail_path = state_dict.get("thumbnail_path")
    test_mode = state_dict.get("test_mode", False)

    # 1. IDEMPOTENCY CHECK — Never upload the same job or video twice
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Job).where(Job.id == job_id))
        job = res.scalar_one_or_none()
        if job:
            if job.youtube_video_id and job.upload_status == "UPLOADED":
                logger.warning(f"[YouTubeUploadAgent] Idempotency Hit: Job #{job_id} already uploaded to YouTube ID '{job.youtube_video_id}'. Skipping duplicate upload.")
                state_dict["youtube_video_id"] = job.youtube_video_id
                state_dict["youtube_url"] = f"https://youtu.be/{job.youtube_video_id}"
                state_dict["publish_status"] = "ALREADY_UPLOADED"
                state_dict["current_step"] = "COMPLETED"
                return state_dict

            # Check channel ownership
            if channel_id:
                chan_res = await session.execute(select(YouTubeChannel).where(YouTubeChannel.id == channel_id))
                chan = chan_res.scalar_one_or_none()
                if chan and chan.user_id != user_id and user_id != 1:
                    logger.error(f"[PRE_UPLOAD_GATE] Channel ownership violation: User #{user_id} does not own Channel #{channel_id}")
                    state_dict["publish_status"] = "FAILED_PRE_UPLOAD_GATE"
                    state_dict["error"] = "Channel ownership verification failed."
                    return state_dict

    # 2. PRE_UPLOAD_GATE VALIDATION
    is_valid, reason = pre_upload_gate(state_dict)
    if not is_valid:
        logger.error(f"⛔ PRE_UPLOAD_GATE VIOLATION: {reason}")
        state_dict["production_gate_passed"] = False
        state_dict["production_gate_reasons"] = reason.split("; ")
        state_dict["publish_status"] = "FAILED_PRE_UPLOAD_GATE"
        state_dict["current_step"] = "FAILED_PRE_UPLOAD_GATE"
        state_dict["error"] = f"PRE_UPLOAD_GATE blocked upload: {reason}"
        return state_dict

    state_dict["production_gate_passed"] = True

    # 3. Check if local test mode (skips live upload)
    if state_dict.get("skip_youtube_upload") or state_dict.get("local_test_only"):
        logger.info("[YouTubeUploadAgent] Local Quality Test Mode: Skipping YouTube upload.")
        state_dict["youtube_video_id"] = "LOCAL_TEST_NO_UPLOAD"
        state_dict["youtube_url"] = "NO_UPLOAD_LOCAL_TEST_ONLY"
        state_dict["publish_status"] = "LOCAL_QUALITY_TEST_ONLY"
        state_dict["current_step"] = "COMPLETED"
        return state_dict

    # 4. Record Upload In-Progress State
    idempotency_key = f"upload_{channel_id or 1}_{title[:20].replace(' ', '_')}_{job_id}"
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                upload_idempotency_key=idempotency_key,
                upload_status="IN_PROGRESS",
                upload_attempts=Job.upload_attempts + 1
            )
        )
        await session.commit()

    # 5. Execute Live YouTube Upload
    publish_mode = state_dict.get("publish_mode") or settings.YOUTUBE_PUBLISH_MODE or "PUBLIC"
    try:
        upload_res = await youtube_service.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            thumbnail_path=thumbnail_path,
            publish_mode=publish_mode,
            is_made_for_kids=True,
            channel_id=channel_id
        )

        if not upload_res or upload_res.get("status") != "COMPLETED":
            err_msg = (upload_res or {}).get("error") or (upload_res or {}).get("reason") or "YouTube upload failed"
            raise RuntimeError(err_msg)

        vid_id = upload_res.get("youtube_video_id")
        yt_url = upload_res.get("youtube_url")
        if not vid_id:
            raise RuntimeError("YouTube API returned COMPLETED without a valid video ID.")

        state_dict["youtube_video_id"] = vid_id
        state_dict["youtube_url"] = yt_url
        state_dict["publish_status"] = "COMPLETED"
        state_dict["current_step"] = "COMPLETED"

        # Update Job in DB to UPLOADED
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(
                    youtube_video_id=vid_id,
                    upload_status="UPLOADED"
                )
            )
            await session.commit()

        logger.info(f"✅ [YouTubeUploadAgent] Upload SUCCESS! YouTube ID: {vid_id}, Link: {yt_url}")

    except Exception as e:
        logger.error(f"[YouTubeUploadAgent] Upload Error: {e}")
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(upload_status="FAILED", error_message=str(e))
            )
            await session.commit()
        state_dict["publish_status"] = "FAILED"
        state_dict["error"] = str(e)

    return state_dict
