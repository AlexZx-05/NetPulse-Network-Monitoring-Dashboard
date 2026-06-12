from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict

from app.domain.models import IncidentStatus, MonitorType, Status, UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=10, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: UUID
    organization_id: UUID
    email: EmailStr
    full_name: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class DeviceCreate(BaseModel):
    name: str
    target: str
    tags: dict = {}


class DeviceRead(BaseModel):
    id: UUID
    name: str
    target: str
    status: Status
    tags: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MonitoringJobCreate(BaseModel):
    device_id: UUID
    monitor_type: MonitorType
    interval_seconds: int = Field(default=60, ge=15, le=3600)
    timeout_seconds: int = Field(default=5, ge=1, le=60)
    config: dict = {}


class MonitoringJobRead(BaseModel):
    id: UUID
    device_id: UUID
    monitor_type: MonitorType
    interval_seconds: int
    timeout_seconds: int
    config: dict
    enabled: bool

    model_config = ConfigDict(from_attributes=True)


class MetricRead(BaseModel):
    id: UUID
    job_id: UUID
    status: Status
    latency_ms: float | None
    packet_loss: float
    detail: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentRead(BaseModel):
    id: UUID
    device_id: UUID
    title: str
    status: IncidentStatus
    severity: str
    opened_at: datetime
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    total_devices: int
    up: int
    degraded: int
    down: int
    unknown: int
    uptime_percentage: float
    avg_latency_ms: float | None
