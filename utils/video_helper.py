import cv2
import os
from typing import Dict, Any, Optional
from utils.logger import logger

class VideoHelper:
    @staticmethod
    def get_metadata(path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves video properties: width, height, FPS, frame_count, duration, codec.
        """
        if not os.path.exists(path):
            logger.error(f"Video file not found at {path}")
            return None

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            logger.error(f"Could not open video file {path}")
            return None

        try:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            duration = frame_count / fps if fps > 0 else 0.0
            
            # Retrieve codec
            fourcc_val = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc_val >> 8 * i) & 0xFF) for i in range(4)])

            metadata = {
                "width": width,
                "height": height,
                "fps": fps,
                "frame_count": frame_count,
                "duration_seconds": duration,
                "codec": codec
            }
            return metadata
        except Exception as e:
            logger.error(f"Error reading video metadata for {path}: {e}")
            return None
        finally:
            cap.release()
            
    @staticmethod
    def get_fourcc(codec_name: str) -> int:
        """Converts codec name (e.g. 'mp4v', 'XVID') to standard OpenCV fourcc integer."""
        if len(codec_name) != 4:
            logger.warning(f"Codec name must be 4 characters, got '{codec_name}'. Defaulting to 'mp4v'")
            codec_name = "mp4v"
        return cv2.VideoWriter_fourcc(*codec_name)
