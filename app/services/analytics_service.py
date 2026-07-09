from datetime import date, datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.alert import Alert
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.trip import Trip
from app.models.analytics import Analytics

class AnalyticsService:
    def get_dashboard_summary(self, db: Session) -> Dict[str, Any]:
        """Fetches high-level metrics for dashboard home page."""
        # Active Vehicles (associated with active trips)
        active_trips_count = db.query(func.count(Trip.id)).filter(Trip.status == "active").scalar() or 0
        total_vehicles = db.query(func.count(Vehicle.id)).scalar() or 0
        
        # Drivers score summary
        drivers_stats = db.query(
            func.avg(Driver.safety_score),
            func.min(Driver.safety_score),
            func.max(Driver.safety_score)
        ).all()
        
        avg_score = round(drivers_stats[0][0] or 100.0, 2)
        min_score = round(drivers_stats[0][1] or 100.0, 2)
        max_score = round(drivers_stats[0][2] or 100.0, 2)

        # Leaderboard
        safest_drivers = db.query(Driver).order_by(Driver.safety_score.desc()).limit(5).all()
        riskiest_drivers = db.query(Driver).order_by(Driver.safety_score.asc()).limit(5).all()

        # Alert aggregations
        total_alerts = db.query(func.count(Alert.id)).scalar() or 0
        active_alerts = db.query(func.count(Alert.id)).filter(Alert.status == "active").scalar() or 0
        
        # Breakdown by alert type
        alert_breakdown = db.query(Alert.type, func.count(Alert.id)).group_by(Alert.type).all()
        breakdown_dict = {
            "drowsiness": 0,
            "phone_usage": 0,
            "seatbelt_absent": 0,
            "distraction": 0,
            "smoking": 0,
            "drinking": 0,
            "lane_departure": 0,
            "speed_violation": 0
        }
        for item in alert_breakdown:
            if item[0] in breakdown_dict:
                breakdown_dict[item[0]] = item[1]

        return {
            "vehicles": {
                "active": active_trips_count,
                "total": total_vehicles,
                "idle": max(0, total_vehicles - active_trips_count)
            },
            "alerts": {
                "total": total_alerts,
                "active": active_alerts,
                "breakdown": breakdown_dict
            },
            "driver_scores": {
                "average": avg_score,
                "lowest": min_score,
                "highest": max_score
            },
            "leaderboard": {
                "safest": [
                    {"id": d.id, "name": d.name, "score": d.safety_score, "violations": d.total_violations}
                    for d in safest_drivers
                ],
                "riskiest": [
                    {"id": d.id, "name": d.name, "score": d.safety_score, "violations": d.total_violations}
                    for d in riskiest_drivers
                ]
            }
        }

    def generate_daily_rollup(self, db: Session, target_date: date) -> Analytics:
        """Rolls up telemetry logs and alerts into a single day record."""
        # Find if rollup already exists
        rollup = db.query(Analytics).filter(Analytics.date == target_date).first()
        if not rollup:
            rollup = Analytics(date=target_date)
            db.add(rollup)
            
        # Get start/end timestamps
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())
        
        # Aggregate alerts
        alerts = db.query(Alert).filter(Alert.timestamp >= start_dt, Alert.timestamp <= end_dt).all()
        rollup.total_alerts = len(alerts)
        rollup.total_drowsiness_events = sum(1 for a in alerts if a.type == "drowsiness")
        rollup.total_phone_usage_events = sum(1 for a in alerts if a.type == "phone_usage")
        rollup.total_overspeed_events = sum(1 for a in alerts if a.type == "speed_violation")
        rollup.total_lane_departures = sum(1 for a in alerts if a.type == "lane_departure")
        rollup.total_seatbelt_violations = sum(1 for a in alerts if a.type == "seatbelt_absent")
        
        # Aggregate active trips on that day
        trips_count = db.query(func.count(Trip.id)).filter(
            Trip.start_time <= end_dt,
            (Trip.end_time == None) | (Trip.end_time >= start_dt)
        ).scalar() or 0
        rollup.total_trips = trips_count
        
        # Get average driver score
        avg_score = db.query(func.avg(Driver.safety_score)).scalar()
        rollup.average_driver_score = round(avg_score or 100.0, 2)
        
        db.commit()
        db.refresh(rollup)
        return rollup

    def get_historical_trends(self, db: Session, days: int = 7) -> List[Dict[str, Any]]:
        """Returns rollup data for the last N days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Run daily rollups for any missing dates in range to keep analytics current
        curr = start_date
        while curr <= end_date:
            self.generate_daily_rollup(db, curr)
            curr += timedelta(days=1)

        records = db.query(Analytics).filter(
            Analytics.date >= start_date,
            Analytics.date <= end_date
        ).order_by(Analytics.date.asc()).all()

        return [
            {
                "date": str(r.date),
                "total_alerts": r.total_alerts,
                "total_trips": r.total_trips,
                "drowsiness": r.total_drowsiness_events,
                "phone_usage": r.total_phone_usage_events,
                "overspeed": r.total_overspeed_events,
                "lane_departure": r.total_lane_departures,
                "seatbelt": r.total_seatbelt_violations,
                "average_score": r.average_driver_score
            }
            for r in records
        ]

analytics_service = AnalyticsService()
