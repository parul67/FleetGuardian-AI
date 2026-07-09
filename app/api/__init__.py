from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.drivers import router as drivers_router
from app.api.vehicles import router as vehicles_router
from app.api.trips import router as trips_router
from app.api.predictions import router as predictions_router
from app.api.alerts import router as alerts_router
from app.api.analytics import router as analytics_router
from app.api.reports import router as reports_router
from app.api.dashboard import router as dashboard_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(drivers_router, prefix="/drivers", tags=["drivers"])
api_router.include_router(vehicles_router, prefix="/vehicles", tags=["vehicles"])
api_router.include_router(trips_router, prefix="/trips", tags=["trips"])
api_router.include_router(predictions_router, prefix="/predict", tags=["predictions"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
