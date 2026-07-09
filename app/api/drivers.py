from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories import driver_repo
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse
from app.services.auth_service import get_current_active_user, RoleChecker
from app.models.user import User

router = APIRouter()

# Permissions setups
read_dependency = Depends(get_current_active_user)
write_dependency = Depends(RoleChecker(["admin", "manager"]))

@router.get("/", response_model=List[DriverResponse])
def read_drivers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = read_dependency):
    return driver_repo.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
def create_driver(driver_in: DriverCreate, db: Session = Depends(get_db), current_user: User = write_dependency):
    existing = driver_repo.get_by_employee_id(db, driver_in.employee_id)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver ID already registered.")
    return driver_repo.create(db, obj_in=driver_in)

@router.get("/{id}", response_model=DriverResponse)
def read_driver(id: int, db: Session = Depends(get_db), current_user: User = read_dependency):
    driver = driver_repo.get(db, id=id)
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver

@router.put("/{id}", response_model=DriverResponse)
def update_driver(id: int, driver_in: DriverUpdate, db: Session = Depends(get_db), current_user: User = write_dependency):
    driver = driver_repo.get(db, id=id)
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver_repo.update(db, db_obj=driver, obj_in=driver_in)

@router.delete("/{id}", response_model=DriverResponse)
def delete_driver(id: int, db: Session = Depends(get_db), current_user: User = write_dependency):
    driver = driver_repo.get(db, id=id)
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver_repo.remove(db, id=id)
