from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class VehicleBase(BaseModel):
    vin: str
    plate_number: str
    make: str
    model: str
    year: int
    status: str = "active"  # active, maintenance, inactive

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    status: Optional[str] = None
    current_speed: Optional[float] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None

class VehicleResponse(VehicleBase):
    id: int
    current_speed: float
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
