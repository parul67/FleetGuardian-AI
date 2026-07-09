from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class AlertBase(BaseModel):
    trip_id: Optional[int] = None
    driver_id: int
    vehicle_id: int
    type: str
    severity: str = "medium"
    snapshot_url: Optional[str] = None

class AlertCreate(AlertBase):
    pass

class AlertAcknowledge(BaseModel):
    pass

class AlertResponse(AlertBase):
    id: int
    timestamp: datetime
    status: str
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None

    class Config:
        from_attributes = True
