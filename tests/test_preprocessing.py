"""
tests/test_preprocessing.py
------------------------------
Unit tests for the Data Preprocessing module.
Covers: DatasetLoader, MissingValueImputer, CategoricalEncoder,
FeatureScaler, OutlierDetector, DataSplitter, ArtifactStore, PreprocessingPipeline.
"""
from __future__ import annotations

import os
import tempfile
import pytest
import numpy as np
import pandas as pd

from pipelines.preprocessing.loader import DatasetLoader
from pipelines.preprocessing.imputer import MissingValueImputer
from pipelines.preprocessing.encoder import CategoricalEncoder
from pipelines.preprocessing.scaler import FeatureScaler
from pipelines.preprocessing.outlier import OutlierDetector
from pipelines.preprocessing.splitter import DataSplitter
from pipelines.preprocessing.artifact_store import ArtifactStore
from pipelines.preprocessing.pipeline import PreprocessingPipeline


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Returns a sample DataFrame mimicking raw telemetry data (20 rows to support stratification)."""
    data = {
        "driver_id": ["D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09", "D10"],
        "vehicle_id": ["V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V09", "V10"],
        "trip_id": ["T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10"],
        "speed": [65.0, 80.0, 55.0, np.nan, 70.0, 120.0, 45.0, 60.0, 90.0, 110.0],
        "eye_ratio": [0.35, 0.38, 0.28, 0.31, 0.36, 0.15, np.nan, 0.33, 0.32, 0.18],
        "mouth_ratio": [0.1, 0.12, 0.15, 0.11, 0.14, 0.45, 0.12, np.nan, 0.13, 0.48],
        "blink_rate": [12.0, 15.0, 10.0, 14.0, 11.0, 8.0, 16.0, 13.0, np.nan, 7.0],
        "eye_closed_seconds": [0.0, 0.0, 0.0, 0.0, 0.0, 2.5, 0.0, 0.0, 0.0, 3.0],
        "yawning_count": [0, 0, 0, 0, 0, 1, 0, 0, 0, 2],
        "fatigue_score": [0.05, 0.08, 0.1, 0.07, 0.06, 0.8, 0.04, 0.09, 0.12, 0.95],
        "head_direction": ["Forward", "Forward", "Left", "Forward", "Forward", "Forward", "Forward", "Right", "Forward", "Forward"],
        "distraction_score": [0.02, 0.05, 0.35, 0.03, 0.04, 0.06, 0.02, 0.45, 0.05, 0.08],
        "phone_detected": [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
        "phone_usage_duration": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 45.0, 0.0, 0.0],
        "seatbelt_status": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "lane_offset": [2.5, 4.0, -10.0, 1.2, 3.3, 20.0, 1.5, 5.0, -2.0, 15.0],
        "lane_departure_count": [0, 0, 1, 0, 0, 2, 0, 0, 0, 1],
        "weather": ["clear", "rainy", "clear", "clear", "snowy", "clear", "clear", "rainy", "clear", "clear"],
        "time_of_day": ["morning", "morning", "afternoon", "evening", "night", "morning", "evening", "afternoon", "morning", "night"],
        "trip_duration": [300.0, 600.0, 1200.0, 180.0, 450.0, 1800.0, 900.0, 60.0, 1500.0, 2400.0],
        "alert_count": [0, 0, 1, 0, 0, 2, 0, 1, 0, 3],
        "risk_level": ["low", "low", "medium", "low", "low", "high", "low", "medium", "low", "high"]
    }
    # Duplicate to make it 20 rows so that stratification in train_test_split (min 2 per class in test) works
    df1 = pd.DataFrame(data)
    df2 = pd.DataFrame(data)
    # Ensure driver_id and other IDs remain unique-ish to prevent any indexing bugs
    df2["driver_id"] = df2["driver_id"] + "_dup"
    df2["trip_id"] = df2["trip_id"] + "_dup"
    return pd.concat([df1, df2], ignore_index=True)


# ─────────────────────────────────────────────────────────────
# DatasetLoader Tests
# ─────────────────────────────────────────────────────────────

def test_loader_valid_load(sample_df: pd.DataFrame):
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "telemetry.csv").replace('\\', '/')
        sample_df.to_csv(csv_path, index=False)

        loader = DatasetLoader(csv_path)
        df = loader.load(drop_ids=False)

        assert df.shape == (20, 22)
        assert list(df.columns) == list(sample_df.columns)
        assert df["speed"].dtype == np.float64
        # check bool casting
        assert df["phone_detected"].dtype == "boolean"
        assert df["seatbelt_status"].dtype == "boolean"
        # check cat string and lowercase coercion
        assert df["weather"].iloc[1] == "rainy"
        assert df["head_direction"].iloc[2] == "left"


def test_loader_drop_ids(sample_df: pd.DataFrame):
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "telemetry.csv").replace('\\', '/')
        sample_df.to_csv(csv_path, index=False)

        loader = DatasetLoader(csv_path)
        df = loader.load(drop_ids=True)

        assert "driver_id" not in df.columns
        assert "vehicle_id" not in df.columns
        assert "trip_id" not in df.columns
        assert df.shape[1] == 19


# ─────────────────────────────────────────────────────────────
# MissingValueImputer Tests
# ─────────────────────────────────────────────────────────────

def test_missing_value_imputer(sample_df: pd.DataFrame):
    # Coerce to format expected by loader/imputer
    df = sample_df.copy()
    df["head_direction"] = df["head_direction"].astype(str).str.lower()
    df["weather"] = df["weather"].astype(str).str.lower()
    df["time_of_day"] = df["time_of_day"].astype(str).str.lower()

    numeric_cols = ["speed", "eye_ratio", "mouth_ratio", "blink_rate"]
    categorical_cols = ["head_direction", "weather"]

    imputer = MissingValueImputer(
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
        numeric_strategy="median",
        categorical_strategy="most_frequent"
    )

    imputer.fit(df)
    df_clean = imputer.transform(df)

    assert df_clean["speed"].isnull().sum() == 0
    assert df_clean["eye_ratio"].isnull().sum() == 0
    assert df_clean["mouth_ratio"].isnull().sum() == 0
    assert df_clean["blink_rate"].isnull().sum() == 0

    # Ensure median was imputed for speed (median of non-nan values is 75.0)
    # Values: 65, 80, 55, 70, 120, 45, 60, 90, 110 (sorted: 45, 55, 60, 65, 70, 80, 90, 110, 120 -> median is 70.0)
    assert df_clean["speed"].iloc[3] == 70.0


# ─────────────────────────────────────────────────────────────
# CategoricalEncoder Tests
# ─────────────────────────────────────────────────────────────

def test_categorical_encoder_onehot(sample_df: pd.DataFrame):
    df = sample_df.copy()
    # Normalize cases
    for col in ["head_direction", "weather", "time_of_day"]:
        df[col] = df[col].astype(str).str.lower()

    categorical_cols = ["head_direction", "weather"]
    encoder = CategoricalEncoder(
        categorical_cols=categorical_cols,
        target_col="risk_level"
    )

    df_enc = encoder.fit_transform(df)

    # Original categorical columns should be dropped
    assert "head_direction" not in df_enc.columns
    assert "weather" not in df_enc.columns

    # One hot encoded columns must exist
    assert "head_direction_forward" in df_enc.columns
    assert "weather_clear" in df_enc.columns

    # Target risk_level must be mapped
    assert df_enc["risk_level"].iloc[0] == 0  # low
    assert df_enc["risk_level"].iloc[2] == 1  # medium
    assert df_enc["risk_level"].iloc[5] == 2  # high


def test_categorical_encoder_labelencoder(sample_df: pd.DataFrame):
    df = sample_df.copy()
    for col in ["weather"]:
        df[col] = df[col].astype(str).str.lower()

    # Use weather as a target column to test LabelEncoder since it is not risk_level
    encoder = CategoricalEncoder(
        categorical_cols=[],
        target_col="weather",
        target_mapping=None
    )

    df_enc = encoder.fit_transform(df)
    # Classes: clear (0), rainy (1), snowy (2) sorted alphabetically
    assert df_enc["weather"].iloc[0] == 0  # clear
    assert df_enc["weather"].iloc[1] == 1  # rainy
    assert df_enc["weather"].iloc[4] == 2  # snowy


# ─────────────────────────────────────────────────────────────
# FeatureScaler Tests
# ─────────────────────────────────────────────────────────────

def test_feature_scaler(sample_df: pd.DataFrame):
    df = sample_df.copy().dropna()  # dropna to test scaling cleanly
    numeric_cols = ["speed", "eye_ratio", "mouth_ratio"]

    # Test StandardScaler
    scaler = FeatureScaler(numeric_cols=numeric_cols, method="standard")
    df_scaled = scaler.fit_transform(df)
    assert np.allclose(df_scaled[numeric_cols].mean(), 0, atol=1e-5)

    # Test MinMaxScaler
    scaler_minmax = FeatureScaler(numeric_cols=numeric_cols, method="minmax", feature_range=(0.0, 1.0))
    df_minmax = scaler_minmax.fit_transform(df)
    assert df_minmax["speed"].min() == pytest.approx(0.0)
    assert df_minmax["speed"].max() == pytest.approx(1.0)


# ─────────────────────────────────────────────────────────────
# OutlierDetector Tests
# ─────────────────────────────────────────────────────────────

def test_outlier_detector_clip(sample_df: pd.DataFrame):
    df = sample_df.copy()
    # Fill speed NaN first to test outlier detector
    df["speed"] = df["speed"].fillna(75.0)

    detector = OutlierDetector(
        numeric_cols=["speed"],
        method="iqr",
        iqr_multiplier=1.0,
        action="clip"
    )

    detector.fit(df)
    # check bounds computed correctly
    assert "speed" in detector.bounds
    lower, upper = detector.bounds["speed"]
    assert lower < 60.0
    assert upper > 100.0

    df_trans = detector.transform(df)
    # check no values in df_trans exceed the bounds
    assert (df_trans["speed"] >= lower).all()
    assert (df_trans["speed"] <= upper).all()


def test_outlier_detector_remove(sample_df: pd.DataFrame):
    df = sample_df.copy()
    df["speed"] = df["speed"].fillna(75.0)

    detector = OutlierDetector(
        numeric_cols=["speed"],
        method="iqr",
        iqr_multiplier=0.5,  # narrow bounds
        action="remove"
    )

    detector.fit(df)

    # With is_training=True, outlier rows should be deleted
    df_train_processed = detector.transform(df, is_training=True)
    assert len(df_train_processed) < len(df)

    # With is_training=False, it should clip, preserving row count
    df_test_processed = detector.transform(df, is_training=False)
    assert len(df_test_processed) == len(df)


# ─────────────────────────────────────────────────────────────
# DataSplitter Tests
# ─────────────────────────────────────────────────────────────

def test_data_splitter(sample_df: pd.DataFrame):
    splitter = DataSplitter(test_size=0.2, val_size=0.25, random_state=42, stratify_col="risk_level")
    df_train, df_val, df_test = splitter.split(sample_df)

    # Total size 20
    # test_size: 0.2 of 20 = 4 rows
    # remainder: 16 rows
    # val_size: 0.25 of 16 = 4 rows
    # train_size: remainder - val = 12 rows
    assert len(df_test) == 4
    assert len(df_val) == 4
    assert len(df_train) == 12


# ─────────────────────────────────────────────────────────────
# ArtifactStore Tests
# ─────────────────────────────────────────────────────────────

def test_artifact_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ArtifactStore(tmpdir)
        test_obj = {"scaler_mean": [0.5, 0.2], "method": "standard"}

        store.save("my_scaler", test_obj)
        loaded = store.load("my_scaler")

        assert loaded == test_obj


# ─────────────────────────────────────────────────────────────
# PreprocessingPipeline Integration Tests
# ─────────────────────────────────────────────────────────────

def test_pipeline_run_integration(sample_df: pd.DataFrame):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save raw dataset
        # Convert path backslashes to forward slashes to avoid yaml loading parse errors on Windows
        base_dir = tmpdir.replace('\\', '/')
        csv_path = f"{base_dir}/fleet_telemetry_raw.csv"
        sample_df.to_csv(csv_path, index=False)

        # Create preprocessing_config.yaml in the temporary directory
        config_path = f"{base_dir}/preprocessing_config_temp.yaml"
        config_content = f"""
