from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class PredictionCreate(BaseModel):
    trip_id: Optional[int] = None
    driver_id: int
    vehicle_id: int
    drowsiness_score: float
    phone_usage_frequency: float
    seatbelt_present: bool
    lane_departure_count: int
    speed: float
    distraction_score: float
    time_of_day: Optional[str] = "day"
    weather: Optional[str] = "clear"

class PredictionResponse(BaseModel):
    id: int
    trip_id: Optional[int] = None
    driver_id: int
    vehicle_id: int
    drowsiness_score: float
    phone_usage_frequency: float
    seatbelt_present: bool
    lane_departure_count: int
    speed: float
    distraction_score: float
    risk_level: str
    timestamp: datetime

    class Config:
        from_attributes = True
