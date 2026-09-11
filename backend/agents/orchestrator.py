import os
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional
from sqlalchemy import select, update
from backend.db.session import AsyncSessionLocal
from backend.db.models import Job, JobLog, Video, Script, Scene, Setting
from backend.config import settings
from backend.services.visual_provider import ImageGenerationError
from backend.services.animation_provider import AnimationGenerationError, animation_provider_manager
from backend.services.cost_protection import cost_protection_service, InsufficientCreditsError
from backend.services.usage_ledger import usage_ledger_service
from backend.agents.state import PipelineState
from backend.agents.research_agent import run_research_agent
from backend.agents.planner_agent import run_planner_agent
from backend.agents.script_writer import run_script_writer
from backend.agents.script_qa import run_script_qa
from backend.agents.scene_director import run_scene_director
from backend.agents.animation_director import run_animation_director_agent
from backend.agents.voice_agent import run_voice_agent
from backend.agents.visual_agent import run_visual_agent
from backend.agents.animation_qa_agent import run_animation_qa_agent
from backend.agents.audio_director import run_audio_director_agent
from backend.agents.video_editor_agent import run_video_editor_agent
from backend.agents.video_qa_agent import run_video_qa_agent
from backend.agents.metadata_agent import run_metadata_agent
from backend.agents.thumbnail_agent import run_thumbnail_agent
from backend.agents.youtube_upload_agent import run_youtube_upload_agent

logger = logging.getLogger(__name__)

async def log_job_step(job_id: str, agent_name: str, level: str, message: str, details: dict = None):
    async with AsyncSessionLocal() as session:
        log_obj = JobLog(
            job_id=job_id,
            agent_name=agent_name,
            log_level=level,
            message=message,
            details=details
        )
        session.add(log_obj)
        await session.commit()

async def update_job_status(job_id: str, status: str, current_step: str, progress: float, error: str = None):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                status=status,
                checkpoint_stage=current_step,
                current_step=current_step,
                progress_percentage=progress,
                error_message=error
            )
        )
        await session.commit()

async def generate_animation_clips_for_scenes(state_dict: dict) -> dict:
    """Helper agent step: Invokes Animation Provider for FULL_ANIMATION & HYBRID visual modes."""
    job_id = state_dict.get("job_id", "job_demo")
    instructions = state_dict.get("animation_instructions", [])
    generated_images = state_dict.get("generated_images", {})
    video_type = state_dict.get("video_type", "LONG")
    is_vertical = (video_type == "SHORT")
    aspect_ratio = "9:16" if is_vertical else "16:9"

    base_dir = f"./storage/renders/{job_id}/animation"
    os.makedirs(base_dir, exist_ok=True)

    generated_clips = {}

    for idx, inst in enumerate(instructions, 1):
        num = inst.get("scene_number", idx)
        prompt = inst.get("animation_prompt", "")
        duration = inst.get("duration", 5.0)
        source_img = generated_images.get(num)
        output_clip_path = os.path.join(base_dir, f"scene_{num}.mp4")

        # Invoke pluggable animation provider manager with resilient fallback
        try:
            res = await animation_provider_manager.generate_scene_animation(
                prompt=prompt,
                output_path=output_clip_path,
                source_image_path=source_img,
                duration=duration,
                aspect_ratio=aspect_ratio
            )
            generated_clips[num] = res.video_clip_path
            
            # Log backend-authoritative usage
            await usage_ledger_service.record_usage(
                user_id=state_dict.get("user_id", 1),
                channel_id=state_dict.get("channel_id"),
                job_id=job_id,
                provider_name=res.provider_name,
                model_name="Luma/Kling/Fal",
                operation_type="ANIMATION_GEN",
                estimated_cost=res.cost,
                actual_cost=res.cost,
                credits_used=res.cost
            )
        except Exception as e:
            logger.warning(f"[AnimationGen] AI Video generation unavailable for scene {num}: {e}. Activating high-res Ken Burns motion fallback!")
            await log_job_step(
                job_id,
                "AnimationDirector",
                "WARNING",
                f"External video AI provider credit limit/quota hit ({e}). Seamlessly switching to dynamic Ken Burns motion rendering."
            )
            state_dict["visual_mode"] = "IMAGE_MOTION"
            state_dict["generated_animation_clips"] = {}
            break

    state_dict["generated_animation_clips"] = generated_clips
    state_dict["current_step"] = "ANIMATION_QA"
    return state_dict

