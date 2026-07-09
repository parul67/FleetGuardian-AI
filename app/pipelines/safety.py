import cv2
import base64
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.cv.detector import driver_cv_detector
from app.ml.risk_predictor import accident_risk_predictor
from app.services.alert_service import alert_service

class SafetyPipeline:
    def process_driving_frame(
        self, db: Session, *, frame, telemetry: Dict[str, Any],
        trip_id: Optional[int], driver_id: int, vehicle_id: int
    ) -> Dict[str, Any]:
        """
        Main pipeline execution:
        Frame -> CV Engine -> Feature Extraction -> ML Risk Prediction -> Alert Engine -> Output Pack
        """
        # 1. Run CV detector on frame
        annotated_frame, cv_metrics = driver_cv_detector.process_frame(frame)
        
        # Merge telemetry (speed, location) with CV metrics
        speed = telemetry.get("speed", cv_metrics.get("speed", 60.0))
        cv_metrics["speed"] = speed

        # 2. Formulate inputs for ML Risk Predictor
        ml_inputs = {
            "drowsiness_score": cv_metrics["drowsiness_score"],
            "phone_usage_frequency": 1.0 if cv_metrics["phone_detected"] else 0.0,
            "seatbelt_present": cv_metrics["seatbelt_present"],
            "lane_departure_count": 1 if abs(cv_metrics["lane_offset"]) > 0.2 else 0,
            "speed": cv_metrics["speed"],
            "distraction_score": cv_metrics["distraction_score"]
        }
        
        # 3. Predict Accident Risk Level
        risk_level = accident_risk_predictor.predict_risk(ml_inputs)
        
        # 4. Evaluate Alert Triggers
        triggered_alerts = []
        
        # Drowsiness alert
        if cv_metrics["drowsiness_score"] > 0.5:
            alert = alert_service.create_alert(
                db, trip_id=trip_id, driver_id=driver_id, vehicle_id=vehicle_id,
                type="drowsiness", severity="critical"
            )
            triggered_alerts.append(alert)
            
        # Phone distraction alert
        if cv_metrics["phone_detected"]:
            alert = alert_service.create_alert(
                db, trip_id=trip_id, driver_id=driver_id, vehicle_id=vehicle_id,
                type="phone_usage", severity="high"
            )
            triggered_alerts.append(alert)

        # Seatbelt alert
        if not cv_metrics["seatbelt_present"]:
            alert = alert_service.create_alert(
                db, trip_id=trip_id, driver_id=driver_id, vehicle_id=vehicle_id,
                type="seatbelt_absent", severity="high"
            )
            triggered_alerts.append(alert)

        # Lane departure
        if abs(cv_metrics["lane_offset"]) > 0.25:
            alert = alert_service.create_alert(
                db, trip_id=trip_id, driver_id=driver_id, vehicle_id=vehicle_id,
                type="lane_departure", severity="medium"
            )
            triggered_alerts.append(alert)

        # Speed violation
        if speed > 80.0:
            alert = alert_service.create_alert(
                db, trip_id=trip_id, driver_id=driver_id, vehicle_id=vehicle_id,
                type="speed_violation", severity="medium"
            )
            triggered_alerts.append(alert)

        # 5. Convert annotated frame to Base64 jpeg string for WebSockets transmission
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "image": f"data:image/jpeg;base64,{jpg_as_text}",
            "metrics": cv_metrics,
            "risk_level": risk_level,
            "alerts": [
                {
                    "id": a.id,
                    "type": a.type,
                    "severity": a.severity,
                    "timestamp": str(a.timestamp)
                }
                for a in triggered_alerts
            ]
        }

safety_pipeline = SafetyPipeline()
