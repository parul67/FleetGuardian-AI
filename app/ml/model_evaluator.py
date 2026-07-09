"""
app/ml/model_evaluator.py
---------------------------
ModelEvaluator – loads a trained pipeline and produces a full evaluation
report: per-class precision/recall/F1, accuracy, confusion matrix, and
a Markdown summary written to docs/model_evaluation.md.
"""
from __future__ import annotations

import os
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

from utils.logger import logger
from .model_trainer import ModelTrainer


class ModelEvaluator:
    """
    Evaluates a trained model pipeline against a hold-out test set.

    Usage::

        evaluator = ModelEvaluator()
        report = evaluator.evaluate(df_test, pipeline=pipeline)
    """

    def __init__(
        self,
        config_path: str = "configs/model_training_config.yaml",
        class_names: Optional[List[str]] = None,
    ) -> None:
        self._trainer = ModelTrainer(config_path)
        self.target_col: str = self._trainer.target_col
        self.model_dir: str = self._trainer.model_dir
        self.report_path: str = self._trainer.cfg.get(
            "evaluation_report_path", "docs/model_evaluation.md"
        )
        self.class_names: List[str] = class_names or self._trainer.class_names

    # ── Public API ────────────────────────────────────────────────────────────

    def evaluate(
        self,
        df_test: pd.DataFrame,
        pipeline=None,
        model_path: Optional[str] = None,
        target_col: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run full evaluation against df_test.

        Args:
            df_test:     Pre-processed test DataFrame (features + target).
            pipeline:    Already-loaded sklearn Pipeline; if None, loads from disk.
            model_path:  Override path to joblib model file.
            target_col:  Override target column name.

        Returns:
            dict with keys: accuracy, classification_report, confusion_matrix, model_name.
        """
        target_col = target_col or self.target_col
        if target_col not in df_test.columns:
            raise ValueError(f"Target column '{target_col}' not in DataFrame.")

        # Load pipeline if not supplied
        if pipeline is None:
            pipeline = self._trainer.load_model(model_path)

        X_test = df_test.drop(columns=[target_col]).select_dtypes(include=[np.number])
        y_test = df_test[target_col]

        y_pred = pipeline.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        clf_report = classification_report(
            y_test, y_pred,
            labels=sorted(y_test.unique()),
            zero_division=0,
            output_dict=True,
        )
        clf_report_str = classification_report(
            y_test, y_pred,
            labels=sorted(y_test.unique()),
            zero_division=0,
        )
        cm = confusion_matrix(y_test, y_pred, labels=sorted(y_test.unique()))

        result: Dict[str, Any] = {
            "accuracy": acc,
            "classification_report": clf_report,
            "classification_report_str": clf_report_str,
            "confusion_matrix": cm.tolist(),
            "model_name": getattr(pipeline, "_model_name", "best_model"),
        }

        logger.info(f"Evaluation complete | Accuracy: {acc:.4f}")
        logger.info(f"\n{clf_report_str}")

        self._save_evaluation_report(result, cm, sorted(y_test.unique()))
        return result

    # ── Private helpers ───────────────────────────────────────────────────────

    def _save_evaluation_report(
        self,
        result: Dict[str, Any],
        cm: np.ndarray,
        labels: List,
    ) -> None:
        """Write a Markdown evaluation report to disk."""
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        report_path = os.path.join(root, self.report_path)
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        clf_dict = result["classification_report"]
        acc = result["accuracy"]

        lines = [
            "# FleetGuardian AI – Model Evaluation Report\n",
            f"**Overall Accuracy:** `{acc:.4f}`\n",
            "## Per-Class Metrics\n",
            "| Class | Precision | Recall | F1-Score | Support |",
            "| --- | --- | --- | --- | --- |",
        ]

        for label in labels:
            key = str(label)
            if key in clf_dict:
                m = clf_dict[key]
                lines.append(
                    f"| `{key}` "
                    f"| {m['precision']:.3f} "
                    f"| {m['recall']:.3f} "
                    f"| {m['f1-score']:.3f} "
                    f"| {int(m['support'])} |"
                )

        # Weighted avg row
        if "weighted avg" in clf_dict:
            w = clf_dict["weighted avg"]
            lines.append(
                f"| **weighted avg** "
                f"| {w['precision']:.3f} "
                f"| {w['recall']:.3f} "
                f"| {w['f1-score']:.3f} "
                f"| {int(w['support'])} |"
            )

        # Confusion matrix
        lines += [
            "",
            "## Confusion Matrix\n",
            "Rows = Actual class, Columns = Predicted class.\n",
        ]
        header = "| | " + " | ".join(f"`{l}`" for l in labels) + " |"
        sep = "| --- " * (len(labels) + 1) + "|"
        lines += [header, sep]
        for i, row in enumerate(cm):
            row_cells = " | ".join(str(v) for v in row)
            lines.append(f"| `{labels[i]}` | {row_cells} |")

        with open(report_path, "w") as f:
            f.write("\n".join(lines))
        logger.info(f"Evaluation report saved to: {report_path}")