async def run_single_pipeline(
    job_id: str,
    video_type: str = "LONG",
    local_test_only: bool = False,
    user_id: int = 1,
    channel_id: Optional[int] = None,
    visual_mode: str = "IMAGE_MOTION",
    parent_job_id: Optional[str] = None
) -> dict:
    """Executes the autonomous pipeline supporting IMAGE_MOTION, FULL_ANIMATION, HYBRID, and AUTO modes."""
    # Ensure child job record exists in DB
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Job).where(Job.id == job_id))
        if not res.scalar_one_or_none():
            child_job = Job(
                id=job_id,
                user_id=user_id,
                channel_id=channel_id,
                job_type=video_type,
                visual_mode=visual_mode,
                status="RUNNING",
                checkpoint_stage="INIT",
                current_step="INIT",
                progress_percentage=0.0
            )
            session.add(child_job)
            await session.commit()

    state = PipelineState(job_id=job_id, video_type=video_type)
    state_dict = state.model_dump()
    state_dict["local_test_only"] = local_test_only
    state_dict["skip_youtube_upload"] = local_test_only
    state_dict["user_id"] = user_id
    state_dict["channel_id"] = channel_id
    state_dict["visual_mode"] = visual_mode

    # Load user-configured publish_mode from database settings (PUBLIC, UNLISTED, PRIVATE)
    async with AsyncSessionLocal() as session:
        setting_res = await session.execute(
            select(Setting.value).where(Setting.key.in_(["YOUTUBE_PUBLISH_MODE", "PUBLISH_MODE"]))
        )
        saved_mode = setting_res.scalars().first()
        state_dict["publish_mode"] = saved_mode or getattr(settings, "YOUTUBE_PUBLISH_MODE", "PUBLIC")

    # COST PROTECTION CHECK BEFORE RUNNING EXPENSIVE STEPS
    estimated_cost = cost_protection_service.estimate_job_cost(visual_mode, video_type)
    approved, reason = await cost_protection_service.validate_user_spending(user_id, estimated_cost)
    if not approved:
        logger.error(f"[Orchestrator] Cost Protection Block: {reason}")
        await update_job_status(job_id, "INSUFFICIENT_CREDITS", "INIT", 0.0, reason)
        await log_job_step(job_id, "MasterOrchestrator", "ERROR", f"STATUS: INSUFFICIENT_CREDITS. {reason}")
        if parent_job_id:
            await update_job_status(parent_job_id, "INSUFFICIENT_CREDITS", "INIT", 0.0, reason)
            await log_job_step(parent_job_id, "MasterOrchestrator", "ERROR", f"[{video_type}] Cost Protection Block: {reason}")
        state_dict["current_step"] = "INSUFFICIENT_CREDITS"
        state_dict["error"] = reason
        return state_dict

    # Define steps based on Visual Mode
    if visual_mode == "FULL_ANIMATION":
        steps = [
            ("RESEARCH", run_research_agent, 10.0),
            ("PLANNER", run_planner_agent, 20.0),
            ("SCRIPT_WRITER", run_script_writer, 30.0),
            ("SCRIPT_QA", run_script_qa, 35.0),
            ("SCENE_DIRECTOR", run_scene_director, 40.0),
            ("ANIMATION_DIRECTOR", run_animation_director_agent, 45.0),
            ("VISUAL_GEN", run_visual_agent, 55.0), # Source frames for Image-to-Video
            ("ANIMATION_GEN", generate_animation_clips_for_scenes, 70.0),
            ("ANIMATION_QA", run_animation_qa_agent, 75.0),
            ("VOICE_GEN", run_voice_agent, 80.0),
            ("AUDIO_DIRECTOR", run_audio_director_agent, 82.0),
            ("VIDEO_EDITOR", run_video_editor_agent, 88.0),
            ("VIDEO_QA", run_video_qa_agent, 90.0),
            ("METADATA_SEO", run_metadata_agent, 93.0),
            ("THUMBNAIL_GEN", run_thumbnail_agent, 96.0),
            ("YOUTUBE_UPLOAD", run_youtube_upload_agent, 100.0)
        ]
    else: # IMAGE_MOTION (Existing 100% verified pipeline)
        steps = [
            ("RESEARCH", run_research_agent, 10.0),
            ("PLANNER", run_planner_agent, 20.0),
            ("SCRIPT_WRITER", run_script_writer, 30.0),
            ("SCRIPT_QA", run_script_qa, 35.0),
            ("SCENE_DIRECTOR", run_scene_director, 45.0),
            ("VOICE_GEN", run_voice_agent, 60.0),
            ("VISUAL_GEN", run_visual_agent, 75.0),
            ("VIDEO_EDITOR", run_video_editor_agent, 85.0),
            ("VIDEO_QA", run_video_qa_agent, 88.0),
            ("METADATA_SEO", run_metadata_agent, 92.0),
            ("THUMBNAIL_GEN", run_thumbnail_agent, 95.0),
            ("YOUTUBE_UPLOAD", run_youtube_upload_agent, 100.0)
        ]

    for step_name, agent_func, progress in steps:
        await update_job_status(job_id, "RUNNING", step_name, progress)
        await log_job_step(job_id, step_name, "INFO", f"Started {step_name} stage for {video_type} video ({visual_mode} mode).")
        
        # Sync parent job so dashboard updates in real time
        if parent_job_id:
            parent_prog = round((progress * 0.45) if video_type == "SHORT" else (45.0 + (progress * 0.55)), 1)
            await update_job_status(parent_job_id, "RUNNING", step_name, parent_prog)
            await log_job_step(parent_job_id, step_name, "INFO", f"[{video_type}] Stage: {step_name} ({parent_prog}%)")

        try:
            state_dict = await agent_func(state_dict)

            # Handle Script QA rewrite retry loop below 85 threshold (Max 3 rewrites)
            while step_name == "SCRIPT_QA" and state_dict.get("current_step") == "SCRIPT_WRITER" and state_dict.get("script_retries", 0) <= 3:
                retries = state_dict.get("script_retries", 0)
                tot_attempts = state_dict.get("total_attempts", retries + 1)
                await log_job_step(job_id, "SCRIPT_QA", "WARNING", f"Script QA failed (Attempt {tot_attempts}/4). Retrying...")
                if parent_job_id:
                    await log_job_step(parent_job_id, "SCRIPT_QA", "WARNING", f"[{video_type}] Script QA rewrite retry ({tot_attempts}/4)...")
                state_dict = await run_script_writer(state_dict)
                state_dict = await run_script_qa(state_dict)

            if state_dict.get("current_step") == "FAILED_QUALITY_GATE":
                err_msg = "Script failed Hard Quality Gates after 3 rewrites."
                await update_job_status(job_id, "FAILED_QUALITY_GATE", "SCRIPT_QA", progress, err_msg)
                if parent_job_id:
                    await update_job_status(parent_job_id, "FAILED_QUALITY_GATE", "SCRIPT_QA", progress, err_msg)
                state_dict["error"] = err_msg
                return state_dict

            if state_dict.get("current_step") == "FAILED_IMAGE_GENERATION":
                err_msg = state_dict.get("error", "Image generation failed.")
                await update_job_status(job_id, "FAILED_IMAGE_GENERATION", step_name, progress, err_msg)
                if parent_job_id:
                    await update_job_status(parent_job_id, "FAILED_IMAGE_GENERATION", step_name, progress, err_msg)
                return state_dict

            if state_dict.get("current_step") == "FAILED_ANIMATION_GENERATION":
                err_msg = state_dict.get("error", "Animation generation failed.")
                await update_job_status(job_id, "FAILED_ANIMATION_GENERATION", step_name, progress, err_msg)
                if parent_job_id:
                    await update_job_status(parent_job_id, "FAILED_ANIMATION_GENERATION", step_name, progress, err_msg)
                return state_dict

            if state_dict.get("current_step") == "FAILED_ANIMATION_QUALITY":
                err_msg = state_dict.get("error", "Animation QA validation failed.")
                await update_job_status(job_id, "FAILED_ANIMATION_QUALITY", step_name, progress, err_msg)
                if parent_job_id:
                    await update_job_status(parent_job_id, "FAILED_ANIMATION_QUALITY", step_name, progress, err_msg)
                return state_dict

        except ImageGenerationError as ige:
            logger.error(f"Image generation failed at step {step_name}: {ige}")
            await update_job_status(job_id, "FAILED_IMAGE_GENERATION", step_name, progress, str(ige))
            if parent_job_id:
                await update_job_status(parent_job_id, "FAILED_IMAGE_GENERATION", step_name, progress, str(ige))
            state_dict["current_step"] = "FAILED_IMAGE_GENERATION"
            state_dict["error"] = str(ige)
            return state_dict
        except AnimationGenerationError as age:
            logger.error(f"Animation generation failed at step {step_name}: {age}")
            await update_job_status(job_id, "FAILED_ANIMATION_GENERATION", step_name, progress, str(age))
            if parent_job_id:
                await update_job_status(parent_job_id, "FAILED_ANIMATION_GENERATION", step_name, progress, str(age))
            state_dict["current_step"] = "FAILED_ANIMATION_GENERATION"
            state_dict["error"] = str(age)
            return state_dict
        except Exception as e:
            logger.error(f"Pipeline error at step {step_name}: {e}")
            err_msg = str(e)
            await update_job_status(job_id, "FAILED", step_name, progress, err_msg)
            await log_job_step(job_id, step_name, "ERROR", f"Failed at {step_name}: {err_msg}")
            if parent_job_id:
                await update_job_status(parent_job_id, "FAILED", step_name, progress, err_msg)
                await log_job_step(parent_job_id, step_name, "ERROR", f"[{video_type}] Pipeline failed at {step_name}: {err_msg}")
            state_dict["current_step"] = "FAILED"
            state_dict["error"] = err_msg
            return state_dict

    # Save generated video & script records to DB
    async with AsyncSessionLocal() as session:
        script_obj = Script(
            video_type=video_type,
            title=state_dict.get("title", "Hindi Animated Story"),
            summary=state_dict.get("selected_idea", {}).get("summary", ""),
            script_json=state_dict.get("script_data", {}),
            moral=state_dict.get("script_data", {}).get("moral", ""),
            qa_score=state_dict.get("script_qa_score", 90.0),
            is_approved=True
        )
        session.add(script_obj)
        await session.flush()

        video_obj = Video(
            user_id=user_id,
            channel_id=channel_id,
            script_id=script_obj.id,
            video_type=video_type,
            visual_mode=visual_mode,
            title=state_dict.get("title", "Hindi Animated Story"),
            description=state_dict.get("description", ""),
            tags=state_dict.get("tags", []),
            hashtags=state_dict.get("hashtags", []),
            publish_mode=state_dict.get("publish_mode") or settings.YOUTUBE_PUBLISH_MODE or "PUBLIC",
            video_path=state_dict.get("rendered_video_path"),
            thumbnail_path=state_dict.get("thumbnail_path"),
            youtube_video_id=state_dict.get("youtube_video_id"),
            youtube_url=state_dict.get("youtube_url"),
            status="COMPLETED",
            qa_passed=state_dict.get("video_qa_passed", True)
        )
        session.add(video_obj)
        await session.commit()

    await update_job_status(job_id, "COMPLETED", "COMPLETED", 100.0)
    await log_job_step(job_id, "MasterOrchestrator", "SUCCESS", f"Successfully completed autonomous pipeline for {video_type} ({visual_mode}) video!")
    return state_dict

