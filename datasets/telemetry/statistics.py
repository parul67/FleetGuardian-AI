"""
datasets/telemetry/statistics.py
----------------------------------
DatasetStatistics – computes and reports summary stats for the telemetry dataset.

Outputs:
  - Per-column descriptive stats (count, mean, std, min, max, quartiles)
  - Risk level distribution
  - Class balance / imbalance ratio
  - Missing value report
  - Correlation highlights (fatigue vs risk, distraction vs risk)
"""
from __future__ import annotations

import csv
import math
import os
from collections import Counter
from typing import List, Dict, Any, Optional

from utils.logger import logger
from .schema import TelemetryRecord, RiskLevel


# ---------------------------------------------------------------------------
# Helper: simple stats without external dependencies
# ---------------------------------------------------------------------------

def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else float("nan")

def _variance(values: List[float]) -> float:
    if len(values) < 2:
        return float("nan")
    m = _mean(values)
    return sum((x - m) ** 2 for x in values) / (len(values) - 1)

def _std(values: List[float]) -> float:
    v = _variance(values)
    return math.sqrt(v) if not math.isnan(v) else float("nan")

def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return float("nan")
    sorted_v = sorted(values)
    idx = (pct / 100.0) * (len(sorted_v) - 1)
    lo, hi = int(idx), min(int(idx) + 1, len(sorted_v) - 1)
    frac = idx - lo
    return sorted_v[lo] * (1 - frac) + sorted_v[hi] * frac

def _corr(xs: List[float], ys: List[float]) -> float:
    """Pearson correlation coefficient."""
    if len(xs) < 2 or len(ys) < 2:
        return float("nan")
    mx, my = _mean(xs), _mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den != 0 else float("nan")


# ---------------------------------------------------------------------------
# DatasetStatistics
# ---------------------------------------------------------------------------

_NUMERIC_FIELDS = [
    "speed", "eye_ratio", "mouth_ratio", "blink_rate", "eye_closed_seconds",
    "yawning_count", "fatigue_score", "distraction_score", "phone_usage_duration",
    "lane_offset", "lane_departure_count", "trip_duration", "alert_count",
]

_BOOL_FIELDS = ["phone_detected", "seatbelt_status"]
_CAT_FIELDS  = ["head_direction", "weather", "time_of_day", "risk_level"]


