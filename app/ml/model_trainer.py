"""
app/ml/model_trainer.py
------------------------
ModelTrainer – trains multiple classifiers using sklearn Pipelines,
StratifiedKFold cross-validation, and GridSearchCV hyperparameter tuning.
Automatically selects and saves the best-performing model.
"""
from __future__ import annotations

import importlib
import os
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .utils.logger import logger


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_cfg(config_path: str) -> Dict[str, Any]:
    """Resolve and load the model_training_config.yaml section."""
    if not os.path.isabs(config_path):
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(root, config_path)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(config_path, "r") as f:
        raw = yaml.safe_load(f) or {}
    return raw.get("model_training", {})


def _import_class(dotted_path: str) -> type:
    """Dynamically import a class from a dotted module path."""
    module_path, class_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


# ─────────────────────────────────────────────────────────────────────────────
# ModelTrainer
# ─────────────────────────────────────────────────────────────────────────────

class ModelTrainer:
    """
    Trains all enabled classifiers via sklearn Pipelines + GridSearchCV,
    compares CV scores, and serialises the best model.

    Usage::

        trainer = ModelTrainer()
        results = trainer.train(df_train, target_col="risk_level")
        trainer.save_best_model()
    """

    def __init__(self, config_path: str = "configs/model_training_config.yaml") -> None:
        self.cfg = _load_cfg(config_path)
        self.model_dir: str = self.cfg.get("model_dir", "models")
        self.best_model_filename: str = self.cfg.get("best_model_filename", "best_model.joblib")
        self.report_path: str = self.cfg.get("training_report_path", "docs/training_report.md")
        self.target_col: str = self.cfg.get("target_column", "risk_level")
        self.cv_folds: int = int(self.cfg.get("cv_folds", 5))
        self.scoring: str = self.cfg.get("scoring", "accuracy")
        self.random_state: int = int(self.cfg.get("random_state", 42))
        self.n_jobs: int = int(self.cfg.get("n_jobs", -1))
        self.class_names: List[str] = self.cfg.get("class_names", ["low", "medium", "high"])

        # Results populated after train()
        self.results: List[Dict[str, Any]] = []
        self.best_pipeline: Optional[Pipeline] = None
        self.best_model_name: str = ""
        self.best_cv_score: float = -1.0

    # ── Public API ────────────────────────────────────────────────────────────

    def train(self, df_train: pd.DataFrame, target_col: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Train all enabled models on df_train.

        Args:
            df_train: Preprocessed training DataFrame (features + target).
            target_col: Override target column name.

        Returns:
            List of result dicts sorted by mean CV score descending.
        """
        target_col = target_col or self.target_col
        if target_col not in df_train.columns:
            raise ValueError(f"Target column '{target_col}' not in DataFrame.")

        X_train = df_train.drop(columns=[target_col]).select_dtypes(include=[np.number])
        y_train = df_train[target_col]

        cv = StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=self.random_state)
        models_cfg: Dict[str, Any] = self.cfg.get("models", {})

        self.results = []

        for model_name, model_cfg in models_cfg.items():
            if not model_cfg.get("enabled", True):
                logger.info(f"[{model_name}] Skipped (disabled in config).")
                continue

            logger.info(f"[{model_name}] Starting training...")

            try:
                clf_class = _import_class(model_cfg["class"])
                fixed_params = model_cfg.get("fixed_params", {})
                param_grid = model_cfg.get("param_grid", {})

                # Build Pipeline: impute → scale → classify
                pipeline = Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                    ("classifier", clf_class(**fixed_params)),
                ])

                if param_grid:
                    search = GridSearchCV(
                        pipeline,
                        param_grid,
                        cv=cv,
                        scoring=self.scoring,
                        n_jobs=self.n_jobs,
                        refit=True,
                        verbose=0,
                    )
                    search.fit(X_train, y_train)
                    best_pipe = search.best_estimator_
                    cv_scores = cross_val_score(best_pipe, X_train, y_train, cv=cv, scoring=self.scoring, n_jobs=self.n_jobs)
                    best_params = search.best_params_
                else:
                    pipeline.fit(X_train, y_train)
                    best_pipe = pipeline
                    cv_scores = cross_val_score(best_pipe, X_train, y_train, cv=cv, scoring=self.scoring, n_jobs=self.n_jobs)
                    best_params = {}

                mean_score = float(np.mean(cv_scores))
                std_score = float(np.std(cv_scores))

                result = {
                    "model_name": model_name,
                    "pipeline": best_pipe,
                    "best_params": best_params,
                    "cv_mean": mean_score,
                    "cv_std": std_score,
                    "cv_scores": cv_scores.tolist(),
                }
                self.results.append(result)

                logger.info(
                    f"[{model_name}] CV {self.scoring}: {mean_score:.4f} ± {std_score:.4f}"
                    + (f" | Best params: {best_params}" if best_params else "")
                )

            except Exception as exc:
                logger.error(f"[{model_name}] Training failed: {exc}", exc_info=True)

        # Sort by CV score descending
        self.results.sort(key=lambda r: r["cv_mean"], reverse=True)

        if self.results:
            best = self.results[0]
            self.best_pipeline = best["pipeline"]
            self.best_model_name = best["model_name"]
            self.best_cv_score = best["cv_mean"]
            logger.info(
                f"Best model: [{self.best_model_name}] "
                f"CV {self.scoring}: {self.best_cv_score:.4f}"
            )

        self._save_training_report()
        return self.results

    def save_best_model(self) -> str:
        """Serialize the best pipeline to disk using joblib."""
        if self.best_pipeline is None:
            raise RuntimeError("No trained model available. Call train() first.")

        os.makedirs(self.model_dir, exist_ok=True)
        path = os.path.join(self.model_dir, self.best_model_filename)
        joblib.dump(self.best_pipeline, path)
        logger.info(f"Best model [{self.best_model_name}] saved to: {path}")
        return path

    def load_model(self, path: Optional[str] = None) -> Pipeline:
        """Load a previously saved model pipeline from disk."""
        if path is None:
            path = os.path.join(self.model_dir, self.best_model_filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        pipeline = joblib.load(path)
        logger.info(f"Model loaded from: {path}")
        return pipeline

    # ── Private helpers ───────────────────────────────────────────────────────

    def _save_training_report(self) -> None:
        """Write a Markdown training summary to disk."""
        if not self.results:
            return

        # Resolve output path relative to project root
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        report_path = os.path.join(root, self.report_path)
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        lines = [
            "# FleetGuardian AI – Model Training Report\n",
            "## Cross-Validation Results\n",
            f"**Scoring metric:** `{self.scoring}`  |  **Folds:** `{self.cv_folds}`\n",
            "| Rank | Model | Mean CV Score | Std | Best Params |",
            "| --- | --- | --- | --- | --- |",
        ]
        for rank, r in enumerate(self.results, 1):
            params_str = ", ".join(
                f"`{k.split('__')[-1]}`={v}" for k, v in r["best_params"].items()
            ) if r["best_params"] else "—"
            lines.append(
                f"| {rank} | **{r['model_name']}** "
                f"| {r['cv_mean']:.4f} "
                f"| ±{r['cv_std']:.4f} "
                f"| {params_str} |"
            )

        lines += [
            "",
            f"## Best Model\n",
            f"**{self.best_model_name}** achieved the highest mean CV "
            f"{self.scoring} of **{self.best_cv_score:.4f}**.\n",
        ]

        with open(report_path, "w") as f:
            f.write("\n".join(lines))
        logger.info(f"Training report saved to: {report_path}")
