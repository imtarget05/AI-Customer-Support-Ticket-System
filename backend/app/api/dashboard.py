from fastapi import APIRouter, Depends

from app.deps import require_agent
from app.schemas import DashboardStats
from app.services import ticket_service
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db), agent=Depends(require_agent)) -> DashboardStats:
    return DashboardStats(**ticket_service.get_stats(db))
