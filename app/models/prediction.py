from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Feature Inputs
    drowsiness_score = Column(Float, default=0.0)
    phone_usage_frequency = Column(Float, default=0.0)
    seatbelt_present = Column(Boolean, default=True)
    lane_departure_count = Column(Integer, default=0)
    speed = Column(Float, default=0.0)
    distraction_score = Column(Float, default=0.0)
    
    # Output Risk level
    risk_level = Column(String, nullable=False)  # low, medium, high, critical
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    trip = relationship("Trip", back_populates="predictions")
    driver = relationship("Driver", back_populates="predictions")
    vehicle = relationship("Vehicle", back_populates="predictions")

