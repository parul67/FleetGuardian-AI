from app.schemas.user import UserBase, UserCreate, UserUpdate, UserResponse, UserLogin
from app.schemas.token import Token, TokenPayload
from app.schemas.driver import DriverBase, DriverCreate, DriverUpdate, DriverResponse
from app.schemas.vehicle import VehicleBase, VehicleCreate, VehicleUpdate, VehicleResponse
from app.schemas.trip import TripBase, TripCreate, TripUpdate, TripResponse
from app.schemas.alert import AlertBase, AlertCreate, AlertAcknowledge, AlertResponse
from app.schemas.prediction import PredictionCreate, PredictionResponse
from app.schemas.analytics import AnalyticsResponse
from app.schemas.report import ReportCreate, ReportResponse

__all__ = [
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "Token", "TokenPayload",
    "DriverBase", "DriverCreate", "DriverUpdate", "DriverResponse",
    "VehicleBase", "VehicleCreate", "VehicleUpdate", "VehicleResponse",
    "TripBase", "TripCreate", "TripUpdate", "TripResponse",
    "AlertBase", "AlertCreate", "AlertAcknowledge", "AlertResponse",
    "PredictionCreate", "PredictionResponse",
    "AnalyticsResponse",
    "ReportCreate", "ReportResponse"
]
