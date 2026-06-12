from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.repositories.monitoring import MetricRepository

router = APIRouter()


@router.get("/sla")
def sla_report(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    return {
        "organization_id": str(current.organization_id),
        "period_start": (now - timedelta(days=30)).isoformat(),
        "period_end": now.isoformat(),
        "summary": MetricRepository(db).summary(current.organization_id),
    }


@router.get("/csv")
def export_csv(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = ["metric_id,job_id,status,latency_ms,packet_loss,created_at"]
    for metric in MetricRepository(db).recent(current.organization_id, limit=1000):
        rows.append(
            f"{metric.id},{metric.job_id},{metric.status.value},{metric.latency_ms or ''},{metric.packet_loss},{metric.created_at.isoformat()}"
        )
    return Response("\n".join(rows), media_type="text/csv")


@router.get("/pdf")
def export_pdf_placeholder(current: CurrentUser = Depends(get_current_user)):
    return {
        "status": "queued",
        "message": "PDF generation should be handled by a dedicated worker using WeasyPrint or ReportLab.",
        "organization_id": str(current.organization_id),
    }
