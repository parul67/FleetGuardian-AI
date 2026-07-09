import cv2
import numpy as np
import mediapipe as mp
import logging
from typing import Dict, Tuple
from ..utils.logger import get_logger

# MediaPipe Face Mesh landmark indices for eyes and mouth (based on MP documentation)
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
MOUTH_IDX = [78, 81, 13, 311, 308, 14]


def _aspect_ratio(landmarks: np.ndarray, indices: list) -> float:
    """Calculate the aspect ratio for a set of landmarks.

    Args:
        landmarks: (N, 2) array of (x, y) normalized coordinates.
        indices: list of landmark indices defining the polygon.
    Returns:
        Aspect ratio (float).
    """
    pts = landmarks[indices]
    # Euclidean distances between vertical eye/mouth points
    a = np.linalg.norm(pts[1] - pts[5])
    b = np.linalg.norm(pts[2] - pts[4])
    c = np.linalg.norm(pts[0] - pts[3])
    if c == 0:
        return 0.0
    return (a + b) / (2.0 * c)


class DrowsinessDetector:
    """Detect drowsiness metrics using EAR, MAR, blink count, and yawning.

    The class maintains state across frames to compute blink count, eye‑closure
    duration, and yawning frequency.
    """

    def __init__(self,
                 ear_thresh: float = 0.25,
                 mar_thresh: float = 0.6,
                 consecutive_frames: int = 3,
                 logger: logging.Logger | None = None) -> None:
        self.ear_thresh = ear_thresh
        self.mar_thresh = mar_thresh
        self.consecutive_frames = consecutive_frames
        self.logger = logger or get_logger(__name__)
        self.face_mesh_params = {
            "static_image_mode": False,
            "max_num_faces": 1,
            "refine_landmarks": True,
            "min_detection_confidence": 0.5,
            "min_tracking_confidence": 0.5,
        }
        self._face_mesh = None
        # State variables
        self._closed_eyes_frames = 0
        self._total_blinks = 0
        self._yawn_counter = 0
        self._total_yawns = 0
        self._eye_closed_seconds = 0.0
        self._frame_time = 1 / 30  # default assuming 30 FPS; can be updated per source

    @property
    def face_mesh(self):
        if self._face_mesh is None:
            from ..utils.model_cache import get_face_mesh
            self._face_mesh = get_face_mesh(**self.face_mesh_params)
        return self._face_mesh

    def _process_landmarks(self, landmarks) -> Tuple[float, float]:
        """Compute EAR and MAR from normalized landmarks.
        Returns (ear, mar).
        """
        pts = np.array([(lm.x, lm.y) for lm in landmarks])
        ear_left = _aspect_ratio(pts, LEFT_EYE_IDX)
        ear_right = _aspect_ratio(pts, RIGHT_EYE_IDX)
        ear = (ear_left + ear_right) / 2.0
        mar = _aspect_ratio(pts, MOUTH_IDX)
        return ear, mar

    def _update_state(self, ear: float, mar: float) -> None:
        # Blink detection
        if ear < self.ear_thresh:
            self._closed_eyes_frames += 1
        else:
            if self._closed_eyes_frames >= self.consecutive_frames:
                self._total_blinks += 1
                self.logger.debug("Blink detected. Total=%d", self._total_blinks)
            self._closed_eyes_frames = 0
        # Yawning detection
        if mar > self.mar_thresh:
            self._yawn_counter += 1
        else:
            if self._yawn_counter >= self.consecutive_frames:
                self._total_yawns += 1
                self.logger.debug("Yawn detected. Total=%d", self._total_yawns)
            self._yawn_counter = 0
        # Eye‑closure duration accumulation
        if ear < self.ear_thresh:
            self._eye_closed_seconds += self._frame_time
        else:
            self._eye_closed_seconds = 0.0

    def process(self, frame: np.ndarray) -> Dict[str, float]:
        """Process a single video frame and return drowsiness metrics.

        Args:
            frame: BGR image as NumPy array.
        Returns:
            Dictionary with keys: ear, mar, blink_rate, eye_closed_seconds,
            yawning_count, fatigue_score.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            self.logger.debug("No face detected in frame.")
            return {}
        landmarks = results.multi_face_landmarks[0].landmark
        ear, mar = self._process_landmarks(landmarks)
        self._update_state(ear, mar)
        # Simple fatigue score (higher indicates more fatigue)
        fatigue_score = (
            (1 - ear / self.ear_thresh) * 0.4
            + (mar / self.mar_thresh) * 0.3
            + (self._eye_closed_seconds / 5.0) * 0.2
            + (self._total_yawns / 5.0) * 0.1
        )
        # Approximate blink rate per minute
        blink_rate = self._total_blinks * (60 * self._frame_time)
        return {
            "ear": ear,
            "mar": mar,
            "blink_rate": blink_rate,
            "eye_closed_seconds": self._eye_closed_seconds,
            "yawning_count": self._total_yawns,
            "fatigue_score": fatigue_score,
        }
