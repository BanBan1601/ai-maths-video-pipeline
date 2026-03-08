from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "mathvid",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],  # autodiscover tasks
)

celery_app.conf.task_routes = {
    "app.workers.tasks.task_generate_idea": {"queue": "scheduler"},
    "app.workers.tasks.task_generate_script": {"queue": "script"},
    "app.workers.tasks.task_generate_manim": {"queue": "render"},
    "app.workers.tasks.task_run_qa": {"queue": "qa"},
    "app.workers.tasks.seed_video_job": {"queue": "scheduler"},
}

celery_app.conf.beat_schedule = {
    "auto-seed-video-jobs": {
        "task": "app.workers.tasks.seed_video_job",
        "schedule": 120.0,
    }
}

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule_filename = "/data/celerybeat-schedule"
