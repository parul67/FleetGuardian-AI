from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories import vehicle_repo
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from app.services.auth_service import get_current_active_user, RoleChecker
from app.models.user import User

router = APIRouter()

read_dependency = Depends(get_current_active_user)
write_dependency = Depends(RoleChecker(["admin", "manager"]))

@router.get("/", response_model=List[VehicleResponse])
def read_vehicles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = read_dependency):
    return vehicle_repo.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(vehicle_in: VehicleCreate, db: Session = Depends(get_db), current_user: User = write_dependency):
    existing_vin = vehicle_repo.get_by_vin(db, vehicle_in.vin)
    if existing_vin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="VIN already registered.")
    existing_plate = vehicle_repo.get_by_plate(db, vehicle_in.plate_number)
    if existing_plate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plate number already registered.")
    return vehicle_repo.create(db, obj_in=vehicle_in)

@router.get("/{id}", response_model=VehicleResponse)
def read_vehicle(id: int, db: Session = Depends(get_db), current_user: User = read_dependency):
    vehicle = vehicle_repo.get(db, id=id)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle

@router.put("/{id}", response_model=VehicleResponse)
def update_vehicle(id: int, vehicle_in: VehicleUpdate, db: Session = Depends(get_db), current_user: User = write_dependency):
    vehicle = vehicle_repo.get(db, id=id)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle_repo.update(db, db_obj=vehicle, obj_in=vehicle_in)

@router.delete("/{id}", response_model=VehicleResponse)
def delete_vehicle(id: int, db: Session = Depends(get_db), current_user: User = write_dependency):
    vehicle = vehicle_repo.get(db, id=id)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle_repo.remove(db, id=id)
