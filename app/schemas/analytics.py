from datetime import date
from pydantic import BaseModel

class AnalyticsResponse(BaseModel):
    id: int
    date: date
    total_alerts: int
    total_trips: int
    total_drowsiness_events: int
    total_phone_usage_events: int
    total_overspeed_events: int
    total_lane_departures: int
    total_seatbelt_violations: int
    average_driver_score: float

    class Config:
        from_attributes = True
