"""
tests/test_feature_engineering.py
-----------------------------------
Unit and integration tests for the Feature Engineering module.
"""
from __future__ import annotations

import os
import tempfile
import pytest
import numpy as np
import pandas as pd

from pipelines.feature_engineering.engineer import FeatureEngineer
from pipelines.feature_engineering.pipeline import FeatureEngineeringPipeline


@pytest.fixture
def base_df() -> pd.DataFrame:
    """Returns a sample DataFrame representing raw telemetry logs for a driver trip."""
    data = {
        "driver_id": ["D01"] * 10,
        "vehicle_id": ["V01"] * 10,
        "trip_id": ["T01"] * 10,
        "speed": [60.0, 70.0, 80.0, 90.0, np.nan, 85.0, 75.0, 65.0, 55.0, 50.0],
        "eye_ratio": [0.35, 0.38, 0.28, 0.31, 0.36, 0.15, 0.32, 0.33, 0.32, 0.18],
        "mouth_ratio": [0.1, 0.12, 0.15, 0.11, 0.14, 0.45, 0.12, 0.11, 0.13, 0.48],
        "blink_rate": [12.0, 15.0, 10.0, 14.0, 11.0, 8.0, 16.0, 13.0, 12.0, 7.0],
        "eye_closed_seconds": [0.0, 0.0, 0.0, 0.0, 0.0, 2.5, 0.0, 0.0, 0.0, 3.0],
        "yawning_count": [0, 0, 0, 0, 0, 1, 1, 1, 1, 2],
        "fatigue_score": [0.05, 0.08, 0.1, 0.07, 0.06, 0.8, 0.04, 0.09, 0.12, 0.95],
        "head_direction": ["Forward", "Forward", "Left", "Forward", "Forward", "Forward", "Forward", "Right", "Forward", "Forward"],
        "distraction_score": [0.02, 0.05, 0.35, 0.03, 0.04, 0.06, 0.02, 0.45, 0.05, 0.08],
        "phone_detected": [0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
        "phone_usage_duration": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 45.0, 90.0, 135.0],
        "seatbelt_status": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "lane_offset": [2.5, 4.0, -10.0, 1.2, 3.3, 20.0, 1.5, 5.0, -2.0, 15.0],
        "lane_departure_count": [0, 0, 1, 1, 1, 2, 2, 2, 2, 3],
        "weather": ["clear"] * 10,
        "time_of_day": ["morning"] * 10,
        "trip_duration": [60.0, 120.0, 180.0, 240.0, 300.0, 360.0, 420.0, 480.0, 540.0, 600.0],
        "alert_count": [0, 0, 1, 1, 1, 2, 2, 3, 3, 4],
        "risk_level": ["low", "low", "medium", "low", "low", "high", "low", "medium", "low", "high"]
    }
    return pd.DataFrame(data)


# ─────────────────────────────────────────────────────────────
# FeatureEngineer Unit Tests
# ─────────────────────────────────────────────────────────────

def test_feature_engineer_calculations(base_df: pd.DataFrame):
    engineer = FeatureEngineer()
    df_eng = engineer.transform(base_df)

    # 1. Check expanding average speed
    # non-nan speed list for trip T01: [60.0, 70.0, 80.0, 90.0, nan, 85.0, 75.0, 65.0, 55.0, 50.0]
    # At index 2: speed=80.0, expanding mean of [60.0, 70.0, 80.0] = 70.0
    assert df_eng["average_speed"].iloc[2] == pytest.approx(70.0)

    # 2. Check phone usage percentage
    # At index 7: phone_usage_duration=45.0, trip_duration=480.0 -> pct = 45.0 / 480.0 * 100 = 9.375
    assert df_eng["phone_usage_percentage"].iloc[7] == pytest.approx(9.375)

    # 3. Check lane deviation frequency (deviations per minute)
    # At index 9: departures=3, duration=600s (10 min) -> departures/min = 3 / 10 = 0.3
    assert df_eng["lane_deviation_frequency"].iloc[9] == pytest.approx(0.3)

    # 4. Check alert frequency (alerts per minute)
    # At index 9: alerts=4, duration=600s (10 min) -> alerts/min = 4 / 10 = 0.4
    assert df_eng["alert_frequency"].iloc[9] == pytest.approx(0.4)

    # 5. Check rolling blink rate (5 records window)
    # At index 2 (size 3): mean of [12.0, 15.0, 10.0] = 12.333
    assert df_eng["blink_frequency_per_minute"].iloc[2] == pytest.approx(12.3333, abs=1e-3)

    # 6. Check fatigue trend (score - 5-record rolling mean)
    # At index 5: fatigue_score=0.8, past 5 (indices 1-5): [0.08, 0.1, 0.07, 0.06, 0.8] -> mean = 0.222
    # trend = 0.8 - 0.222 = 0.578
    assert df_eng["fatigue_trend"].iloc[5] == pytest.approx(0.8 - 0.222, abs=1e-3)

    # 7. Check driver behavior score bounds
    # Ensure it lies within [0, 100]
    assert (df_eng["driver_behavior_score"] >= 0.0).all()
    assert (df_eng["driver_behavior_score"] <= 100.0).all()
    # Behavior score at index 0 should be relatively high (no fatigue, phone usage, seatbelt on)
    assert df_eng["driver_behavior_score"].iloc[0] > 80.0


# ─────────────────────────────────────────────────────────────
# Pipeline Integration Tests
# ─────────────────────────────────────────────────────────────

def test_feature_engineering_pipeline(base_df: pd.DataFrame):
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = tmpdir.replace('\\', '/')
        raw_csv = f"{base_dir}/fleet_telemetry_raw.csv"
        
        # Make a larger sample df by duplicating to satisfy stratification constraints
        df1 = base_df.copy()
        df2 = base_df.copy()
        df2["driver_id"] = "D02"
        df2["trip_id"] = "T02"
        # Combine
        combined_df = pd.concat([df1, df2], ignore_index=True)
        combined_df.to_csv(raw_csv, index=False)

        # Create config file
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

        # Run pipeline
        pipeline = FeatureEngineeringPipeline(config_path)
        df_train, df_val, df_test = pipeline.run_pipeline(raw_csv)

        # Ensure engineered files exist
        assert os.path.exists(f"{base_dir}/processed/train_engineered.csv")
        assert os.path.exists(f"{base_dir}/processed/val_engineered.csv")
        assert os.path.exists(f"{base_dir}/processed/test_engineered.csv")

        # Check shapes (total size 20: test = 4, val = 4, train = 12)
        assert df_test.shape[0] == 4
        assert df_val.shape[0] == 4
        assert df_train.shape[0] == 12

        # Check engineered features exist in preprocessed dataframes
        for col in [
            "average_speed", "phone_usage_percentage", "lane_deviation_frequency",
            "alert_frequency", "blink_frequency_per_minute", "fatigue_trend",
            "driver_behavior_score"
        ]:
            assert col in df_train.columns
            assert col in df_val.columns
            assert col in df_test.columns

        # Verify reports are generated
        assert os.path.exists(f"{base_dir}/models/feature_importance.csv")
        assert os.path.exists(f"{base_dir}/models/correlation_matrix.csv")

        # Check documentation markdown reports
        # The docs folder is resolved relative to the pipeline code, so let's verify if they exist
        # We also mock it or verify it locally. Since the pipeline writes to relative '../../docs',
        # let's make sure files exist relative to where they're generated.
        docs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
        assert os.path.exists(os.path.join(docs_path, "feature_importance.md"))
        assert os.path.exists(os.path.join(docs_path, "correlation_analysis.md"))
