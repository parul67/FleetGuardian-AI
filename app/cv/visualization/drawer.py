import cv2
import logging
from typing import Any, Dict, List, Tuple

from ..utils.logger import get_logger

logger = get_logger(__name__)

def _draw_boxes(frame: Any, boxes: List[Dict[str, Any]], color: Tuple[int, int, int], label: str) -> None:
    """Draw bounding boxes on *frame*.

    ``boxes`` is a list of dictionaries with a ``bbox`` key containing ``(x1, y1, x2, y2)``.
    ``color`` is an BGR tuple. ``label`` is drawn above each box.
    """
    for det in boxes:
        x1, y1, x2, y2 = det.get("bbox", (0, 0, 0, 0))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        conf = det.get("confidence", 0)
        txt = f"{label}: {conf:.2f}" if conf is not None else label
        cv2.putText(
            frame,
            txt,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
            cv2.LINE_AA,
        )

def _draw_lanes(frame: Any, lanes: List[Tuple[int, int, int, int]], color: Tuple[int, int, int]) -> None:
    """Draw lane line segments on *frame*.

    Each lane is a ``(x1, y1, x2, y2)`` tuple.
    """
    for (x1, y1, x2, y2) in lanes:
        cv2.line(frame, (x1, y1), (x2, y2), color, 2)

def draw_features(frame: Any, features: Dict[str, Any]) -> Any:
    """Overlay detection results onto *frame* and return the annotated image.

    Supported keys in ``features``:
        - ``phones`` – list of detections (drawn in red)
        - ``seatbelts`` – list of detections (drawn in green)
        - ``lanes`` – list of line segments (drawn in blue)
        - ``drowsiness`` – dict with ``blink``/``yawn`` counters (shown as text)
        - ``distraction`` – dict with ``attention_score`` etc. (shown as text)
    """
    if frame is None:
        logger.warning("draw_features called with None frame")
        return None

    # Draw object detections
    if "phones" in features:
        _draw_boxes(frame, features["phones"], (0, 0, 255), "Phone")
    if "seatbelts" in features:
        _draw_boxes(frame, features["seatbelts"], (0, 255, 0), "Seatbelt")
    if "lanes" in features:
        _draw_lanes(frame, features["lanes"], (255, 0, 0))

    # Overlay status text for drowsiness & distraction
    y_offset = 20
    if "drowsiness" in features:
        d = features["drowsiness"]
        txt = f"Blink:{d.get('blink_count',0)} Yawn:{d.get('yawn_count',0)}"
        cv2.putText(frame, txt, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_offset += 20
    if "distraction" in features:
        disc = features["distraction"]
        txt = f"Attention:{disc.get('attention_score',0):.2f}"
        cv2.putText(frame, txt, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    return frame
