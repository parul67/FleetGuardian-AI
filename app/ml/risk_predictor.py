import os
import pandas as pd
from typing import Dict, Any, List
from app.core.config import settings

class AccidentRiskPredictor:
    def __init__(self):
        """Loads the trained ML classifier to estimate accident risk."""
        self.model_path = str(settings.ROOT_DIR / settings.ACCIDENT_MODEL_PATH)
        self._model = None
        self.classes = ["Low", "Medium", "High", "Critical"]
        self._loaded = False

    @property
    def model(self):
        if not self._loaded:
            if os.path.exists(self.model_path):
                try:
                    import joblib
                    self._model = joblib.load(self.model_path)
                    print("Accident Risk Predictor model loaded successfully.")
                except Exception as e:
                    print(f"Error loading ML model: {e}. Falling back to heuristic classifier.")
            self._loaded = True
        return self._model

    def predict_risk(self, inputs: Dict[str, Any]) -> str:
        """
        Predicts accident risk level based on telemetry and driver scores.
        Inputs: {drowsiness_score, phone_usage_frequency, seatbelt_present, lane_departure_count, speed, distraction_score}
        """
        # If model is loaded, construct features and run prediction
        if self.model:
            try:
                # Features in correct order matching trainer.py
                features = pd.DataFrame([{
                    "drowsiness_score": inputs.get("drowsiness_score", 0.0),
                    "phone_usage_frequency": inputs.get("phone_usage_frequency", 0.0),
                    "seatbelt_present": 1 if inputs.get("seatbelt_present", True) else 0,
                    "lane_departure_count": inputs.get("lane_departure_count", 0),
                    "speed": inputs.get("speed", 0.0),
                    "distraction_score": inputs.get("distraction_score", 0.0)
                }])
                pred_idx = int(self.model.predict(features)[0])
                return self.classes[pred_idx]
            except Exception as e:
                print(f"Model prediction error: {e}. Using fallback heuristic.")
                
        # Heuristic/Rule-based Fallback (SOLID and reliable out-of-the-box)
        drowsiness = inputs.get("drowsiness_score", 0.0)
        phone = inputs.get("phone_usage_frequency", 0.0)
        seatbelt = inputs.get("seatbelt_present", True)
        lanes = inputs.get("lane_departure_count", 0)
        speed = inputs.get("speed", 0.0)
        distraction = inputs.get("distraction_score", 0.0)
        
        # Heavy risk factors
        score = 0
        if drowsiness > 0.6 or phone > 0.5:
            score += 4
        elif drowsiness > 0.3 or phone > 0.1:
            score += 2
            
        if not seatbelt:
            score += 2
        if lanes > 3 or speed > 85:
            score += 3
        elif lanes > 1 or speed > 70:
            score += 1
        if distraction > 0.4:
            score += 2

        if score >= 6:
            return "Critical"
        elif score >= 4:
            return "High"
        elif score >= 2:
            return "Medium"
        return "Low"

accident_risk_predictor = AccidentRiskPredictor()
