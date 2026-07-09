from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.models.driver import Driver
from app.repositories import alert_repo, driver_repo

VIOLATION_PENALTIES = {
    "drowsiness": 10.0,
    "phone_usage": 15.0,
    "seatbelt_absent": 10.0,
    "distraction": 5.0,
    "smoking": 5.0,
    "drinking": 5.0,
    "lane_departure": 5.0,
    "speed_violation": 10.0
}

class AlertService:
    def create_alert(
        self, db: Session, *, trip_id: Optional[int], driver_id: int, vehicle_id: int,
        type: str, severity: str, snapshot_url: Optional[str] = None
    ) -> Alert:
        # Create alert entry
        alert = Alert(
            trip_id=trip_id,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            type=type,
            severity=severity,
            status="active",
            snapshot_url=snapshot_url
        )
        db.add(alert)
        
        # Adjust driver's safety score and infraction counts
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if driver:
            penalty = VIOLATION_PENALTIES.get(type, 5.0)
            driver.safety_score = max(0.0, driver.safety_score - penalty)
            driver.total_violations += 1
            db.add(driver)
            
        db.commit()
        db.refresh(alert)
        return alert

    def acknowledge_alert(self, db: Session, *, alert_id: int, user_id: int) -> Optional[Alert]:
        alert = alert_repo.get(db, id=alert_id)
        if not alert:
            return None
        
        alert.status = "acknowledged"
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def get_active_alerts(self, db: Session) -> List[Alert]:
        return alert_repo.get_alerts_by_filters(db, status="active")

    def get_all_alerts(self, db: Session, skip: int = 0, limit: int = 100) -> List[Alert]:
        return alert_repo.get_multi(db, skip=skip, limit=limit)

alert_service = AlertService()
