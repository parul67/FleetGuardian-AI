import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import cv2
import numpy as np

from ..utils.logger import get_logger
from ..utils.config_loader import load_config

logger = get_logger(__name__)

class LaneDetector:
    """Simple lane detection using Canny edge detection and Hough transform.

    Configurable parameters are read from ``config.yaml`` under ``lane_detection``.
    Returns a list of lane line segments as ``(x1, y1, x2, y2)`` tuples.
    """

    def __init__(self, config_path: str = "C:/Resume-Project/FleetGuardian-AI/app/cv/config.yaml"):
        cfg = load_config(config_path)
        lane_cfg = cfg.get("lane_detection", {})
        self.canny_thresh1 = lane_cfg.get("canny_thresh1", 50)
        self.canny_thresh2 = lane_cfg.get("canny_thresh2", 150)
        self.hough_rho = lane_cfg.get("hough_rho", 1)
        self.hough_theta = lane_cfg.get("hough_theta", np.pi / 180)
        self.hough_threshold = lane_cfg.get("hough_threshold", 50)
        self.min_line_length = lane_cfg.get("min_line_length", 100)
        self.max_line_gap = lane_cfg.get("max_line_gap", 50)
        logger.info("LaneDetector initialized with Canny thresholds (%d, %d)", self.canny_thresh1, self.canny_thresh2)

    def detect(self, frame: Any) -> List[Tuple[int, int, int, int]]:
        if frame is None:
            logger.warning("Received empty frame for lane detection.")
            return []
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Apply Gaussian blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        # Canny edge detection
        edges = cv2.Canny(blur, self.canny_thresh1, self.canny_thresh2)
        # Hough line transform
        lines = cv2.HoughLinesP(
            edges,
            rho=self.hough_rho,
            theta=self.hough_theta,
            threshold=self.hough_threshold,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap,
        )
        lane_segments: List[Tuple[int, int, int, int]] = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                lane_segments.append((x1, y1, x2, y2))
        logger.debug("Lane detection found %d line segments.", len(lane_segments))
        return lane_segments
