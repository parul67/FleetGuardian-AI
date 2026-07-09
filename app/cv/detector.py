from app.cv.inference.pipeline import InferencePipeline

class DriverCVDetector:
    def __init__(self):
        self.pipeline = InferencePipeline(visualize=True)
        
    def process_frame(self, frame):
        cv_metrics, annotated_frame = self.pipeline.process_frame(frame)
        # Ensure we have required keys for the pipeline
        if not cv_metrics:
            cv_metrics = {
                "speed": 60.0,
                "drowsiness_score": 0.0,
                "phone_detected": False,
                "seatbelt_present": True,
                "lane_offset": 0.0,
                "distraction_score": 0.0
            }
        return annotated_frame, cv_metrics

driver_cv_detector = DriverCVDetector()
