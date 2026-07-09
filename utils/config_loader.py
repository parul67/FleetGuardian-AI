import os
import yaml
from typing import Any, Dict

class ConfigLoader:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls, config_path: str = "configs/config.yaml"):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance

    def _load_config(self, config_path: str):
        # If absolute path is not given, resolve it relative to the project root
        if not os.path.isabs(config_path):
            # utils/logger_setup.py is 1 levels deep from root, so we get parent
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(root_dir, config_path)

        if not os.path.exists(config_path):
            # Fallback to current working directory resolution
            config_path = os.path.abspath(config_path)
            if not os.path.exists(config_path):
                # Hardcoded fallback config if file is completely missing
                self._config = {
                    "models": {"yolo_model_path": "yolo11n.pt", "face_landmarker_path": "face_landmarker.task"},
                    "camera": {"source": 0, "width": 640, "height": 480, "fps": 30, "auto_reconnect": True, "reconnect_delay": 5.0, "buffer_size": 5},
                    "preprocessing": {"target_width": 640, "target_height": 640, "normalize": True, "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]},
                    "thresholds": {"yolo_conf": 0.45, "yolo_iou": 0.45, "face_conf": 0.5, "face_presence_conf": 0.5, "blink_ear_threshold": 0.18, "blink_duration_max": 0.4, "blink_duration_min": 0.05, "yawn_mar_threshold": 0.25, "distraction_threshold": 0.25, "drowsiness_time_threshold": 2.0},
                    "video": {"output_format": "mp4v", "output_fps": 30.0, "output_width": 640, "output_height": 480},
                    "logging": {"level": "INFO", "console_output": True, "file_output": True, "log_file_path": "logs/fleetguardian.log", "max_bytes": 10485760, "backup_count": 5}
                }
                return

        with open(config_path, "r") as f:
            self._config = yaml.safe_load(f) or {}

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Retrieves a nested configuration value using a dot-separated string path.
        Example: config.get("camera.width", 640)
        """
        keys = key_path.split(".")
        val = self._config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    @property
    def raw_config(self) -> Dict[str, Any]:
        """Returns the raw configuration dictionary."""
        return self._config
