import logging
import os
from logging.handlers import RotatingFileHandler

def get_logger(name: str = "dms") -> logging.Logger:
    """Create (or retrieve) a configured logger.

    The logger writes to both the console and a rotating file located at
    ``logs/dms.log`` relative to the project root. The file handler rotates
    after 5 MB and keeps up to 3 backups.

    Args:
        name: Logger name. Using the same name returns the same instance.

    Returns:
        A :class:`logging.Logger` instance ready for use.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    fh = RotatingFileHandler(
        os.path.join(log_dir, "dms.log"), maxBytes=5 * 1024 * 1024, backupCount=3
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger
