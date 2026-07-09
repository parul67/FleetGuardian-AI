import cv2
import base64
import numpy as np
import os
from typing import Optional
from utils.logger import logger

class ImageHelper:
    @staticmethod
    def load_image(path: str) -> Optional[np.ndarray]:
        """Loads an image from path using OpenCV. Returns None if it fails."""
        if not os.path.exists(path):
            logger.error(f"Image load failed: Path does not exist at {path}")
            return None
        try:
            image = cv2.imread(path)
            if image is None:
                logger.error(f"Image load failed: OpenCV could not decode image at {path}")
            return image
        except Exception as e:
            logger.error(f"Error loading image {path}: {e}")
            return None

    @staticmethod
    def save_image(image: np.ndarray, path: str) -> bool:
        """Saves an image to path using OpenCV. Creates directory if needed."""
        try:
            parent_dir = os.path.dirname(path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            success = cv2.imwrite(path, image)
            if not success:
                logger.error(f"Image save failed: cv2.imwrite returned False for {path}")
            return success
        except Exception as e:
            logger.error(f"Error saving image to {path}: {e}")
            return False

    @staticmethod
    def to_base64(image: np.ndarray, ext: str = ".jpg") -> str:
        """Converts an OpenCV image (np.ndarray) into a Base64-encoded UTF-8 string."""
        try:
            success, buffer = cv2.imencode(ext, image)
            if not success:
                raise ValueError("Failed to encode image to buffer")
            return base64.b64encode(buffer).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to encode image to base64: {e}")
            return ""

    @staticmethod
    def from_base64(base64_str: str) -> Optional[np.ndarray]:
        """Converts a Base64-encoded string back into an OpenCV image (np.ndarray)."""
        try:
            if "," in base64_str:
                # Strip prefix if present (e.g. 'data:image/jpeg;base64,...')
                base64_str = base64_str.split(",")[1]
            img_bytes = base64.b64decode(base64_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            logger.error(f"Failed to decode base64 string to image: {e}")
            return None
