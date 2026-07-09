import logging
from typing import Dict, Any, List
import cv2
import numpy as np

from ..phone_detection.detector import PhoneDetector
from ..seatbelt_detection.detector import SeatbeltDetector
from ..lane_detection.detector import LaneDetector
from ..drowsiness.detector import DrowsinessDetector
from ..distraction.estimator import DistractionEstimator
from ..utils.logger import get_logger

logger = get_logger(__name__)

class FeatureExtractor:
    """Aggregate detections from all CV modules into a single feature dictionary.

    The extractor lazily creates each detector on first use to avoid unnecessary model
    loading if a particular component is not needed.
    """

    def __init__(self):
        self._phone_detector: PhoneDetector | None = None
        self._seatbelt_detector: SeatbeltDetector | None = None
        self._lane_detector: LaneDetector | None = None
        self._drowsiness_detector: DrowsinessDetector | None = None
        self._distraction_estimator: DistractionEstimator | None = None
        logger.info("FeatureExtractor instantiated – detectors will be loaded on demand.")

    # ---------------------------------------------------------------------
    # Lazy initialisers
    # ---------------------------------------------------------------------
    @property
    def phone_detector(self) -> PhoneDetector:
        if self._phone_detector is None:
            self._phone_detector = PhoneDetector()
        return self._phone_detector

    @property
    def seatbelt_detector(self) -> SeatbeltDetector:
        if self._seatbelt_detector is None:
            self._seatbelt_detector = SeatbeltDetector()
        return self._seatbelt_detector

    @property
    def lane_detector(self) -> LaneDetector:
        if self._lane_detector is None:
            self._lane_detector = LaneDetector()
        return self._lane_detector

    @property
    def drowsiness_detector(self) -> DrowsinessDetector:
        if self._drowsiness_detector is None:
            self._drowsiness_detector = DrowsinessDetector()
        return self._drowsiness_detector

    @property
    def distraction_estimator(self) -> DistractionEstimator:
        if self._distraction_estimator is None:
            self._distraction_estimator = DistractionEstimator()
        return self._distraction_estimator

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def extract(self, frame: Any) -> Dict[str, Any]:
        """Run all detectors on *frame* and return a consolidated dictionary.

        The returned structure looks like::

            {
                "phones": [...],
                "seatbelts": [...],
                "lanes": [...],
                "drowsiness": {...},
                "distraction": {...},
            }
        """
        if frame is None:
            logger.warning("Received empty frame for feature extraction.")
            return {}

        # Phone, seatbelt and lane detections are list‑based
        phones = self.phone_detector.detect(frame)
        seatbelts = self.seatbelt_detector.detect(frame)
        lanes = self.lane_detector.detect(frame)

        # Drowsiness returns a dict with ``blink``/``yawn`` counters
        drowsiness = self.drowsiness_detector.process(frame)

        # Distraction returns a dict with head‑pose status etc.
        distraction = self.distraction_estimator.process(frame)

        features: Dict[str, Any] = {
            "phones": phones,
            "seatbelts": seatbelts,
            "lanes": lanes,
            "drowsiness": drowsiness,
            "distraction": distraction,
        }
        logger.debug("Feature extraction yielded keys: %s", list(features.keys()))
        return features
