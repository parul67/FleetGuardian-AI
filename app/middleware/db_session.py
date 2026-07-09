from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.database.session import SessionLocal

class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = None
        try:
            request.state.db = SessionLocal()
            response = await call_next(request)
        finally:
            if hasattr(request.state, "db"):
                request.state.db.close()
        return response
