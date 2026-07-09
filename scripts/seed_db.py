import sys
from pathlib import Path

# Add root folder to python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.trip import Trip

def seed_database():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    try:
        # 1. Seed Users
        if db.query(User).filter(User.email == "admin@fleetguardian.ai").first() is None:
            admin_user = User(
                email="admin@fleetguardian.ai",
                hashed_password=get_password_hash("password123"),
                full_name="Fleet Administrator",
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            print("Added admin user: admin@fleetguardian.ai / password123")
            
        # 2. Seed Drivers
        if db.query(Driver).count() == 0:
            drivers = [
                Driver(employee_id="FG-D101", name="Marcus Vance", license_number="DL-88902", phone="555-0192", email="marcus.v@fleet.com", current_status="active", safety_score=97.5, total_trips=28, total_violations=2),
                Driver(employee_id="FG-D102", name="Sarah Jenkins", license_number="DL-44391", phone="555-0145", email="s.jenkins@fleet.com", current_status="on_trip", safety_score=94.2, total_trips=34, total_violations=3),
                Driver(employee_id="FG-D103", name="Elena Rostova", license_number="DL-11023", phone="555-0168", email="elena.r@fleet.com", current_status="resting", safety_score=88.0, total_trips=12, total_violations=5),
                Driver(employee_id="FG-D104", name="David Kross", license_number="DL-55902", phone="555-0177", email="d.kross@fleet.com", current_status="on_trip", safety_score=68.5, total_trips=45, total_violations=22),
            ]
            db.add_all(drivers)
            print(f"Seeded {len(drivers)} drivers.")
            
        # 3. Seed Vehicles
        if db.query(Vehicle).count() == 0:
            vehicles = [
                Vehicle(vin="1FVACWDB230912389", plate_number="FL-8890", make="Freightliner", model="Cascadia", year=2022, status="active", current_speed=0.0, current_latitude=34.0522, current_longitude=-118.2437),
                Vehicle(vin="4V4NC9EJ430238902", plate_number="VL-5567", make="Volvo", model="VNL 860", year=2023, status="active", current_speed=62.5, current_latitude=40.7128, current_longitude=-74.0060),
                Vehicle(vin="1XP5D49X540981290", plate_number="PB-1122", make="Peterbilt", model="579", year=2021, status="maintenance", current_speed=0.0, current_latitude=41.8781, current_longitude=-87.6298),
                Vehicle(vin="5YJ3E1EA5KF129043", plate_number="TES-909", make="Tesla", model="Semi", year=2024, status="active", current_speed=55.0, current_latitude=37.7749, current_longitude=-122.4194)
            ]
            db.add_all(vehicles)
            print(f"Seeded {len(vehicles)} vehicles.")
            
        db.commit()

        # 4. Seed Active Trips
        # We need drivers and vehicles instantiated to link IDs
        if db.query(Trip).count() == 0:
            sarah = db.query(Driver).filter(Driver.employee_id == "FG-D102").first()
            david = db.query(Driver).filter(Driver.employee_id == "FG-D104").first()
            volvo = db.query(Vehicle).filter(Vehicle.plate_number == "VL-5567").first()
            tesla = db.query(Vehicle).filter(Vehicle.plate_number == "TES-909").first()
            
            if sarah and volvo:
                trip1 = Trip(
                    driver_id=sarah.id,
                    vehicle_id=volvo.id,
                    start_latitude=40.7128,
                    start_longitude=-74.0060,
                    distance_km=145.2,
                    status="active",
                    average_speed=60.0,
                    max_speed=72.0
                )
                db.add(trip1)
            if david and tesla:
                trip2 = Trip(
                    driver_id=david.id,
                    vehicle_id=tesla.id,
                    start_latitude=37.7749,
                    start_longitude=-122.4194,
                    distance_km=210.5,
                    status="active",
                    average_speed=52.0,
                    max_speed=65.0
                )
                db.add(trip2)
            db.commit()
            print("Seeded active trips linking drivers and vehicles.")

        print("Database seeding completed successfully.")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
