from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class DriverBase(BaseModel):
    employee_id: str
    name: str
    license_number: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    current_status: str = "active"  # active, inactive, on_trip, resting

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    name: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    current_status: Optional[str] = None
    safety_score: Optional[float] = None
    total_trips: Optional[int] = None
    total_violations: Optional[int] = None

class DriverResponse(DriverBase):
    id: int
    safety_score: float
    total_trips: int
    total_violations: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
