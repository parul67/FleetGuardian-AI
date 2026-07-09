class DMSException(Exception):
    """Base exception for the Driver Monitoring System."""

class ModelLoadError(DMSException):
    """Raised when a model file cannot be loaded."""

class FrameReadError(DMSException):
    """Raised when a video/frame cannot be read."""

class DetectionError(DMSException):
    """Raised when detection fails unexpectedly."""