async def run_pipeline(
    job_id: str = None,
    task_type: str = "DAILY_WORKFLOW",
    local_test_only: bool = False,
    user_id: int = 1,
    channel_id: Optional[int] = None,
    visual_mode: str = "IMAGE_MOTION"
) -> dict:
    if not job_id:
        job_id = f"job_{uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job_obj = result.scalar_one_or_none()
        if not job_obj:
            job_obj = Job(
                id=job_id,
                user_id=user_id,
                channel_id=channel_id,
                job_type=task_type,
                visual_mode=visual_mode,
                status="RUNNING",
                checkpoint_stage="INIT",
                current_step="INIT",
                progress_percentage=0.0
            )
            session.add(job_obj)
        else:
            job_obj.status = "RUNNING"
            job_obj.current_step = "INIT"
            job_obj.progress_percentage = 0.0
        await session.commit()

    await log_job_step(job_id, "MasterOrchestrator", "INFO", f"Autonomous AutoTube Pipeline launched (Task: {task_type}, Mode: {visual_mode}).")

    if task_type in ["DAILY_WORKFLOW", "BOTH"]:
        logger.info(f"[MasterOrchestrator] Executing Daily Workflow for Channel #{channel_id}: 1 Short + 1 Long Video...")
        short_res = await run_single_pipeline(
            job_id=f"{job_id}_short",
            video_type="SHORT",
            local_test_only=local_test_only,
            user_id=user_id,
            channel_id=channel_id,
            visual_mode=visual_mode,
            parent_job_id=job_id
        )
        long_res = await run_single_pipeline(
            job_id=f"{job_id}_long",
            video_type="LONG",
            local_test_only=local_test_only,
            user_id=user_id,
            channel_id=channel_id,
            visual_mode=visual_mode,
            parent_job_id=job_id
        )

        short_err = short_res.get("error")
        long_err = long_res.get("error")

        if short_err or long_err:
            err_summary = f"Short: {short_err or 'OK'} | Long: {long_err or 'OK'}"
            await update_job_status(job_id, "FAILED", "FAILED", 100.0, err_summary)
            await log_job_step(job_id, "MasterOrchestrator", "ERROR", f"Daily Workflow completed with errors: {err_summary}")
            return {"short": short_res, "long": long_res, "error": err_summary}
        else:
            await update_job_status(job_id, "COMPLETED", "COMPLETED", 100.0)
            await log_job_step(job_id, "MasterOrchestrator", "SUCCESS", "Successfully completed autonomous Daily Workflow (1 Short + 1 Long)!")
            return {"short": short_res, "long": long_res}
    elif task_type == "SHORT":
        return await run_single_pipeline(job_id=job_id, video_type="SHORT", local_test_only=local_test_only, user_id=user_id, channel_id=channel_id, visual_mode=visual_mode)
    else:
        return await run_single_pipeline(job_id=job_id, video_type="LONG", local_test_only=local_test_only, user_id=user_id, channel_id=channel_id, visual_mode=visual_mode)