class DatasetStatistics:
    """
    Compute and display dataset statistics from a list of TelemetryRecord objects
    or directly from a CSV file.
    """

    def compute(self, records: List[TelemetryRecord]) -> Dict[str, Any]:
        """
        Compute full statistics on a record list.

        Returns:
            Nested dict with keys: numeric, boolean, categorical, correlations, class_balance, missing.
        """
        if not records:
            logger.warning("DatasetStatistics.compute() called with empty records list.")
            return {}

        n = len(records)
        stats: Dict[str, Any] = {"total_records": n}

        # ── Numeric stats ──────────────────────────────────────────────
        numeric_stats: Dict[str, Dict[str, float]] = {}
        for field_name in _NUMERIC_FIELDS:
            values = []
            missing = 0
            for rec in records:
                v = getattr(rec, field_name, None)
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    missing += 1
                else:
                    try:
                        values.append(float(v))
                    except (TypeError, ValueError):
                        missing += 1

            numeric_stats[field_name] = {
                "count":   len(values),
                "missing": missing,
                "mean":    round(_mean(values), 4),
                "std":     round(_std(values), 4),
                "min":     round(min(values), 4) if values else float("nan"),
                "q25":     round(_percentile(values, 25), 4),
                "median":  round(_percentile(values, 50), 4),
                "q75":     round(_percentile(values, 75), 4),
                "max":     round(max(values), 4) if values else float("nan"),
            }
        stats["numeric"] = numeric_stats

        # ── Boolean stats ──────────────────────────────────────────────
        bool_stats: Dict[str, Dict[str, Any]] = {}
        for field_name in _BOOL_FIELDS:
            true_count = sum(1 for rec in records if bool(getattr(rec, field_name, False)))
            bool_stats[field_name] = {
                "true_count":  true_count,
                "false_count": n - true_count,
                "true_pct":    round(true_count / n * 100, 2),
            }
        stats["boolean"] = bool_stats

        # ── Categorical stats ──────────────────────────────────────────
        cat_stats: Dict[str, Dict[str, Any]] = {}
        for field_name in _CAT_FIELDS:
            counts = Counter(str(getattr(rec, field_name, "unknown")) for rec in records)
            cat_stats[field_name] = {
                k: {"count": v, "pct": round(v / n * 100, 2)}
                for k, v in counts.most_common()
            }
        stats["categorical"] = cat_stats

        # ── Risk class balance ──────────────────────────────────────────
        risk_counts = Counter(str(getattr(rec, "risk_level", "low")) for rec in records)
        total = sum(risk_counts.values())
        stats["class_balance"] = {
            k: {"count": v, "pct": round(v / total * 100, 2)}
            for k, v in risk_counts.most_common()
        }
        # Imbalance ratio (max / min frequency)
        freqs = list(risk_counts.values())
        stats["imbalance_ratio"] = round(max(freqs) / min(freqs), 2) if min(freqs) > 0 else float("inf")

        # ── Correlations with risk score proxy (fatigue_score) ─────────
        risk_numeric = [
            0.0 if getattr(rec, "risk_level", "low") == RiskLevel.LOW.value
            else 0.5 if getattr(rec, "risk_level", "low") == RiskLevel.MEDIUM.value
            else 1.0
            for rec in records
        ]
        correlations: Dict[str, float] = {}
        for field_name in ["fatigue_score", "distraction_score", "speed", "eye_ratio", "lane_offset"]:
            field_vals = [float(getattr(rec, field_name, 0.0)) for rec in records]
            correlations[field_name] = round(_corr(field_vals, risk_numeric), 4)
        stats["correlations_with_risk"] = correlations

        # ── Missing value summary ──────────────────────────────────────
        missing_summary: Dict[str, int] = {}
        all_fields = _NUMERIC_FIELDS + _BOOL_FIELDS + _CAT_FIELDS
        for field_name in all_fields:
            missing_count = sum(
                1 for rec in records
                if getattr(rec, field_name, None) is None
            )
            if missing_count > 0:
                missing_summary[field_name] = missing_count
        stats["missing_values"] = missing_summary

        return stats

    def report(self, stats: Dict[str, Any], verbose: bool = True) -> str:
        """Format stats dict into a human-readable text report."""
        lines = [
            "=" * 60,
            "  FleetGuardian AI – Telemetry Dataset Statistics",
            "=" * 60,
            f"  Total Records  : {stats.get('total_records', 0)}",
            f"  Imbalance Ratio: {stats.get('imbalance_ratio', 'N/A')}",
            "",
            "── Risk Level Distribution ──────────────────────────────",
        ]
        for lvl, info in stats.get("class_balance", {}).items():
            lines.append(f"  {lvl:<10}: {info['count']:>6} ({info['pct']:.1f}%)")

        if verbose:
            lines += ["", "── Numeric Field Summary ────────────────────────────────"]
            for fname, s in stats.get("numeric", {}).items():
                lines.append(
                    f"  {fname:<26}: mean={s['mean']:.3f}  std={s['std']:.3f}  "
                    f"[{s['min']:.2f}, {s['max']:.2f}]  missing={s['missing']}"
                )

            lines += ["", "── Boolean Field Summary ─────────────────────────────────"]
            for fname, s in stats.get("boolean", {}).items():
                lines.append(f"  {fname:<20}: True={s['true_count']} ({s['true_pct']}%)")

            lines += ["", "── Correlations with Risk Level ─────────────────────────"]
            for fname, corr in stats.get("correlations_with_risk", {}).items():
                direction = "↑" if corr > 0 else ("↓" if corr < 0 else "→")
                lines.append(f"  {fname:<26}: r={corr:+.4f} {direction}")

        if stats.get("missing_values"):
            lines += ["", "── Missing Values ────────────────────────────────────────"]
            for fname, cnt in stats["missing_values"].items():
                lines.append(f"  {fname:<26}: {cnt} missing")

        lines.append("=" * 60)
        report_text = "\n".join(lines)

        if verbose:
            logger.info("\n" + report_text)

        return report_text

    def from_csv(self, csv_path: str) -> Dict[str, Any]:
        """
        Load a CSV and compute statistics directly without TelemetryRecord objects.
        Useful for post-hoc analysis of exported files.
        """
        if not os.path.exists(csv_path):
            logger.error(f"CSV not found: {csv_path}")
            return {}

        records: List[TelemetryRecord] = []
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rec = TelemetryRecord(
                    driver_id=row.get("driver_id", ""),
                    vehicle_id=row.get("vehicle_id", ""),
                    trip_id=row.get("trip_id", ""),
                    speed=float(row.get("speed", 0)),
                    eye_ratio=float(row.get("eye_ratio", 1.0)),
                    mouth_ratio=float(row.get("mouth_ratio", 0.0)),
                    blink_rate=float(row.get("blink_rate", 0.0)),
                    eye_closed_seconds=float(row.get("eye_closed_seconds", 0.0)),
                    yawning_count=int(float(row.get("yawning_count", 0))),
                    fatigue_score=float(row.get("fatigue_score", 0.0)),
                    head_direction=row.get("head_direction", "Forward"),
                    distraction_score=float(row.get("distraction_score", 0.0)),
                    phone_detected=bool(int(row.get("phone_detected", 0))),
                    phone_usage_duration=float(row.get("phone_usage_duration", 0.0)),
                    seatbelt_status=bool(int(row.get("seatbelt_status", 0))),
                    lane_offset=float(row.get("lane_offset", 0.0)),
                    lane_departure_count=int(float(row.get("lane_departure_count", 0))),
                    weather=row.get("weather", "unknown"),
                    time_of_day=row.get("time_of_day", "night"),
                    trip_duration=float(row.get("trip_duration", 0.0)),
                    alert_count=int(float(row.get("alert_count", 0))),
                    risk_level=row.get("risk_level", "low"),
                )
                records.append(rec)
        return self.compute(records)
