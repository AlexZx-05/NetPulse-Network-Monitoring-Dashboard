from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.domain.models import Incident
from app.domain.schemas import IncidentRead

router = APIRouter()


@router.get("", response_model=list[IncidentRead])
def list_incidents(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = (
        select(Incident)
        .where(Incident.organization_id == current.organization_id)
        .order_by(Incident.opened_at.desc())
        .limit(100)
    )
    return list(db.scalars(stmt))
