import pandas as pd
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from ..utils.logger import get_logger
from ..utils.exceptions import DataProcessingError

logger = get_logger(__name__)

class FeatureSelector:
    """Select top‑k features using mutual information.

    The number of features ``k`` is read from the configuration.
    """

    def __init__(self, k: int = 15):
        if k <= 0:
            raise ValueError("k must be a positive integer")
        self.k = k
        self.selector = SelectKBest(score_func=mutual_info_classif, k=self.k)
        logger.info("FeatureSelector initialized to select %d features", self.k)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        try:
            self.selector.fit(X, y)
            logger.debug("FeatureSelector fitted; scores: %s", self.selector.scores_)
        except Exception as exc:
            logger.exception("Failed to fit FeatureSelector")
            raise DataProcessingError("Feature selection fitting failed") from exc

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        try:
            cols = self.selector.get_feature_names_out()
            transformed = self.selector.transform(X)
            return pd.DataFrame(transformed, columns=cols, index=X.index)
        except Exception as exc:
            logger.exception("Failed to transform with FeatureSelector")
            raise DataProcessingError("Feature selection transform failed") from exc

    def fit_transform(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        self.fit(X, y)
        return self.transform(X)
