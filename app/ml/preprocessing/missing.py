import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from ..utils.logger import get_logger
from ..utils.exceptions import DataProcessingError

logger = get_logger(__name__)

class MissingValueHandler:
    """Handle missing values using a SimpleImputer.

    The strategy (mean, median, most_frequent) is read from the configuration.
    """

    def __init__(self, strategy: str = "median"):
        if strategy not in {"mean", "median", "most_frequent"}:
            raise ValueError(f"Unsupported imputation strategy: {strategy}")
        self.strategy = strategy
        self.imputer = SimpleImputer(strategy=self.strategy)
        logger.info("MissingValueHandler initialized with strategy %s", self.strategy)

    def fit(self, X: pd.DataFrame) -> None:
        try:
            self.imputer.fit(X)
            logger.debug("Fitted imputer on %d columns", X.shape[1])
        except Exception as exc:
            logger.exception("Failed to fit MissingValueHandler")
            raise DataProcessingError("Imputer fitting failed") from exc

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        try:
            arr = self.imputer.transform(X)
            return pd.DataFrame(arr, columns=X.columns, index=X.index)
        except Exception as exc:
            logger.exception("Failed to transform with MissingValueHandler")
            raise DataProcessingError("Imputer transform failed") from exc

    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self.fit(X)
        return self.transform(X)
