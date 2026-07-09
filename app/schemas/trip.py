from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class TripBase(BaseModel):
    driver_id: int
    vehicle_id: int
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    status: str = "active"

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    end_time: Optional[datetime] = None
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    distance_km: Optional[float] = None
    status: Optional[str] = None
    average_speed: Optional[float] = None
    max_speed: Optional[float] = None

class TripResponse(TripBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    distance_km: float
    average_speed: float
    max_speed: float

    class Config:
        from_attributes = True
