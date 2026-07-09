"""
datasets/telemetry/collector.py
--------------------------------
TelemetryCollector – bridges Module 2 DriverState output to TelemetryRecord rows.

Usage::

    collector = TelemetryCollector(driver_id="D001", vehicle_id="V42", trip_id="T999")
    collector.start_trip()
    # in frame loop:
    record = collector.collect(state, speed=60.0, weather="clear")
    # on trip end:
    collector.end_trip()
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Optional, Any

from utils.logger import logger
from .schema import TelemetryRecord, RiskLevel, TimeOfDay, WeatherCondition


class TelemetryCollector:
    """
    Converts a DriverState snapshot + contextual metadata into a TelemetryRecord.

    Maintains trip-level state (start time, cumulative lane departure count,
    alert count) across frames.
    """

    def __init__(
        self,
        driver_id: str,
        vehicle_id: str,
        trip_id: str,
        risk_low_thresh: float = 0.35,
        risk_med_thresh: float = 0.65,
    ) -> None:
        self.driver_id = driver_id
        self.vehicle_id = vehicle_id
        self.trip_id = trip_id
        self._risk_low = risk_low_thresh
        self._risk_med = risk_med_thresh

        # Trip-level accumulators
        self._trip_start: Optional[float] = None
        self._lane_departure_count: int = 0
        self._alert_count: int = 0
        self._prev_lane_departure: bool = False

    # ------------------------------------------------------------------
    # Trip lifecycle
    # ------------------------------------------------------------------

    def start_trip(self) -> None:
        """Call once when a new trip/session begins."""
        self._trip_start = time.time()
        self._lane_departure_count = 0
        self._alert_count = 0
        self._prev_lane_departure = False
        logger.info(f"Trip started – driver={self.driver_id} vehicle={self.vehicle_id} trip={self.trip_id}")

    def end_trip(self) -> None:
        """Call once when a trip/session ends."""
        duration = time.time() - (self._trip_start or time.time())
        logger.info(
            f"Trip ended – driver={self.driver_id} trip={self.trip_id} "
            f"duration={duration:.0f}s alerts={self._alert_count} lane_departures={self._lane_departure_count}"
        )

    # ------------------------------------------------------------------
    # Per-frame collection
    # ------------------------------------------------------------------

    def collect(
        self,
        state: Any,                         # cv.feature_extraction.extractor.DriverState
        speed: float = 0.0,
        weather: str = WeatherCondition.UNKNOWN.value,
        blink_count_window: int = 30,       # denominator for blink-rate calculation (frames)
    ) -> TelemetryRecord:
        """
        Build a TelemetryRecord from a DriverState snapshot.

        Args:
            state:                DriverState from FeatureExtractor.
            speed:                Vehicle speed in km/h (from OBD / GPS).
            weather:              Weather condition string.
            blink_count_window:   Rolling window used for blink_rate (blinks/min) estimation.

        Returns:
            A filled TelemetryRecord ready for validation/storage.
        """
        now = time.time()
        trip_duration = now - (self._trip_start or now)

        # ── Accumulate lane departures (rising edge only) ─────────────────
        current_departure = bool(getattr(state, "lane_departure", False))
        if current_departure and not self._prev_lane_departure:
            self._lane_departure_count += 1
        self._prev_lane_departure = current_departure

        # ── Count active alerts this frame ────────────────────────────────
        active_alerts = getattr(state, "active_alerts", [])
        if active_alerts:
            self._alert_count += len(active_alerts)

        # ── Blink rate: blinks per minute estimate ─────────────────────────
        blink_count = getattr(state, "blink_count", 0)
        elapsed_min = max(trip_duration / 60.0, 1 / 60.0)  # avoid /0
        blink_rate = round(blink_count / elapsed_min, 2)

        # ── Distraction score (1 - attention) ────────────────────────────
        distraction_score = round(1.0 - getattr(state, "attention_score", 1.0), 3)

        # ── Risk label ────────────────────────────────────────────────────
        risk_score = getattr(state, "overall_risk_score", 0.0)
        risk_level = RiskLevel.from_score(risk_score, self._risk_low, self._risk_med).value

        # ── Time of day ───────────────────────────────────────────────────
        hour = datetime.fromtimestamp(now).hour
        time_of_day = TimeOfDay.from_hour(hour).value

        return TelemetryRecord(
            driver_id=self.driver_id,
            vehicle_id=self.vehicle_id,
            trip_id=self.trip_id,
            timestamp=now,
            speed=round(float(speed), 2),
            weather=weather,
            time_of_day=time_of_day,
            trip_duration=round(trip_duration, 2),

            # Drowsiness
            eye_ratio=round(getattr(state, "eye_ratio", 1.0), 4),
            mouth_ratio=round(getattr(state, "mouth_ratio", 0.0), 4),
            blink_rate=blink_rate,
            eye_closed_seconds=round(getattr(state, "eye_closed_seconds", 0.0), 3),
            yawning_count=int(getattr(state, "yawn_count", 0)),
            fatigue_score=round(getattr(state, "fatigue_score", 0.0), 4),

            # Distraction
            head_direction=str(getattr(state, "head_direction", "Forward")),
            distraction_score=distraction_score,

            # Phone
            phone_detected=bool(getattr(state, "phone_detected", False)),
            phone_usage_duration=round(getattr(state, "phone_usage_duration", 0.0), 2),

            # Seatbelt
            seatbelt_status=bool(getattr(state, "seatbelt_detected", False)),

            # Lane
            lane_offset=round(getattr(state, "lane_offset_px", 0.0), 2),
            lane_departure_count=self._lane_departure_count,

            # Aggregated
            alert_count=self._alert_count,
            risk_level=risk_level,
        )

    def reset_accumulators(self) -> None:
        """Reset trip-level counters without ending the trip."""
        self._lane_departure_count = 0
        self._alert_count = 0
        self._prev_lane_departure = False
