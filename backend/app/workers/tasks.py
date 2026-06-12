import asyncio

from app.db.session import SessionLocal
from app.repositories.monitoring import JobRepository
from app.services.monitoring_service import MonitoringService
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.run_monitoring_checks")
def run_monitoring_checks() -> int:
    db = SessionLocal()
    try:
        jobs = JobRepository(db).enabled()
        service = MonitoringService(db)
        for job in jobs:
            asyncio.run(service.run_check(job))
        return len(jobs)
    finally:
        db.close()
