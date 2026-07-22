from celery import Celery
from app.config import settings

celery_app = Celery(
    "ai_service",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Configure task routing to specific queues
    task_routes={
        "app.tasks.transcribe_task": {"queue": "voice_transcription_queue"},
        "app.tasks.extract_trade_task": {"queue": "trade_extraction_queue"},
        "app.tasks.emotion_analysis_task": {"queue": "emotion_analysis_queue"},
        "app.tasks.generate_summary_task": {"queue": "summary_generation_queue"}
    }
)
