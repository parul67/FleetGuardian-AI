import os
import pytest
from utils.config_loader import ConfigLoader

def test_config_singleton():
    """Verify that ConfigLoader behaves as a singleton."""
    config1 = ConfigLoader()
    config2 = ConfigLoader()
    assert config1 is config2

def test_config_retrieval():
    """Verify that config parameters can be fetched correctly via dot access."""
    config = ConfigLoader()
    
    # Assert fields are correctly loaded or resolved default values
    assert config.get("camera.width") is not None
    assert isinstance(config.get("camera.fps"), int)
    
    # Assert nested thresholds are floats
    assert isinstance(config.get("thresholds.yolo_conf"), float)
    assert 0.0 <= config.get("thresholds.yolo_conf") <= 1.0
    
    # Test missing configurations return defaults
    assert config.get("non_existent_key.xyz", "default_val") == "default_val"
    assert config.get("logging.console_output") in [True, False]
