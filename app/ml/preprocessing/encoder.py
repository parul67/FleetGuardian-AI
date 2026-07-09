import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from ..utils.logger import get_logger
from ..utils.exceptions import DataProcessingError

logger = get_logger(__name__)

class CategoricalEncoder:
    """Encode categorical features using OneHotEncoder.

    The encoder is fitted on the training data and can transform both
    training and inference dataframes.
    """

    def __init__(self, handle_unknown: str = "ignore"):
        self.handle_unknown = handle_unknown
        self.encoder: ColumnTransformer | None = None
        logger.info("CategoricalEncoder initialized (handle_unknown=%s)", self.handle_unknown)

    def fit(self, X: pd.DataFrame) -> None:
        try:
            cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
            if not cat_cols:
                logger.warning("No categorical columns found for encoding.")
                self.encoder = None
                return
            self.encoder = ColumnTransformer(
                [
                    (
                        "cat",
                        OneHotEncoder(handle_unknown=self.handle_unknown, sparse_output=False),
                        cat_cols,
                    )
                ],
                remainder="passthrough",
            )
            self.encoder.fit(X)
            logger.debug("Fitted OneHotEncoder on columns: %s", cat_cols)
        except Exception as exc:
            logger.exception("Failed to fit CategoricalEncoder")
            raise DataProcessingError("Encoder fitting failed") from exc

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if self.encoder is None:
            logger.info("Encoder not fitted or no categorical columns; returning original DataFrame.")
            return X.copy()
        try:
            transformed = self.encoder.transform(X)
            # Retrieve feature names
            ohe = self.encoder.named_transformers_["cat"]
            ohe_features = ohe.get_feature_names_out()
            numeric_features = [c for c in X.columns if c not in self.encoder.transformers_[0][2]]
            columns = list(ohe_features) + numeric_features
            return pd.DataFrame(transformed, columns=columns, index=X.index)
        except Exception as exc:
            logger.exception("Failed to transform with CategoricalEncoder")
            raise DataProcessingError("Encoder transform failed") from exc

    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        self.fit(X)
        return self.transform(X)
