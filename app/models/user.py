from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="viewer", nullable=False)  # admin, manager, viewer
    is_active = Column(Boolean, default=True)

    reports = relationship("Report", back_populates="creator", cascade="all, delete-orphan")
    acknowledged_alerts = relationship("Alert", back_populates="acknowledger")

