import cv2
import numpy as np
import mediapipe as mp
import logging
from typing import Dict, Tuple
from ..utils.logger import get_logger

# 3D model points of facial landmarks (in mm) for a generic head model
MODEL_POINTS = np.array([
    (0.0, 0.0, 0.0),           # Nose tip
    (0.0, -330.0, -65.0),      # Chin
    (-225.0, 170.0, -135.0),   # Left eye left corner
    (225.0, 170.0, -135.0),    # Right eye right corner
    (-150.0, -150.0, -125.0),  # Left mouth corner
    (150.0, -150.0, -125.0)    # Right mouth corner
], dtype="double")

# Corresponding MediaPipe landmark indices for the above points
LANDMARK_IDS = {
    "nose_tip": 1,
    "chin": 152,
    "left_eye_left_corner": 33,
    "right_eye_right_corner": 263,
    "left_mouth_corner": 61,
    "right_mouth_corner": 291,
}


class DistractionEstimator:
    """Estimate driver distraction via head pose using MediaPipe Face Mesh.

    Provides pitch, yaw, roll, direction label and attention score.
    """

    def __init__(self,
                 angle_thresh: float = 15.0,
                 consecutive_frames: int = 3,
                 logger: logging.Logger | None = None) -> None:
        self.angle_thresh = angle_thresh
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
        self._off_center_frames = 0
        self._look_away_seconds = 0.0
        self._frame_time = 1 / 30
        self._image_shape = None

    @property
    def face_mesh(self):
        if self._face_mesh is None:
            from ..utils.model_cache import get_face_mesh
            self._face_mesh = get_face_mesh(**self.face_mesh_params)
        return self._face_mesh

    def _get_image_points(self, landmarks) -> np.ndarray:
        img_h, img_w = self._image_shape
        points = []
        for name in ["nose_tip", "chin", "left_eye_left_corner", "right_eye_right_corner",
                     "left_mouth_corner", "right_mouth_corner"]:
            idx = LANDMARK_IDS[name]
            lm = landmarks[idx]
            points.append([int(lm.x * img_w), int(lm.y * img_h)])
        return np.array(points, dtype="double")

    def _estimate_pose(self, image_points: np.ndarray) -> Tuple[float, float, float]:
        focal = self._image_shape[1]
        center = (self._image_shape[1] / 2, self._image_shape[0] / 2)
        camera_matrix = np.array([
            [focal, 0, center[0]],
            [0, focal, center[1]],
            [0, 0, 1]
        ], dtype="double")
        dist_coeffs = np.zeros((4, 1))
        success, rotation_vec, _ = cv2.solvePnP(
            MODEL_POINTS, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
        )
        if not success:
            raise RuntimeError("solvePnP failed")
        rot_mat, _ = cv2.Rodrigues(rotation_vec)
        sy = np.sqrt(rot_mat[0, 0] ** 2 + rot_mat[1, 0] ** 2)
        singular = sy < 1e-6
        if not singular:
            x = np.arctan2(rot_mat[2, 1], rot_mat[2, 2])
            y = np.arctan2(-rot_mat[2, 0], sy)
            z = np.arctan2(rot_mat[1, 0], rot_mat[0, 0])
        else:
            x = np.arctan2(-rot_mat[1, 2], rot_mat[1, 1])
            y = np.arctan2(-rot_mat[2, 0], sy)
            z = 0
        return np.degrees(x), np.degrees(y), np.degrees(z)

    def _categorize(self, yaw: float, pitch: float) -> str:
        if abs(yaw) < self.angle_thresh and abs(pitch) < self.angle_thresh:
            return "forward"
        if yaw > self.angle_thresh:
            return "right"
        if yaw < -self.angle_thresh:
            return "left"
        if pitch > self.angle_thresh:
            return "down"
        if pitch < -self.angle_thresh:
            return "up"
        return "forward"

    def process(self, frame: np.ndarray) -> Dict[str, any]:
        self._image_shape = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            self.logger.debug("No face detected for distraction estimation.")
            return {}
        landmarks = results.multi_face_landmarks[0].landmark
        img_pts = self._get_image_points(landmarks)
        pitch, yaw, roll = self._estimate_pose(img_pts)
        direction = self._categorize(yaw, pitch)
        if direction != "forward":
            self._off_center_frames += 1
            self._look_away_seconds += self._frame_time
        else:
            self._off_center_frames = 0
            self._look_away_seconds = 0.0
        attention = max(0.0, 1.0 - self._look_away_seconds / 10.0)
        return {
            "pitch": pitch,
            "yaw": yaw,
            "roll": roll,
            "direction": direction,
            "looking_away_seconds": self._look_away_seconds,
            "attention_score": attention,
        }
