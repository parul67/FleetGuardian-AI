from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.fleet_repos import trip_repo, driver_repo, vehicle_repo
from app.schemas.trip import TripCreate, TripUpdate, TripResponse
from app.services.auth_service import get_current_active_user, RoleChecker
from app.models.user import User
from app.models.trip import Trip

router = APIRouter()

read_dependency = Depends(get_current_active_user)
write_dependency = Depends(RoleChecker(["admin", "manager"]))

@router.get("/", response_model=List[TripResponse])
def read_trips(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: User = read_dependency
):
    """Retrieve trips."""
    return trip_repo.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def start_trip(
    trip_in: TripCreate, 
    db: Session = Depends(get_db), 
    current_user: User = write_dependency
):
    """Start a new trip."""
    # Validate driver and vehicle exist
    driver = driver_repo.get(db, id=trip_in.driver_id)
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        
    vehicle = vehicle_repo.get(db, id=trip_in.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Check if driver or vehicle already have an active trip
    if trip_repo.get_active_trip_by_driver(db, driver_id=trip_in.driver_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver already has an active trip.")
    
    if trip_repo.get_active_trip_by_vehicle(db, vehicle_id=trip_in.vehicle_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vehicle is already on an active trip.")

    # Update statuses
    driver.current_status = "on_trip"
    vehicle.status = "active"
    db.add(driver)
    db.add(vehicle)
    db.commit()

    return trip_repo.create(db, obj_in=trip_in)

@router.get("/{id}", response_model=TripResponse)
def read_trip(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: User = read_dependency
):
    """Get a specific trip by id."""
    trip = trip_repo.get(db, id=id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip

@router.put("/{id}/end", response_model=TripResponse)
def end_trip(
    id: int, 
    trip_in: TripUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = write_dependency
):
    """End a trip and update driver/vehicle statuses."""
    trip = trip_repo.get(db, id=id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if trip.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip is already completed.")
    
    # End trip
    trip_in.status = "completed"
    if not trip_in.end_time:
        trip_in.end_time = datetime.now(timezone.utc)
        
    updated_trip = trip_repo.update(db, db_obj=trip, obj_in=trip_in)
    
    # Update driver and vehicle statuses
    driver = driver_repo.get(db, id=updated_trip.driver_id)
    if driver:
        driver.current_status = "active"
        driver.total_trips += 1
        db.add(driver)
        
    vehicle = vehicle_repo.get(db, id=updated_trip.vehicle_id)
    if vehicle:
        vehicle.status = "active"
        db.add(vehicle)
        
    db.commit()
    
    return updated_trip
