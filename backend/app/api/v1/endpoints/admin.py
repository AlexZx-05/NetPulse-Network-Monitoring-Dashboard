from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_roles
from app.db.session import get_db
from app.domain.models import Device, Incident, User, UserRole

router = APIRouter()


@router.get("/dashboard")
def admin_dashboard(
    current: CurrentUser = Depends(require_roles(UserRole.owner, UserRole.admin)),
    db: Session = Depends(get_db),
):
    org_id = current.organization_id
    return {
        "users": db.scalar(select(func.count(User.id)).where(User.organization_id == org_id)) or 0,
        "devices": db.scalar(select(func.count(Device.id)).where(Device.organization_id == org_id)) or 0,
        "open_incidents": db.scalar(select(func.count(Incident.id)).where(Incident.organization_id == org_id)) or 0,
    }
