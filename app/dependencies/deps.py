from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import get_current_user, get_current_active_user, RoleChecker
from app.models.user import User

def get_session() -> Generator:
    """Dependency to get a database session. Alias for get_db."""
    yield from get_db()

def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Dependency to ensure the current user is an admin."""
    if current_user.role != "admin":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
        )
    return current_user
