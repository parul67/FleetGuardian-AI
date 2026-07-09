import yaml
import os
from typing import Dict, Any
from .logger import get_logger

logger = get_logger(__name__)

def load_config(config_path: str = "C:/Resume-Project/FleetGuardian-AI/app/ml/config.yaml") -> Dict[str, Any]:
    """Load a YAML configuration file for the ML module.

    Args:
        config_path: Absolute path to the config file.
    Returns:
        Dictionary with configuration values.
    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the YAML cannot be parsed.
    """
    if not os.path.isfile(config_path):
        logger.error("ML config file not found: %s", config_path)
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        try:
            cfg = yaml.safe_load(f) or {}
            logger.info("Loaded ML config from %s", config_path)
            return cfg
        except yaml.YAMLError as exc:
            logger.exception("Failed to parse ML config YAML")
            raise
