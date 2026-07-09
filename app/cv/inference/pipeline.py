import cv2
import logging
from typing import Any, Dict

from ..feature_extraction.extractor import FeatureExtractor
from ..visualization.drawer import draw_features
from ..utils.logger import get_logger

logger = get_logger(__name__)

class InferencePipeline:
    """High‑level pipeline that runs all CV detectors on each frame.

    Usage example::

        pipeline = InferencePipeline(visualize=True)
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            features, annotated = pipeline.process_frame(frame)
            # ``annotated`` is the frame with drawings if ``visualize=True``
            cv2.imshow("DMS", annotated)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
    """

    def __init__(self, visualize: bool = False):
        self.visualize = visualize
        self.extractor = FeatureExtractor()
        logger.info(
            "InferencePipeline created – visualization %s", "enabled" if visualize else "disabled"
        )

    def process_frame(self, frame: Any) -> tuple[Dict[str, Any], Any]:
        """Run the full feature extraction on *frame*.

        Returns a tuple ``(features, output_frame)`` where ``features`` is the
        dictionary produced by :class:`FeatureExtractor` and ``output_frame`` is
        either the original frame (if ``visualize=False``) or a copy with drawings
        overlaid (if ``visualize=True``).
        """
        if frame is None:
            logger.warning("Received empty frame for inference.")
            return {}, None
        features = self.extractor.extract(frame)
        if self.visualize:
            annotated = draw_features(frame.copy(), features)
            return features, annotated
        else:
            return features, frame

    def run_video(self, source: int | str = 0) -> None:
        """Open a video source (camera index or file path) and process it live.

        The method blocks until the video ends or the user presses ``q``.
        """
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            logger.error("Failed to open video source %s", source)
            return
        logger.info("Starting video loop on source %s", source)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            _, out_frame = self.process_frame(frame)
            cv2.imshow("DMS Inference", out_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        logger.info("Video loop terminated.")
