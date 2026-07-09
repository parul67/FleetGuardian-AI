import logging
from typing import List, Dict, Any
from app.core.config import settings
from ..utils.logger import get_logger
from ..utils.model_cache import get_yolo_model

logger = get_logger(__name__)

class PhoneDetector:
    """Detect mobile phones in an image using a YOLO model.

    The model path and confidence threshold are read from the global settings.
    """

    def __init__(self, model_path: str = None, conf_thresh: float = None):
        self.model_path = model_path or settings.PHONE_MODEL_PATH
        self.conf_thresh = conf_thresh or 0.45
        self._model = None
        logger.info("PhoneDetector initialized (model will be loaded lazily on demand).")

    @property
    def model(self):
        if self._model is None:
            self._model = get_yolo_model(self.model_path)
        return self._model

    def detect(self, frame: Any) -> List[Dict[str, Any]]:
        """Run detection on a single frame.

        Returns a list of dicts with keys: ``bbox`` (x1, y1, x2, y2), ``confidence``, ``class_id``.
        """
        if frame is None:
            logger.warning("Received empty frame for phone detection.")
            return []
        results = self.model(frame)
        detections = []
        for r in results:
            for box in r.boxes:
                conf = float(box.conf)
                if conf < self.conf_thresh:
                    continue
                cls = int(box.cls)
                # Assuming COCO class 67 corresponds to "cell phone"
                if cls != 67:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "confidence": conf,
                    "class_id": cls,
                })
        logger.debug("Phone detection yielded %d boxes.", len(detections))
        return detections
