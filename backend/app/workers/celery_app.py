from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("netpulse", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.beat_schedule = {
    "run-monitoring-every-minute": {
        "task": "app.workers.tasks.run_monitoring_checks",
        "schedule": 60.0,
    }
}
