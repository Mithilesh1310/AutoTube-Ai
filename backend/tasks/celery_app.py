from celery import Celery
from celery.schedules import crontab
from backend.config import settings

celery_app = Celery(
    "autotube",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.TIMEZONE,
    enable_utc=False,
    task_track_started=True,
    task_time_limit=3600, # 1 hour max per workflow run
)

# Parse schedules (HH:MM)
def parse_time(time_str: str):
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])

gen_h, gen_m = parse_time(settings.WORKFLOW_GENERATE_TIME)
shorts_h, shorts_m = parse_time(settings.SHORTS_PUBLISH_TIME)
long_h, long_m = parse_time(settings.LONG_PUBLISH_TIME)

celery_app.conf.beat_schedule = {
    "daily-content-generation": {
        "task": "backend.tasks.workflow_tasks.run_daily_content_generation",
        "schedule": crontab(hour=gen_h, minute=gen_m),
    },
    "daily-shorts-publish": {
        "task": "backend.tasks.workflow_tasks.run_shorts_publish",
        "schedule": crontab(hour=shorts_h, minute=shorts_m),
    },
    "daily-long-publish": {
        "task": "backend.tasks.workflow_tasks.run_long_publish",
        "schedule": crontab(hour=long_h, minute=long_m),
    },
    "weekly-learning-analysis": {
        "task": "backend.tasks.workflow_tasks.run_weekly_learning",
        "schedule": crontab(day_of_week="sunday", hour=23, minute=0),
    }
}
