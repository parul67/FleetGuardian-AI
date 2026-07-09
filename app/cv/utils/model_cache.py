import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Global cache for loaded model instances
_model_cache: Dict[Any, Any] = {}

def get_yolo_model(model_path: str) -> Any:
    """Retrieve or load a YOLO model from the cache."""
    if model_path not in _model_cache:
        logger.info(f"Loading YOLO model from {model_path} (cache miss)...")
        from ultralytics import YOLO
        _model_cache[model_path] = YOLO(model_path)
    return _model_cache[model_path]

def get_face_mesh(
    static_image_mode: bool = False,
    max_num_faces: int = 1,
    refine_landmarks: bool = True,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5
) -> Any:
    """Retrieve or load a MediaPipe FaceMesh model from the cache."""
    cache_key = (
        "face_mesh",
        static_image_mode,
        max_num_faces,
        refine_landmarks,
        min_detection_confidence,
        min_tracking_confidence
    )
    if cache_key not in _model_cache:
        logger.info("Loading MediaPipe FaceMesh model (cache miss)...")
        import mediapipe as mp
        _model_cache[cache_key] = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=static_image_mode,
            max_num_faces=max_num_faces,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
    return _model_cache[cache_key]
