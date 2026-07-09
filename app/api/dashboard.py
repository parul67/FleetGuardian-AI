from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.analytics_service import analytics_service
from app.services.auth_service import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.get("/")
def get_dashboard_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Exposes aggregate KPI summaries, alerts totals, and driver scores for the dashboard."""
    return analytics_service.get_dashboard_summary(db)
