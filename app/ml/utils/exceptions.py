class MLException(Exception):
    """Base exception for all ML‑module errors."""

class ConfigLoadError(MLException):
    """Raised when the configuration file cannot be read or is invalid."""

class DataProcessingError(MLException):
    """Raised during preprocessing steps (missing values, outliers, etc.)."""

class ModelTrainingError(MLException):
    """Raised when model fitting fails or hyper‑parameters are incorrect."""

class InferenceError(MLException):
    """Raised during prediction (e.g., mismatched feature set)."""
