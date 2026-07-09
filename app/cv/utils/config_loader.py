import yaml
from pathlib import Path

def load_config(config_path: str = "C:/Resume-Project/FleetGuardian-AI/app/cv/config.yaml") -> dict:
    """Load YAML configuration for the DMS.

    Args:
        config_path: Absolute path to the config file.
    Returns:
        Dictionary with configuration values.
    """
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with path.open('r') as f:
        return yaml.safe_load(f)
