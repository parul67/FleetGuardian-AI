import os
import logging
from logging.handlers import RotatingFileHandler
from utils.config_loader import ConfigLoader

def setup_logger(name: str = "FleetGuardian") -> logging.Logger:
    """
    Sets up a reusable Logger instance using settings from YAML configuration.
    Supports console outputs and rotating file outputs.
    """
    # Load configuration
    config = ConfigLoader()
    log_level_str = config.get("logging.level", "INFO").upper()
    level = getattr(logging, log_level_str, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handler configuration
    if logger.hasHandlers():
        return logger

    # Log Formatter: Timestamp, Level, Module Name, Line Number, Message
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Logging Handler
    if config.get("logging.console_output", True):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Rotating File Logging Handler
    if config.get("logging.file_output", True):
        log_file = config.get("logging.log_file_path", "logs/fleetguardian.log")
        
        # Resolve log file directory
        if not os.path.isabs(log_file):
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_file = os.path.normpath(os.path.join(root_dir, log_file))
            
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        max_bytes = config.get("logging.max_bytes", 10485760)
        backup_count = config.get("logging.backup_count", 5)

        try:
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Fallback to console-only warning if file creation fails
            print(f"Warning: Failed to initialize file logger at {log_file} due to: {e}")

    return logger

# Create and export project-wide default logger
logger = setup_logger()
