import asyncio
import socket
import ssl
import time
from datetime import datetime, timezone
from uuid import UUID

import dns.resolver
import httpx
from sqlalchemy.orm import Session

from app.domain.models import Device, Incident, Metric, MonitorType, MonitoringJob, Status
from app.domain.schemas import DashboardSummary, DeviceCreate, MonitoringJobCreate
from app.repositories.monitoring import DeviceRepository, JobRepository, MetricRepository


class MonitoringService:
    def __init__(self, db: Session):
        self.db = db
        self.devices = DeviceRepository(db)
        self.jobs = JobRepository(db)
        self.metrics = MetricRepository(db)

    def create_device(self, organization_id: UUID, data: DeviceCreate) -> Device:
        return self.devices.add(Device(organization_id=organization_id, **data.model_dump()))

    def create_job(self, organization_id: UUID, data: MonitoringJobCreate) -> MonitoringJob:
        device = self.devices.get(organization_id, data.device_id)
        if not device:
            raise ValueError("Device not found")
        return self.jobs.add(MonitoringJob(organization_id=organization_id, **data.model_dump()))

    def dashboard_summary(self, organization_id: UUID) -> DashboardSummary:
        return DashboardSummary(**self.metrics.summary(organization_id))

    async def run_check(self, job: MonitoringJob) -> Metric:
        started = time.perf_counter()
        status = Status.up
        detail: dict = {}
        packet_loss = 0.0
        try:
            await self._probe(job)
            latency = (time.perf_counter() - started) * 1000
        except Exception as exc:
            latency = None
            packet_loss = 100.0
            status = Status.down
            detail = {"error": str(exc)}

        metric = Metric(
            organization_id=job.organization_id,
            job_id=job.id,
            status=status,
            latency_ms=latency,
            packet_loss=packet_loss,
            detail=detail,
        )
        self.db.add(metric)
        device = self.db.get(Device, job.device_id)
        if device:
            device.status = status
            if status == Status.down:
                self._open_incident(job, device)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    async def _probe(self, job: MonitoringJob) -> None:
        target = job.device.target
        match job.monitor_type:
            case MonitorType.http | MonitorType.api:
                url = job.config.get("url", target)
                method = job.config.get("method", "GET")
                expected = int(job.config.get("expected_status", 200))
                async with httpx.AsyncClient(timeout=job.timeout_seconds) as client:
                    response = await client.request(method, url)
                    if response.status_code != expected:
                        raise RuntimeError(f"Expected {expected}, got {response.status_code}")
            case MonitorType.tcp:
                host = job.config.get("host", target)
                port = int(job.config["port"])
                await asyncio.wait_for(asyncio.open_connection(host, port), timeout=job.timeout_seconds)
            case MonitorType.dns:
                resolver = dns.resolver.Resolver()
                resolver.lifetime = job.timeout_seconds
                resolver.resolve(target, job.config.get("record_type", "A"))
            case MonitorType.ssl:
                host = job.config.get("host", target)
                port = int(job.config.get("port", 443))
                context = ssl.create_default_context()
                with socket.create_connection((host, port), timeout=job.timeout_seconds) as sock:
                    with context.wrap_socket(sock, server_hostname=host) as tls:
                        cert = tls.getpeercert()
                expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                if (expires - datetime.now(timezone.utc)).days < int(job.config.get("min_days", 14)):
                    raise RuntimeError("SSL certificate expires inside threshold")
            case MonitorType.icmp:
                # Containers usually lack raw socket permission. Use TCP fallback when configured.
                port = int(job.config.get("port", 443))
                await asyncio.wait_for(asyncio.open_connection(target, port), timeout=job.timeout_seconds)

    def _open_incident(self, job: MonitoringJob, device: Device) -> None:
        incident = Incident(
            organization_id=job.organization_id,
            device_id=device.id,
            title=f"{device.name} is down",
            severity="critical",
        )
        self.db.add(incident)
