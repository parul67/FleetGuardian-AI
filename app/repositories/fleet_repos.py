from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.repositories.base import BaseRepository
from app.models.user import User
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.trip import Trip
from app.models.alert import Alert
from app.models.prediction import Prediction
from app.models.analytics import Analytics
from app.models.report import Report
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.driver import DriverCreate, DriverUpdate
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.schemas.trip import TripCreate, TripUpdate
from app.schemas.alert import AlertCreate, AlertAcknowledge
from app.schemas.prediction import PredictionCreate
from app.schemas.analytics import AnalyticsResponse
from app.schemas.report import ReportCreate

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(self.model).filter(self.model.email == email).first()

class DriverRepository(BaseRepository[Driver, DriverCreate, DriverUpdate]):
    def get_by_employee_id(self, db: Session, employee_id: str) -> Optional[Driver]:
        return db.query(self.model).filter(self.model.employee_id == employee_id).first()

class VehicleRepository(BaseRepository[Vehicle, VehicleCreate, VehicleUpdate]):
    def get_by_vin(self, db: Session, vin: str) -> Optional[Vehicle]:
        return db.query(self.model).filter(self.model.vin == vin).first()

    def get_by_plate(self, db: Session, plate_number: str) -> Optional[Vehicle]:
        return db.query(self.model).filter(self.model.plate_number == plate_number).first()

class TripRepository(BaseRepository[Trip, TripCreate, TripUpdate]):
    def get_active_trip_by_driver(self, db: Session, driver_id: int) -> Optional[Trip]:
        return db.query(self.model).filter(self.model.driver_id == driver_id, self.model.status == "active").first()

    def get_active_trip_by_vehicle(self, db: Session, vehicle_id: int) -> Optional[Trip]:
        return db.query(self.model).filter(self.model.vehicle_id == vehicle_id, self.model.status == "active").first()

class AlertRepository(BaseRepository[Alert, AlertCreate, AlertAcknowledge]):
    def get_alerts_by_filters(
        self, db: Session, *, type: Optional[str] = None, severity: Optional[str] = None,
        status: Optional[str] = None, driver_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[Alert]:
        query = db.query(self.model)
        if type:
            query = query.filter(self.model.type == type)
        if severity:
            query = query.filter(self.model.severity == severity)
        if status:
            query = query.filter(self.model.status == status)
        if driver_id:
            query = query.filter(self.model.driver_id == driver_id)
        return query.order_by(self.model.timestamp.desc()).offset(skip).limit(limit).all()

    def get_counts_by_type(self, db: Session) -> dict:
        results = db.query(self.model.type, func.count(self.model.id)).group_by(self.model.type).all()
        return {r[0]: r[1] for r in results}

class PredictionRepository(BaseRepository[Prediction, PredictionCreate, None]):
    def get_latest_predictions_by_driver(self, db: Session, driver_id: int, limit: int = 10) -> List[Prediction]:
        return db.query(self.model).filter(self.model.driver_id == driver_id).order_by(self.model.timestamp.desc()).limit(limit).all()

class AnalyticsRepository(BaseRepository[Analytics, AnalyticsResponse, None]):
    def get_by_date_range(self, db: Session, start_date: date, end_date: date) -> List[Analytics]:
        return db.query(self.model).filter(self.model.date >= start_date, self.model.date <= end_date).order_by(self.model.date.asc()).all()

class ReportRepository(BaseRepository[Report, ReportCreate, None]):
    pass

# Instantiate singletons for convenience
user_repo = UserRepository(User)
driver_repo = DriverRepository(Driver)
vehicle_repo = VehicleRepository(Vehicle)
trip_repo = TripRepository(Trip)
alert_repo = AlertRepository(Alert)
prediction_repo = PredictionRepository(Prediction)
analytics_repo = AnalyticsRepository(Analytics)
report_repo = ReportRepository(Report)