preprocessing:
  artifacts_dir: "{base_dir}/models"
  processed_dir: "{base_dir}/processed"

  numeric_features:
    - speed
    - eye_ratio
    - mouth_ratio
    - blink_rate
    - eye_closed_seconds
    - yawning_count
    - fatigue_score
    - distraction_score
    - phone_usage_duration
    - lane_offset
    - lane_departure_count
    - trip_duration
    - alert_count

  categorical_features:
    - head_direction
    - weather
    - time_of_day

  boolean_features:
    - phone_detected
    - seatbelt_status

  target_column: risk_level

  drop_columns:
    - driver_id
    - vehicle_id
    - trip_id

  imputation:
    numeric_strategy: median
    categorical_strategy: most_frequent

  outlier_detection:
    method: iqr
    iqr_multiplier: 1.5
    action: clip

  scaling:
    method: standard

  split:
    test_size: 0.2
    val_size: 0.25
    random_state: 42
    stratify: true
"""
        with open(config_path, "w") as f:
            f.write(config_content)

        # Initialize and run pipeline
        pipeline = PreprocessingPipeline(config_path)
        df_train, df_val, df_test = pipeline.run_pipeline(csv_path)

        # Assert shapes
        assert len(df_test) == 4
        assert len(df_val) == 4
        assert len(df_train) == 12

        # Processed directory should contain the CSVs
        assert os.path.exists(f"{base_dir}/processed/train.csv")
        assert os.path.exists(f"{base_dir}/processed/val.csv")
        assert os.path.exists(f"{base_dir}/processed/test.csv")

        # Models directory should contain serialized objects
        assert os.path.exists(f"{base_dir}/models/scaler.joblib")
        assert os.path.exists(f"{base_dir}/models/categorical_encoder.joblib")
        assert os.path.exists(f"{base_dir}/models/imputer.joblib")
        assert os.path.exists(f"{base_dir}/models/outlier_detector.joblib")

        # Test loading from stored artifacts
        new_pipeline = PreprocessingPipeline(config_path)
        new_pipeline.load_fitted_pipeline()
        assert new_pipeline._fitted

        # Transform a new sample
        sample_inf = sample_df.iloc[[0]].copy()
        processed_inf = new_pipeline.transform(sample_inf)
        assert processed_inf.shape[0] == 1
