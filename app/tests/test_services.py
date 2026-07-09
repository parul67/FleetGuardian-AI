import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.services.alert_service import alert_service
from app.services.analytics_service import analytics_service

# Setup mock SQLite session
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_services.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_alert_score_penalty(db_session):
    # 1. Create driver
    driver = Driver(
        employee_id="FG-D999",
        name="John Test",
        license_number="LIC-1234",
        safety_score=100.0,
        total_violations=0
    )
    db_session.add(driver)
    
    # 2. Create vehicle
    vehicle = Vehicle(
        vin="VIN1234567890",
        plate_number="MOCK-001",
        make="Volvo",
        model="Truck",
        year=2021
    )
    db_session.add(vehicle)
    db_session.commit()
    
    # 3. Create a phone usage alert
    alert = alert_service.create_alert(
        db_session,
        trip_id=None,
        driver_id=driver.id,
        vehicle_id=vehicle.id,
        type="phone_usage",
        severity="high"
    )
    
    assert alert.id is not None
    assert alert.status == "active"
    
    # Refetch driver and assert safety score dropped by 15 points
    db_session.refresh(driver)
    assert driver.safety_score == 85.0
    assert driver.total_violations == 1

def test_dashboard_summary_empty(db_session):
    summary = analytics_service.get_dashboard_summary(db_session)
    assert summary["vehicles"]["total"] == 0
    assert summary["driver_scores"]["average"] == 100.0
