from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories import alert_repo
from app.schemas.alert import AlertResponse
from app.services.alert_service import alert_service
from app.services.auth_service import get_current_active_user
from app.models.user import User

router = APIRouter()

read_dependency = Depends(get_current_active_user)

@router.get("/", response_model=List[AlertResponse])
def read_alerts(
    type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    driver_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = read_dependency
):
    """Retrieves list of safety alerts, filtered by type, severity, status, or driver."""
    return alert_repo.get_alerts_by_filters(
        db, type=type, severity=severity, status=status,
        driver_id=driver_id, skip=skip, limit=limit
    )

@router.post("/{id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = read_dependency
):
    """Acknowledge a specific alert, tagging the user who authorized the dismiss."""
    alert = alert_service.acknowledge_alert(db, alert_id=id, user_id=current_user.id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.get("/stats")
def read_alert_stats(db: Session = Depends(get_db), current_user: User = read_dependency):
    """Get total alerts breakdown by violation types."""
    return alert_repo.get_counts_by_type(db)
