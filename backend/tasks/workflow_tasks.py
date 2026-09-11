import asyncio
from backend.tasks.celery_app import celery_app
from backend.config import settings

@celery_app.task(bind=True, name="backend.tasks.workflow_tasks.run_daily_content_generation")
def run_daily_content_generation(self, job_id: str = None):
    """Triggers the autonomous daily generation workflow for 1 Short and 1 Long video."""
    print(f"🚀 Starting daily content generation task... (Job ID: {job_id})")
    # Will call orchestrator workflow
    from backend.agents.orchestrator import run_pipeline
    return asyncio.run(run_pipeline(job_id=job_id, task_type="DAILY_WORKFLOW"))

@celery_app.task(bind=True, name="backend.tasks.workflow_tasks.run_shorts_publish")
def run_shorts_publish(self, video_id: int = None):
    """Triggers publishing of scheduled Short video to YouTube."""
    print(f"📤 Publishing daily Hindi Short video... (Video ID: {video_id})")
    from backend.services.youtube_service import publish_video_by_id
    return asyncio.run(publish_video_by_id(video_id=video_id, target_type="SHORT"))

@celery_app.task(bind=True, name="backend.tasks.workflow_tasks.run_long_publish")
def run_long_publish(self, video_id: int = None):
    """Triggers publishing of scheduled Long video to YouTube."""
    print(f"📤 Publishing daily Hindi Long cartoon video... (Video ID: {video_id})")
    from backend.services.youtube_service import publish_video_by_id
    return asyncio.run(publish_video_by_id(video_id=video_id, target_type="LONG"))

@celery_app.task(bind=True, name="backend.tasks.workflow_tasks.run_weekly_learning")
def run_weekly_learning(self):
    """Triggers weekly analytics analysis and learning insight generator."""
    print("📊 Executing weekly learning analysis...")
    from backend.agents.learning_agent import run_learning_analysis
    return asyncio.run(run_learning_analysis())
