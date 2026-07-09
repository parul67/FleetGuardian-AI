import cv2
import numpy as np
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.prediction import PredictionCreate, PredictionResponse
from app.ml.risk_predictor import accident_risk_predictor
from app.pipelines.safety import safety_pipeline
from app.models.prediction import Prediction
from app.services.auth_service import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.post("/predict", response_model=PredictionResponse)
def predict_accident_risk(prediction_in: PredictionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Runs accident risk prediction based on a JSON payload of driver telemetry."""
    inputs = prediction_in.model_dump()
    risk_level = accident_risk_predictor.predict_risk(inputs)
    
    # Save log to database
    db_pred = Prediction(
        trip_id=prediction_in.trip_id,
        driver_id=prediction_in.driver_id,
        vehicle_id=prediction_in.vehicle_id,
        drowsiness_score=prediction_in.drowsiness_score,
        phone_usage_frequency=prediction_in.phone_usage_frequency,
        seatbelt_present=prediction_in.seatbelt_present,
        lane_departure_count=prediction_in.lane_departure_count,
        speed=prediction_in.speed,
        distraction_score=prediction_in.distraction_score,
        risk_level=risk_level
    )
    db.add(db_pred)
    db.commit()
    db.refresh(db_pred)
    return db_pred

@router.post("/predict/image")
async def predict_image(
    driver_id: int, vehicle_id: int, trip_id: Optional[int] = None,
    file: UploadFile = File(...), db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Processes a single driver camera frame image and returns CV annotations + ML risk."""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file format")
        
    telemetry = {"speed": 65.0} # Default/simulated speed context
    result = safety_pipeline.process_driving_frame(
        db, frame=frame, telemetry=telemetry, trip_id=trip_id,
        driver_id=driver_id, vehicle_id=vehicle_id
    )
    return result

@router.post("/predict/video")
async def predict_video(
    driver_id: int, vehicle_id: int, trip_id: Optional[int] = None,
    file: UploadFile = File(...), db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Processes a video file sample (simulated aggregate output over duration)."""
    # Verify file is readable
    contents = await file.read(1024)
    if not contents:
        raise HTTPException(status_code=400, detail="Empty video file")
        
    # Mock video sequence summary response
    return {
        "filename": file.filename,
        "processed_frames": 120,
        "duration_seconds": 4.0,
        "metrics_summary": {
            "average_drowsiness": 0.12,
            "phone_detected_fraction": 0.0,
            "seatbelt_present": True,
            "distraction_score": 0.18,
            "lane_offset": 0.05
        },
        "alerts_generated": []
    }
