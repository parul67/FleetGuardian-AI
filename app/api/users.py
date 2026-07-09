from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.fleet_repos import user_repo
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.auth_service import get_current_active_user, RoleChecker
from app.models.user import User
from app.core import security

router = APIRouter()

# Permissions: only admin can manage users
admin_dependency = Depends(RoleChecker(["admin"]))
read_dependency = Depends(get_current_active_user)

@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: User = admin_dependency
):
    """Retrieve users."""
    return user_repo.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate, 
    db: Session = Depends(get_db), 
    current_user: User = admin_dependency
):
    """Create new user."""
    existing = user_repo.get_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )
    user_in.password = security.get_password_hash(user_in.password)
    return user_repo.create(db, obj_in=user_in)

@router.get("/{id}", response_model=UserResponse)
def read_user(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: User = admin_dependency
):
    """Get a specific user by id."""
    user = user_repo.get(db, id=id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/{id}", response_model=UserResponse)
def update_user(
    id: int, 
    user_in: UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = admin_dependency
):
    """Update a user."""
    user = user_repo.get(db, id=id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user_in.password:
        user_in.password = security.get_password_hash(user_in.password)
        
    return user_repo.update(db, db_obj=user, obj_in=user_in)

@router.delete("/{id}", response_model=UserResponse)
def delete_user(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: User = admin_dependency
):
    """Delete a user."""
    user = user_repo.get(db, id=id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own user account.")
    return user_repo.remove(db, id=id)
