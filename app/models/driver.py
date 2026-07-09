from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    license_number = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    current_status = Column(String, default="active", nullable=False)  # active, inactive, on_trip, resting
    safety_score = Column(Float, default=100.0, nullable=False)
    total_trips = Column(Integer, default=0, nullable=False)
    total_violations = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    trips = relationship("Trip", back_populates="driver", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="driver", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="driver", cascade="all, delete-orphan")

