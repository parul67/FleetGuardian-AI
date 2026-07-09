from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.analytics_service import analytics_service
from app.services.auth_service import get_current_active_user
from app.models.user import User

router = APIRouter()

read_dependency = Depends(get_current_active_user)

@router.get("/daily")
def get_daily_trends(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = read_dependency
):
    """Returns rollup metrics for the last N days."""
    return analytics_service.get_historical_trends(db, days=days)

@router.get("/monthly")
def get_monthly_trends(
    db: Session = Depends(get_db),
    current_user: User = read_dependency
):
    """Returns rollup metrics grouped by month for the last 6 months."""
    # Group the daily trends into monthly summaries
    trends = analytics_service.get_historical_trends(db, days=180)
    monthly_data = {}
    for t in trends:
        # Date format is YYYY-MM-DD
        year_month = t["date"][:7] # YYYY-MM
        if year_month not in monthly_data:
            monthly_data[year_month] = {
                "month": year_month,
                "total_alerts": 0,
                "total_trips": 0,
                "drowsiness": 0,
                "phone_usage": 0,
                "overspeed": 0,
                "lane_departure": 0,
                "seatbelt": 0,
                "score_sum": 0.0,
                "count": 0
            }
        
        m = monthly_data[year_month]
        m["total_alerts"] += t["total_alerts"]
        m["total_trips"] += t["total_trips"]
        m["drowsiness"] += t["drowsiness"]
        m["phone_usage"] += t["phone_usage"]
        m["overspeed"] += t["overspeed"]
        m["lane_departure"] += t["lane_departure"]
        m["seatbelt"] += t["seatbelt"]
        m["score_sum"] += t["average_score"]
        m["count"] += 1

    result = []
    for month, m in sorted(monthly_data.items()):
        result.append({
            "month": m["month"],
            "total_alerts": m["total_alerts"],
            "total_trips": m["total_trips"],
            "drowsiness": m["drowsiness"],
            "phone_usage": m["phone_usage"],
            "overspeed": m["overspeed"],
            "lane_departure": m["lane_departure"],
            "seatbelt": m["seatbelt"],
            "average_score": round(m["score_sum"] / max(1, m["count"]), 2)
        })
    return result

@router.get("/live")
def get_live_metrics(
    db: Session = Depends(get_db),
    current_user: User = read_dependency
):
    """Returns active vehicle speeds, coordinates, and real-time safety scores."""
    return analytics_service.get_dashboard_summary(db)
