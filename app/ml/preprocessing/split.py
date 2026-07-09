import pandas as pd
from sklearn.model_selection import train_test_split
from ..utils.logger import get_logger
from ..utils.exceptions import DataProcessingError

logger = get_logger(__name__)

class DataSplitter:
    """Split data into train, validation, and test sets.

    The split ratios are provided via the configuration (default 0.2 test, 0.2 val).
    """

    def __init__(self, test_size: float = 0.2, val_size: float = 0.2, random_state: int = 42):
        if not 0 < test_size < 1:
            raise ValueError("test_size must be between 0 and 1")
        if not 0 <= val_size < 1:
            raise ValueError("val_size must be between 0 and 1")
        self.test_size = test_size
        self.val_size = val_size
        self.random_state = random_state
        logger.info(
            "DataSplitter initialized (test=%.2f, val=%.2f, seed=%d)",
            self.test_size,
            self.val_size,
            self.random_state,
        )

    def split(self, X: pd.DataFrame, y: pd.Series):
        """Perform train/validation/test split.

        Returns ``X_train, X_val, X_test, y_train, y_val, y_test``.
        """
        try:
            X_temp, X_test, y_temp, y_test = train_test_split(
                X,
                y,
                test_size=self.test_size,
                random_state=self.random_state,
                stratify=y,
            )
            # Adjust validation size relative to the remaining data
            val_rel = self.val_size / (1 - self.test_size)
            X_train, X_val, y_train, y_val = train_test_split(
                X_temp,
                y_temp,
                test_size=val_rel,
                random_state=self.random_state,
                stratify=y_temp,
            )
            logger.debug(
                "Data split: train=%d, val=%d, test=%d", len(y_train), len(y_val), len(y_test)
            )
            return X_train, X_val, X_test, y_train, y_val, y_test
        except Exception as exc:
            logger.exception("Failed to split data")
            raise DataProcessingError("Data splitting failed") from exc
