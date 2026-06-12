from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import Device, Metric, MonitoringJob, Status
from app.repositories.base import TenantRepository


class DeviceRepository(TenantRepository[Device]):
    def __init__(self, db: Session):
        super().__init__(db, Device)


class JobRepository(TenantRepository[MonitoringJob]):
    def __init__(self, db: Session):
        super().__init__(db, MonitoringJob)

    def enabled(self) -> list[MonitoringJob]:
        return list(self.db.scalars(select(MonitoringJob).where(MonitoringJob.enabled.is_(True))))


class MetricRepository(TenantRepository[Metric]):
    def __init__(self, db: Session):
        super().__init__(db, Metric)

    def recent(self, organization_id: UUID, limit: int = 200) -> list[Metric]:
        stmt = (
            select(Metric)
            .where(Metric.organization_id == organization_id)
            .order_by(Metric.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def summary(self, organization_id: UUID) -> dict:
        day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        total_devices = self.db.scalar(
            select(func.count(Device.id)).where(Device.organization_id == organization_id)
        ) or 0
        counts = {
            status.value: self.db.scalar(
                select(func.count(Device.id)).where(
                    Device.organization_id == organization_id,
                    Device.status == status,
                )
            )
            or 0
            for status in Status
        }
        total_metrics = self.db.scalar(
            select(func.count(Metric.id)).where(
                Metric.organization_id == organization_id,
                Metric.created_at >= day_ago,
            )
        ) or 0
        up_metrics = self.db.scalar(
            select(func.count(Metric.id)).where(
                Metric.organization_id == organization_id,
                Metric.created_at >= day_ago,
                Metric.status == Status.up,
            )
        ) or 0
        avg_latency = self.db.scalar(
            select(func.avg(Metric.latency_ms)).where(
                Metric.organization_id == organization_id,
                Metric.created_at >= day_ago,
                Metric.status == Status.up,
            )
        )
        return {
            "total_devices": total_devices,
            "up": counts["up"],
            "degraded": counts["degraded"],
            "down": counts["down"],
            "unknown": counts["unknown"],
            "uptime_percentage": round((up_metrics / total_metrics) * 100, 3) if total_metrics else 100.0,
            "avg_latency_ms": round(float(avg_latency), 2) if avg_latency is not None else None,
        }
