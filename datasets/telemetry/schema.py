"""
datasets/telemetry/schema.py
-----------------------------
Canonical data model for a single driver telemetry record.
All fields map directly to the required CSV columns.
"""
from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class RiskLevel(str, Enum):
    """Ordinal risk classification for accident prediction."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def from_score(cls, score: float, low_thresh: float = 0.35, med_thresh: float = 0.65) -> "RiskLevel":
        """Map a continuous risk score [0,1] to a categorical level."""
        if score < low_thresh:
            return cls.LOW
        if score < med_thresh:
            return cls.MEDIUM
        return cls.HIGH


class TimeOfDay(str, Enum):
    MORNING = "morning"     # 06–12
    AFTERNOON = "afternoon" # 12–17
    EVENING = "evening"     # 17–21
    NIGHT = "night"         # 21–06

    @classmethod
    def from_hour(cls, hour: int) -> "TimeOfDay":
        if 6 <= hour < 12:
            return cls.MORNING
        if 12 <= hour < 17:
            return cls.AFTERNOON
        if 17 <= hour < 21:
            return cls.EVENING
        return cls.NIGHT


class WeatherCondition(str, Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    FOG = "fog"
    SNOW = "snow"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# TelemetryRecord
# ---------------------------------------------------------------------------

@dataclass
class TelemetryRecord:
    """
    Single row in the fleet telemetry dataset.
    All fields correspond to required CSV columns.
    """
    # ── Identity ──────────────────────────────────────────────────────────
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    driver_id: str = ""
    vehicle_id: str = ""
    trip_id: str = ""
    timestamp: float = field(default_factory=time.time)

    # ── Contextual ────────────────────────────────────────────────────────
    speed: float = 0.0                          # km/h
    weather: str = WeatherCondition.UNKNOWN.value
    time_of_day: str = TimeOfDay.NIGHT.value
    trip_duration: float = 0.0                  # seconds elapsed since trip start

    # ── Drowsiness (from DrowsinessDetector) ─────────────────────────────
    eye_ratio: float = 1.0                      # EAR
    mouth_ratio: float = 0.0                    # MAR
    blink_rate: float = 0.0                     # blinks/min
    eye_closed_seconds: float = 0.0
    yawning_count: int = 0
    fatigue_score: float = 0.0                  # [0,1]

    # ── Distraction (from DistractionDetector) ───────────────────────────
    head_direction: str = "Forward"
    distraction_score: float = 0.0              # 1 - attention_score

    # ── Phone (from PhoneDetector) ────────────────────────────────────────
    phone_detected: bool = False
    phone_usage_duration: float = 0.0           # seconds

    # ── Seatbelt (from SeatbeltDetector) ─────────────────────────────────
    seatbelt_status: bool = False

    # ── Lane (from LaneDetector) ──────────────────────────────────────────
    lane_offset: float = 0.0                    # pixels from center
    lane_departure_count: int = 0

    # ── Aggregated alerts ─────────────────────────────────────────────────
    alert_count: int = 0

    # ── Target label ──────────────────────────────────────────────────────
    risk_level: str = RiskLevel.LOW.value

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def csv_columns(cls) -> list[str]:
        """Returns the ordered list of CSV column names (excluding record_id/timestamp internals)."""
        return [
            "driver_id", "vehicle_id", "trip_id",
            "speed", "eye_ratio", "mouth_ratio", "blink_rate",
            "eye_closed_seconds", "yawning_count", "fatigue_score",
            "head_direction", "distraction_score",
            "phone_detected", "phone_usage_duration",
            "seatbelt_status", "lane_offset", "lane_departure_count",
            "weather", "time_of_day", "trip_duration",
            "alert_count", "risk_level",
        ]
