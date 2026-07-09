import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from ..utils.logger import get_logger
from ..utils.exceptions import DataProcessingError

logger = get_logger(__name__)

class OutlierHandler:
    """Detect and remove outliers using IsolationForest.

    The model is fitted on the training data and then used to mask outlier rows.
    """

    def __init__(self, contamination: float = 0.01, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.iforest = IsolationForest(
            contamination=self.contamination, random_state=self.random_state
        )
        logger.info(
            "OutlierHandler initialized (contamination=%.3f)", self.contamination
        )

    def fit(self, X: pd.DataFrame) -> None:
        try:
            self.iforest.fit(X)
            logger.debug("Fitted IsolationForest on %d rows, %d columns", X.shape[0], X.shape[1])
        except Exception as exc:
            logger.exception("Failed to fit OutlierHandler")
            raise DataProcessingError("Outlier detection fitting failed") from exc

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return a DataFrame with outlier rows removed.

        Rows flagged as outliers (prediction = -1) are dropped.
        """
        try:
            preds = self.iforest.predict(X)
            mask = preds == 1  # 1 = inlier, -1 = outlier
            kept = X[mask]
            logger.info("Outlier removal: %d out of %d rows removed", (~mask).sum(), X.shape[0])
            return kept
        except Exception as exc:
            logger.exception("Failed to transform with OutlierHandler")
            raise DataProcessingError("Outlier detection transform failed") from exc

    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self.fit(X)
        return self.transform(X)
