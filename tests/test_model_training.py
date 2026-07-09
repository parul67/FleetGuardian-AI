"""
tests/test_model_training.py
------------------------------
Unit and integration tests for ModelTrainer and ModelEvaluator.
Uses a small synthetic dataset — no CSV files or GPU required.
"""
from __future__ import annotations

import os
import tempfile
import pytest
import numpy as np
import pandas as pd

from app.ml.model_trainer import ModelTrainer, _import_class
from app.ml.model_evaluator import ModelEvaluator


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _make_synthetic_df(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """
    Generate a tiny synthetic telemetry-like DataFrame with numeric features
    and an ordinal target: 0=low, 1=medium, 2=high.
    """
    rng = np.random.default_rng(seed)

    fatigue   = rng.uniform(0, 1, n)
    distract  = rng.uniform(0, 1, n)
    phone_pct = rng.uniform(0, 100, n)
    speed     = rng.uniform(30, 130, n)
    lane_freq = rng.uniform(0, 5, n)
    alert_frq = rng.uniform(0, 5, n)
    blink     = rng.uniform(5, 25, n)
    behav     = 100 - (fatigue * 25 + distract * 20 + phone_pct * 0.2 + lane_freq * 4 + alert_frq * 3)
    behav     = np.clip(behav, 0, 100)

    # Simple deterministic target
    raw_risk  = fatigue * 0.4 + distract * 0.3 + phone_pct / 100 * 0.2 + lane_freq / 5 * 0.1
    risk      = pd.cut(raw_risk, bins=[-0.01, 0.33, 0.66, 1.01], labels=[0, 1, 2]).astype(int)

    return pd.DataFrame({
        "fatigue_score":           fatigue,
        "distraction_score":       distract,
        "phone_usage_percentage":  phone_pct,
        "speed":                   speed,
        "lane_deviation_frequency": lane_freq,
        "alert_frequency":         alert_frq,
        "blink_frequency_per_minute": blink,
        "driver_behavior_score":   behav,
        "risk_level":              risk,
    })


def _make_config(tmpdir: str, fast: bool = True) -> str:
    """Write a minimal YAML config into tmpdir, returning its path."""
    base = tmpdir.replace("\\", "/")
    # Use minimal grids when fast=True to keep tests sub-second
    if fast:
        rf_grid = "classifier__n_estimators: [50]"
        gb_grid = "classifier__n_estimators: [50]"
        xgb_grid = "classifier__n_estimators: [50]"
        lr_grid = "classifier__C: [1.0]"
    else:
        rf_grid  = "classifier__n_estimators: [100, 200]\n        classifier__max_depth: [6, null]"
        gb_grid  = "classifier__n_estimators: [100]\n        classifier__learning_rate: [0.1]"
        xgb_grid = "classifier__n_estimators: [100]\n        classifier__learning_rate: [0.1]"
        lr_grid  = "classifier__C: [0.1, 1.0]"

    content = f"""
model_training:
  model_dir: "{base}/models"
  best_model_filename: "best_model.joblib"
  training_report_path: "{base}/docs/training_report.md"
  evaluation_report_path: "{base}/docs/model_evaluation.md"
  train_csv: "{base}/train.csv"
  test_csv:  "{base}/test.csv"
  target_column: risk_level
  cv_folds: 3
  scoring: accuracy
  random_state: 42
  n_jobs: 1
  class_names:
    - 0
    - 1
    - 2
  models:
    random_forest:
      enabled: true
      class: "sklearn.ensemble.RandomForestClassifier"
      fixed_params:
        random_state: 42
      param_grid:
        {rf_grid}
    gradient_boosting:
      enabled: true
      class: "sklearn.ensemble.GradientBoostingClassifier"
      fixed_params:
        random_state: 42
      param_grid:
        {gb_grid}
    xgboost:
      enabled: true
      class: "xgboost.XGBClassifier"
      fixed_params:
        random_state: 42
        eval_metric: mlogloss
        verbosity: 0
      param_grid:
        {xgb_grid}
    logistic_regression:
      enabled: true
      class: "sklearn.linear_model.LogisticRegression"
      fixed_params:
        random_state: 42
        max_iter: 500
      param_grid:
        {lr_grid}
        classifier__solver: [lbfgs]
"""
    cfg_path = f"{base}/model_training_config.yaml"
    with open(cfg_path, "w") as f:
        f.write(content)
    return cfg_path


@pytest.fixture
def setup_env(tmp_path):
    """Returns (df_train, df_test, config_path, tmpdir_str)."""
    tmpdir = str(tmp_path)
    df = _make_synthetic_df(300)
    split = int(0.8 * len(df))
    df_train = df.iloc[:split].reset_index(drop=True)
    df_test  = df.iloc[split:].reset_index(drop=True)
    cfg_path = _make_config(tmpdir, fast=True)
    return df_train, df_test, cfg_path, tmpdir


# ─────────────────────────────────────────────────────────────────────────────
# _import_class helper tests
# ─────────────────────────────────────────────────────────────────────────────

def test_import_class_rf():
    from sklearn.ensemble import RandomForestClassifier
    cls = _import_class("sklearn.ensemble.RandomForestClassifier")
    assert cls is RandomForestClassifier


def test_import_class_xgb():
    from xgboost import XGBClassifier
    cls = _import_class("xgboost.XGBClassifier")
    assert cls is XGBClassifier


def test_import_class_bad_path():
    with pytest.raises((ModuleNotFoundError, AttributeError)):
        _import_class("nonexistent.module.FakeClass")


# ─────────────────────────────────────────────────────────────────────────────
# ModelTrainer unit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestModelTrainer:

    def test_train_returns_all_models(self, setup_env):
        df_train, _, cfg_path, _ = setup_env
        trainer = ModelTrainer(cfg_path)
        results = trainer.train(df_train)
        # Expect entries for all 4 enabled models
        assert len(results) == 4

    def test_results_sorted_descending(self, setup_env):
        df_train, _, cfg_path, _ = setup_env
        trainer = ModelTrainer(cfg_path)
        results = trainer.train(df_train)
        scores = [r["cv_mean"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_cv_scores_between_0_and_1(self, setup_env):
        df_train, _, cfg_path, _ = setup_env
        trainer = ModelTrainer(cfg_path)
        results = trainer.train(df_train)
        for r in results:
            assert 0.0 <= r["cv_mean"] <= 1.0
            assert r["cv_std"] >= 0.0

    def test_best_pipeline_set_after_train(self, setup_env):
        df_train, _, cfg_path, _ = setup_env
        trainer = ModelTrainer(cfg_path)
        trainer.train(df_train)
        assert trainer.best_pipeline is not None
        assert trainer.best_model_name != ""
        assert trainer.best_cv_score > 0.0

    def test_save_best_model_creates_file(self, setup_env):
        df_train, _, cfg_path, tmpdir = setup_env
        trainer = ModelTrainer(cfg_path)
        trainer.train(df_train)
        path = trainer.save_best_model()
        assert os.path.exists(path)
        assert path.endswith(".joblib")

    def test_load_model_returns_pipeline(self, setup_env):
        df_train, _, cfg_path, _ = setup_env
        trainer = ModelTrainer(cfg_path)
        trainer.train(df_train)
        path = trainer.save_best_model()
        loaded = trainer.load_model(path)
        # The pipeline should be predict-capable
        from sklearn.pipeline import Pipeline
        assert isinstance(loaded, Pipeline)

    def test_training_report_created(self, setup_env):
        df_train, _, cfg_path, tmpdir = setup_env
        trainer = ModelTrainer(cfg_path)
        trainer.train(df_train)
        # Report path is inside tmpdir/docs/
        report_path = os.path.join(tmpdir, "docs", "training_report.md")
        assert os.path.exists(report_path)
        content = open(report_path).read()
        assert "# FleetGuardian AI" in content
        assert "random_forest" in content

    def test_missing_target_raises(self, setup_env):
        df_train, _, cfg_path, _ = setup_env
        trainer = ModelTrainer(cfg_path)
        df_bad = df_train.drop(columns=["risk_level"])
        with pytest.raises(ValueError, match="Target column"):
            trainer.train(df_bad)

    def test_disabled_model_skipped(self, setup_env, tmp_path):
        """Models with enabled=false should be excluded from results."""
        df_train, _, _, tmpdir = setup_env
        # Make a fresh config with 1 model disabled
        cfg_path = _make_config(str(tmp_path), fast=True)
        import yaml
        with open(cfg_path) as f:
            raw = yaml.safe_load(f)
        raw["model_training"]["models"]["xgboost"]["enabled"] = False
        with open(cfg_path, "w") as f:
            yaml.dump(raw, f)

        trainer = ModelTrainer(cfg_path)
        results = trainer.train(df_train)
        names = [r["model_name"] for r in results]
        assert "xgboost" not in names
        assert len(results) == 3


# ─────────────────────────────────────────────────────────────────────────────
# ModelEvaluator unit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestModelEvaluator:

    def test_evaluate_returns_accuracy(self, setup_env):
        df_train, df_test, cfg_path, _ = setup_env
        trainer = ModelTrainer(cfg_path)
        trainer.train(df_train)
        path = trainer.save_best_model()

        evaluator = ModelEvaluator(cfg_path)
        result = evaluator.evaluate(df_test, model_path=path)

        assert "accuracy" in result
        assert 0.0 <= result["accuracy"] <= 1.0

    def test_evaluate_returns_confusion_matrix(self, setup_env):
        df_train, df_test, cfg_path, _ = setup_env
        trainer = ModelTrainer(cfg_path)
        trainer.train(df_train)
        path = trainer.save_best_model()

        evaluator = ModelEvaluator(cfg_path)
        result = evaluator.evaluate(df_test, model_path=path)

        cm = result["confusion_matrix"]
        assert isinstance(cm, list)
        assert len(cm) > 0          # non-empty

    def test_evaluate_accepts_pipeline_directly(self, setup_env):
        df_train, df_test, cfg_path, _ = setup_env
        trainer = ModelTrainer(cfg_path)
        trainer.train(df_train)

        evaluator = ModelEvaluator(cfg_path)
        result = evaluator.evaluate(df_test, pipeline=trainer.best_pipeline)
        assert result["accuracy"] >= 0.0

    def test_evaluation_report_created(self, setup_env):
        df_train, df_test, cfg_path, tmpdir = setup_env
        trainer = ModelTrainer(cfg_path)
        trainer.train(df_train)
        path = trainer.save_best_model()

        evaluator = ModelEvaluator(cfg_path)
        evaluator.evaluate(df_test, model_path=path)

        report_path = os.path.join(tmpdir, "docs", "model_evaluation.md")
        assert os.path.exists(report_path)
        content = open(report_path).read()
        assert "# FleetGuardian AI" in content
        assert "Accuracy" in content
        assert "Confusion Matrix" in content

    def test_evaluate_missing_target_raises(self, setup_env):
        df_train, df_test, cfg_path, _ = setup_env
        trainer = ModelTrainer(cfg_path)
        trainer.train(df_train)

        evaluator = ModelEvaluator(cfg_path)
        df_bad = df_test.drop(columns=["risk_level"])
        with pytest.raises(ValueError, match="Target column"):
            evaluator.evaluate(df_bad, pipeline=trainer.best_pipeline)
