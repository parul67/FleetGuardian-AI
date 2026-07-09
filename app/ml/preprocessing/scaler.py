import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from ..utils.logger import get_logger
from ..utils.exceptions import DataProcessingError

logger = get_logger(__name__)

class FeatureScaler:
    """Scale numeric features.

    Supports 'standard' (StandardScaler) and 'minmax' (MinMaxScaler) based on configuration.
    """

    def __init__(self, method: str = "standard"):
        if method == "standard":
            self.scaler = StandardScaler()
        elif method == "minmax":
            self.scaler = MinMaxScaler()
        else:
            raise ValueError(f"Unsupported scaling method: {method}")
        self.method = method
        logger.info("FeatureScaler initialized with method %s", self.method)

    def fit(self, X: pd.DataFrame) -> None:
        try:
            self.scaler.fit(X)
            logger.debug("Fitted %s scaler on %d columns", self.method, X.shape[1])
        except Exception as exc:
            logger.exception("Failed to fit FeatureScaler")
            raise DataProcessingError("Scaler fitting failed") from exc

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        try:
            arr = self.scaler.transform(X)
            return pd.DataFrame(arr, columns=X.columns, index=X.index)
        except Exception as exc:
            logger.exception("Failed to transform with FeatureScaler")
            raise DataProcessingError("Scaler transform failed") from exc

    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self.fit(X)
        return self.transform(X)
