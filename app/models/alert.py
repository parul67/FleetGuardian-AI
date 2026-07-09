from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False)  # drowsiness, phone_usage, seatbelt_absent, distraction, smoking, drinking, lane_departure, speed_violation
    severity = Column(String, default="medium", nullable=False, index=True)  # low, medium, high, critical
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    status = Column(String, default="active", nullable=False, index=True)  # active, acknowledged
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    snapshot_url = Column(String, nullable=True)  # path or url to saved frame

    trip = relationship("Trip", back_populates="alerts")
    driver = relationship("Driver", back_populates="alerts")
    vehicle = relationship("Vehicle", back_populates="alerts")
    acknowledger = relationship("User", back_populates="acknowledged_alerts")

