from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, require_roles
from app.db.session import get_db
from app.domain.models import UserRole
from app.domain.schemas import (
    DashboardSummary,
    DeviceCreate,
    DeviceRead,
    MetricRead,
    MonitoringJobCreate,
    MonitoringJobRead,
)
from app.repositories.monitoring import DeviceRepository, JobRepository, MetricRepository
from app.services.monitoring_service import MonitoringService

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def summary(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return MonitoringService(db).dashboard_summary(current.organization_id)


@router.get("/devices", response_model=list[DeviceRead])
def list_devices(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return DeviceRepository(db).list(current.organization_id)


@router.post("/devices", response_model=DeviceRead, status_code=201)
def create_device(
    payload: DeviceCreate,
    current: CurrentUser = Depends(require_roles(UserRole.owner, UserRole.admin, UserRole.engineer)),
    db: Session = Depends(get_db),
):
    return MonitoringService(db).create_device(current.organization_id, payload)


@router.get("/jobs", response_model=list[MonitoringJobRead])
def list_jobs(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return JobRepository(db).list(current.organization_id)


@router.post("/jobs", response_model=MonitoringJobRead, status_code=201)
def create_job(
    payload: MonitoringJobCreate,
    current: CurrentUser = Depends(require_roles(UserRole.owner, UserRole.admin, UserRole.engineer)),
    db: Session = Depends(get_db),
):
    try:
        return MonitoringService(db).create_job(current.organization_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/run", response_model=MetricRead)
async def run_job(
    job_id: UUID,
    current: CurrentUser = Depends(require_roles(UserRole.owner, UserRole.admin, UserRole.engineer)),
    db: Session = Depends(get_db),
):
    job = JobRepository(db).get(current.organization_id, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return await MonitoringService(db).run_check(job)


@router.get("/metrics", response_model=list[MetricRead])
def recent_metrics(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return MetricRepository(db).recent(current.organization_id)
