"""
datasets/telemetry/validator.py
--------------------------------
Row-level and dataframe-level validation for TelemetryRecord data.

Responsibilities:
  - Field range / type checks per record
  - Null / missing value handling (impute or drop)
  - Duplicate row removal
  - Categorical value enforcement
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from utils.logger import logger
from .schema import TelemetryRecord, RiskLevel, WeatherCondition, TimeOfDay


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Outcome of validating a single TelemetryRecord."""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


# ---------------------------------------------------------------------------
# DataValidator
# ---------------------------------------------------------------------------

_VALID_DIRECTIONS = {"Forward", "Left", "Right", "Up", "Down", "Unknown"}
_VALID_WEATHER = {w.value for w in WeatherCondition}
_VALID_TIME = {t.value for t in TimeOfDay}
_VALID_RISK = {r.value for r in RiskLevel}


class DataValidator:
    """
    Validates and cleans TelemetryRecord collections.

    Usage::

        validator = DataValidator()
        result = validator.validate_record(record)
        if not result.is_valid:
            print(result.errors)

        clean_records = validator.clean_dataset(records)
    """

    # Field ranges: (min, max)
    _RANGES: Dict[str, Tuple[float, float]] = {
        "eye_ratio":          (0.0,  1.0),
        "mouth_ratio":        (0.0,  1.0),
        "blink_rate":         (0.0,  60.0),
        "eye_closed_seconds": (0.0,  300.0),
        "fatigue_score":      (0.0,  1.0),
        "distraction_score":  (0.0,  1.0),
        "speed":              (0.0,  300.0),
        "lane_offset":        (-500.0, 500.0),
        "trip_duration":      (0.0,  86400.0),  # max 24 h
        "phone_usage_duration": (0.0, 3600.0),
    }

    # Default fill values for numeric fields when value is missing/NaN
    _DEFAULTS: Dict[str, Any] = {
        "eye_ratio":            1.0,
        "mouth_ratio":          0.0,
        "blink_rate":           15.0,
        "eye_closed_seconds":   0.0,
        "yawning_count":        0,
        "fatigue_score":        0.0,
        "distraction_score":    0.0,
        "phone_usage_duration": 0.0,
        "lane_offset":          0.0,
        "lane_departure_count": 0,
        "alert_count":          0,
        "speed":                0.0,
        "trip_duration":        0.0,
    }

    # ------------------------------------------------------------------
    # Single-record validation
    # ------------------------------------------------------------------

    def validate_record(self, record: TelemetryRecord) -> ValidationResult:
        """Full validation of a single TelemetryRecord. Returns a ValidationResult."""
        result = ValidationResult()

        # ── Required identity fields ───────────────────────────────────
        for id_field in ("driver_id", "vehicle_id", "trip_id"):
            val = getattr(record, id_field, "")
            if not val or not str(val).strip():
                result.add_error(f"Missing required field: {id_field}")

        # ── Numeric range checks ───────────────────────────────────────
        for attr, (lo, hi) in self._RANGES.items():
            val = getattr(record, attr, None)
            if val is None or (isinstance(val, float) and math.isnan(val)):
                result.add_warning(f"Field '{attr}' is None/NaN – will be imputed.")
            elif not (lo <= float(val) <= hi):
                result.add_error(f"Field '{attr}' = {val} out of valid range [{lo}, {hi}].")

        # ── Non-negative integer checks ────────────────────────────────
        for int_field in ("yawning_count", "lane_departure_count", "alert_count"):
            val = getattr(record, int_field, 0)
            if not isinstance(val, int) or val < 0:
                result.add_error(f"Field '{int_field}' must be a non-negative integer, got {val!r}.")

        # ── Boolean checks ─────────────────────────────────────────────
        for bool_field in ("phone_detected", "seatbelt_status"):
            val = getattr(record, bool_field, None)
            if not isinstance(val, bool):
                result.add_warning(f"Field '{bool_field}' is not bool ({type(val).__name__}) – will be cast.")

        # ── Categorical checks ─────────────────────────────────────────
        if record.head_direction not in _VALID_DIRECTIONS:
            result.add_error(f"Invalid head_direction: '{record.head_direction}'. Valid: {_VALID_DIRECTIONS}")

        if record.weather not in _VALID_WEATHER:
            result.add_warning(f"Unrecognised weather '{record.weather}' – defaulting to 'unknown'.")

        if record.time_of_day not in _VALID_TIME:
            result.add_error(f"Invalid time_of_day: '{record.time_of_day}'.")

        if record.risk_level not in _VALID_RISK:
            result.add_error(f"Invalid risk_level: '{record.risk_level}'.")

        return result

    # ------------------------------------------------------------------
    # Record-level repair
    # ------------------------------------------------------------------

    def repair_record(self, record: TelemetryRecord) -> TelemetryRecord:
        """
        Attempt to fix common issues in-place:
        - Impute NaN/None numerics with defaults
        - Cast booleans
        - Normalise categoricals
        Returns the (possibly modified) record.
        """
        # Impute numeric NaN/None
        for attr, default in self._DEFAULTS.items():
            val = getattr(record, attr, None)
            if val is None or (isinstance(val, float) and math.isnan(val)):
                setattr(record, attr, default)
                logger.debug(f"Imputed {attr} = {default}")

        # Clamp ranges
        for attr, (lo, hi) in self._RANGES.items():
            val = getattr(record, attr, None)
            if val is not None and not math.isnan(float(val)):
                clamped = max(lo, min(hi, float(val)))
                if clamped != val:
                    setattr(record, attr, clamped)

        # Cast booleans
        record.phone_detected = bool(record.phone_detected)
        record.seatbelt_status = bool(record.seatbelt_status)

        # Normalise categoricals
        if record.weather not in _VALID_WEATHER:
            record.weather = WeatherCondition.UNKNOWN.value

        if record.head_direction not in _VALID_DIRECTIONS:
            record.head_direction = "Unknown"

        # Ensure non-negative ints
        record.yawning_count = max(0, int(record.yawning_count))
        record.lane_departure_count = max(0, int(record.lane_departure_count))
        record.alert_count = max(0, int(record.alert_count))

        return record

    # ------------------------------------------------------------------
    # Dataset-level cleaning
    # ------------------------------------------------------------------

    def clean_dataset(
        self,
        records: List[TelemetryRecord],
        drop_invalid: bool = True,
        remove_duplicates: bool = True,
        dedup_keys: Optional[List[str]] = None,
    ) -> Tuple[List[TelemetryRecord], Dict[str, int]]:
        """
        Validate, repair, and deduplicate a list of records.

        Args:
            records:           Input records.
            drop_invalid:      If True, records with unrecoverable errors are dropped.
                               If False, they are repaired and kept.
            remove_duplicates: Remove exact duplicate rows (same driver+vehicle+trip+timestamp bucket).
            dedup_keys:        Fields to use for deduplication (defaults below).

        Returns:
            (clean_records, stats_dict)
        """
        if dedup_keys is None:
            dedup_keys = ["driver_id", "vehicle_id", "trip_id", "timestamp"]

        stats = {
            "input": len(records),
            "repaired": 0,
            "dropped_invalid": 0,
            "dropped_duplicate": 0,
            "output": 0,
        }

        cleaned: List[TelemetryRecord] = []

        for record in records:
            # Repair first (impute NaN, cast types)
            record = self.repair_record(record)

            # Validate after repair
            result = self.validate_record(record)
            if not result.is_valid:
                if drop_invalid:
                    stats["dropped_invalid"] += 1
                    logger.warning(f"Dropped invalid record {record.record_id}: {result.errors}")
                    continue
                else:
                    stats["repaired"] += 1
                    logger.warning(f"Kept repaired record {record.record_id} with errors: {result.errors}")
            else:
                if result.warnings:
                    stats["repaired"] += 1

            cleaned.append(record)

        # ── Duplicate removal ──────────────────────────────────────────
        if remove_duplicates:
            seen: set = set()
            deduped: List[TelemetryRecord] = []
            for rec in cleaned:
                # Round timestamp to nearest second for dedup window
                key_vals = []
                for k in dedup_keys:
                    v = getattr(rec, k, "")
                    if k == "timestamp":
                        v = round(float(v))  # 1-second bucket
                    key_vals.append(str(v))
                key = "|".join(key_vals)

                if key in seen:
                    stats["dropped_duplicate"] += 1
                else:
                    seen.add(key)
                    deduped.append(rec)
            cleaned = deduped

        stats["output"] = len(cleaned)
        logger.info(
            f"Dataset cleaned: {stats['input']} in → {stats['output']} out "
            f"({stats['dropped_invalid']} invalid dropped, {stats['dropped_duplicate']} dupes removed, "
            f"{stats['repaired']} repaired)"
        )
        return cleaned, stats
