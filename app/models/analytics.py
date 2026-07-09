from sqlalchemy import Column, Integer, Float, Date
from app.database.session import Base

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    
    # Aggregated metrics
    total_alerts = Column(Integer, default=0, nullable=False)
    total_trips = Column(Integer, default=0, nullable=False)
    total_drowsiness_events = Column(Integer, default=0, nullable=False)
    total_phone_usage_events = Column(Integer, default=0, nullable=False)
    total_overspeed_events = Column(Integer, default=0, nullable=False)
    total_lane_departures = Column(Integer, default=0, nullable=False)
    total_seatbelt_violations = Column(Integer, default=0, nullable=False)
    average_driver_score = Column(Float, default=100.0, nullable=False)
