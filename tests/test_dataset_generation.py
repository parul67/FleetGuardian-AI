"""
tests/test_dataset_generation.py
----------------------------------
Unit tests for the Dataset Generation module.
Covers: schema, collector, validator, exporter, statistics, pipeline.
No camera / CV models required – uses mock DriverState objects.
"""
import csv
import math
import os
import tempfile
import time
import uuid
import pytest


# ─────────────────────────────────────────────────────────────
# Helpers / fixtures
# ─────────────────────────────────────────────────────────────

def _mock_state(
    eye_ratio=0.35, mouth_ratio=0.1, blink_count=5, yawn_count=0,
    head_nod_count=0, eye_closed_seconds=0.0, fatigue_score=0.1,
    head_direction="Forward", attention_score=0.95,
    phone_detected=False, phone_usage_duration=0.0, phone_usage_active=False,
    seatbelt_detected=True, lane_departure=False, lane_offset_px=10.0,
    overall_risk_score=0.05, active_alerts=None, highest_alert_level="safe",
):
    """Returns a simple namespace that mimics DriverState."""
    class _State:
        pass
    s = _State()
    s.eye_ratio = eye_ratio
    s.mouth_ratio = mouth_ratio
    s.blink_count = blink_count
    s.yawn_count = yawn_count
    s.head_nod_count = head_nod_count
    s.eye_closed_seconds = eye_closed_seconds
    s.fatigue_score = fatigue_score
    s.head_direction = head_direction
    s.attention_score = attention_score
    s.phone_detected = phone_detected
    s.phone_usage_duration = phone_usage_duration
    s.phone_usage_active = phone_usage_active
    s.seatbelt_detected = seatbelt_detected
    s.lane_departure = lane_departure
    s.lane_offset_px = lane_offset_px
    s.overall_risk_score = overall_risk_score
    s.active_alerts = active_alerts or []
    s.highest_alert_level = highest_alert_level
    return s


def _make_record(**kwargs):
    from datasets.telemetry.schema import TelemetryRecord
    defaults = dict(
        driver_id="D01", vehicle_id="V01", trip_id="T01",
        speed=60.0, eye_ratio=0.35, mouth_ratio=0.1,
        blink_rate=15.0, eye_closed_seconds=0.0, yawning_count=0,
        fatigue_score=0.1, head_direction="Forward", distraction_score=0.05,
        phone_detected=False, phone_usage_duration=0.0, seatbelt_status=True,
        lane_offset=5.0, lane_departure_count=0, weather="clear",
        time_of_day="morning", trip_duration=120.0, alert_count=0,
        risk_level="low",
    )
    defaults.update(kwargs)
    return TelemetryRecord(**defaults)


# ─────────────────────────────────────────────────────────────
# Schema Tests
# ─────────────────────────────────────────────────────────────

class TestSchema:
    def test_risk_level_from_score_low(self):
        from datasets.telemetry.schema import RiskLevel
        assert RiskLevel.from_score(0.1) == RiskLevel.LOW

    def test_risk_level_from_score_medium(self):
        from datasets.telemetry.schema import RiskLevel
        assert RiskLevel.from_score(0.5) == RiskLevel.MEDIUM

    def test_risk_level_from_score_high(self):
        from datasets.telemetry.schema import RiskLevel
        assert RiskLevel.from_score(0.9) == RiskLevel.HIGH

    def test_time_of_day_morning(self):
        from datasets.telemetry.schema import TimeOfDay
        assert TimeOfDay.from_hour(8) == TimeOfDay.MORNING

    def test_time_of_day_night(self):
        from datasets.telemetry.schema import TimeOfDay
        assert TimeOfDay.from_hour(23) == TimeOfDay.NIGHT

    def test_telemetry_record_to_dict_has_all_columns(self):
        from datasets.telemetry.schema import TelemetryRecord
        rec = TelemetryRecord()
        d = rec.to_dict()
        for col in TelemetryRecord.csv_columns():
            assert col in d, f"Missing column: {col}"

    def test_record_id_is_unique(self):
        from datasets.telemetry.schema import TelemetryRecord
        ids = {TelemetryRecord().record_id for _ in range(50)}
        assert len(ids) == 50


# ─────────────────────────────────────────────────────────────
# Collector Tests
# ─────────────────────────────────────────────────────────────

class TestCollector:
    def _make(self):
        from datasets.telemetry.collector import TelemetryCollector
        return TelemetryCollector(driver_id="D01", vehicle_id="V01", trip_id="T01")

    def test_collect_returns_telemetry_record(self):
        from datasets.telemetry.schema import TelemetryRecord
        col = self._make()
        col.start_trip()
        rec = col.collect(_mock_state(), speed=80.0, weather="clear")
        assert isinstance(rec, TelemetryRecord)

    def test_collect_speed_stored(self):
        col = self._make()
        col.start_trip()
        rec = col.collect(_mock_state(), speed=120.5)
        assert rec.speed == pytest.approx(120.5)

    def test_collect_driver_id_matches(self):
        col = self._make()
        col.start_trip()
        rec = col.collect(_mock_state())
        assert rec.driver_id == "D01"

    def test_lane_departure_count_increments_on_rising_edge(self):
        col = self._make()
        col.start_trip()
        col.collect(_mock_state(lane_departure=False))
        col.collect(_mock_state(lane_departure=True))   # rising edge → count=1
        col.collect(_mock_state(lane_departure=True))   # still true  → no increment
        rec = col.collect(_mock_state(lane_departure=True))
        assert rec.lane_departure_count == 1

    def test_alert_count_accumulates(self):
        col = self._make()
        col.start_trip()
        col.collect(_mock_state(active_alerts=["alert1", "alert2"]))
        rec = col.collect(_mock_state(active_alerts=["alert3"]))
        assert rec.alert_count == 3

    def test_risk_level_high_for_high_score(self):
        col = self._make()
        col.start_trip()
        rec = col.collect(_mock_state(overall_risk_score=0.9))
        assert rec.risk_level == "high"

    def test_blink_rate_non_negative(self):
        col = self._make()
        col.start_trip()
        rec = col.collect(_mock_state(blink_count=10))
        assert rec.blink_rate >= 0.0


# ─────────────────────────────────────────────────────────────
# Validator Tests
# ─────────────────────────────────────────────────────────────

class TestValidator:
    def _make(self):
        from datasets.telemetry.validator import DataValidator
        return DataValidator()

    def test_valid_record_passes(self):
        v = self._make()
        result = v.validate_record(_make_record())
        assert result.is_valid
        assert result.errors == []

    def test_missing_driver_id_is_error(self):
        v = self._make()
        result = v.validate_record(_make_record(driver_id=""))
        assert not result.is_valid
        assert any("driver_id" in e for e in result.errors)

    def test_out_of_range_eye_ratio_is_error(self):
        v = self._make()
        result = v.validate_record(_make_record(eye_ratio=2.5))
        assert not result.is_valid
        assert any("eye_ratio" in e for e in result.errors)

    def test_invalid_head_direction_is_error(self):
        v = self._make()
        result = v.validate_record(_make_record(head_direction="Sideways"))
        assert not result.is_valid

    def test_invalid_risk_level_is_error(self):
        v = self._make()
        result = v.validate_record(_make_record(risk_level="extreme"))
        assert not result.is_valid

    def test_repair_fills_nan(self):
        import math
        v = self._make()
        rec = _make_record(eye_ratio=float("nan"))
        repaired = v.repair_record(rec)
        assert not math.isnan(repaired.eye_ratio)
        assert repaired.eye_ratio == pytest.approx(1.0)

    def test_repair_clamps_speed(self):
        v = self._make()
        rec = _make_record(speed=999.0)
        repaired = v.repair_record(rec)
        assert repaired.speed <= 300.0

    def test_clean_dataset_removes_duplicates(self):
        v = self._make()
        rec = _make_record()
        # Same record duplicated 3x – same timestamp bucket
        records = [_make_record() for _ in range(3)]
        for r in records:
            r.driver_id = "D01"
            r.vehicle_id = "V01"
            r.trip_id = "T01"
            r.timestamp = 1000.0  # same second → duplicates

        clean, stats = v.clean_dataset(records, drop_invalid=True, remove_duplicates=True)
        assert len(clean) == 1
        assert stats["dropped_duplicate"] == 2

    def test_clean_dataset_drops_invalid(self):
        v = self._make()
        good = _make_record()
        bad = _make_record(driver_id="", eye_ratio=99.0)
        clean, stats = v.clean_dataset([good, bad], drop_invalid=True)
        assert len(clean) == 1
        assert stats["dropped_invalid"] == 1

    def test_negative_yawning_count_is_error(self):
        v = self._make()
        result = v.validate_record(_make_record(yawning_count=-1))
        assert not result.is_valid


# ─────────────────────────────────────────────────────────────
# Exporter Tests
# ─────────────────────────────────────────────────────────────

class TestExporter:
    def test_export_creates_csv_with_header(self):
        from datasets.telemetry.exporter import CSVExporter
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.csv")
            exp = CSVExporter(path)
            exp.export([_make_record(), _make_record()])
            assert os.path.exists(path)
            with open(path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            assert len(rows) == 2
            assert "driver_id" in reader.fieldnames
            assert "risk_level" in reader.fieldnames

    def test_export_has_all_22_columns(self):
        from datasets.telemetry.exporter import CSVExporter
        from datasets.telemetry.schema import TelemetryRecord
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.csv")
            exp = CSVExporter(path)
            exp.export([_make_record()])
            with open(path) as f:
                reader = csv.DictReader(f)
                list(reader)  # consume
                assert set(TelemetryRecord.csv_columns()) == set(reader.fieldnames)

    def test_append_does_not_duplicate_header(self):
        from datasets.telemetry.exporter import CSVExporter
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.csv")
            exp = CSVExporter(path)
            exp.export([_make_record()])
            exp.append([_make_record()])
            exp.append([_make_record()])
            count = exp.record_count()
            assert count == 3

    def test_boolean_fields_exported_as_int(self):
        from datasets.telemetry.exporter import CSVExporter
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.csv")
            exp = CSVExporter(path)
            exp.export([_make_record(phone_detected=True, seatbelt_status=False)])
            with open(path) as f:
                reader = csv.DictReader(f)
                row = next(reader)
            assert row["phone_detected"] in ("0", "1")
            assert row["seatbelt_status"] in ("0", "1")

    def test_record_count_returns_correct_number(self):
        from datasets.telemetry.exporter import CSVExporter
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.csv")
            exp = CSVExporter(path)
            assert exp.record_count() == 0
            exp.export([_make_record() for _ in range(7)])
            assert exp.record_count() == 7


# ─────────────────────────────────────────────────────────────
# Statistics Tests
# ─────────────────────────────────────────────────────────────

class TestStatistics:
    def _make_records(self, n=30):
        import random
        from datasets.telemetry.schema import RiskLevel
        risks = [RiskLevel.LOW.value, RiskLevel.MEDIUM.value, RiskLevel.HIGH.value]
        return [
            _make_record(
                fatigue_score=random.uniform(0, 1),
                distraction_score=random.uniform(0, 1),
                speed=random.uniform(0, 120),
                risk_level=random.choice(risks),
            )
            for _ in range(n)
        ]

    def test_compute_returns_total_records(self):
        from datasets.telemetry.statistics import DatasetStatistics
        stats = DatasetStatistics()
        records = self._make_records(20)
        result = stats.compute(records)
        assert result["total_records"] == 20

    def test_compute_has_numeric_section(self):
        from datasets.telemetry.statistics import DatasetStatistics
        stats = DatasetStatistics()
        result = stats.compute(self._make_records(10))
        assert "numeric" in result
        assert "fatigue_score" in result["numeric"]

    def test_compute_has_class_balance(self):
        from datasets.telemetry.statistics import DatasetStatistics
        stats = DatasetStatistics()
        result = stats.compute(self._make_records(15))
        assert "class_balance" in result

    def test_compute_correlations_present(self):
        from datasets.telemetry.statistics import DatasetStatistics
        stats = DatasetStatistics()
        result = stats.compute(self._make_records(20))
        assert "correlations_with_risk" in result
        assert "fatigue_score" in result["correlations_with_risk"]

    def test_report_returns_string(self):
        from datasets.telemetry.statistics import DatasetStatistics
        stats = DatasetStatistics()
        result = stats.compute(self._make_records(10))
        report = stats.report(result, verbose=False)
        assert isinstance(report, str)
        assert "Risk Level" in report

    def test_from_csv_matches_compute(self):
        from datasets.telemetry.statistics import DatasetStatistics
        from datasets.telemetry.exporter import CSVExporter
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.csv")
            records = self._make_records(15)
            CSVExporter(path).export(records)
            stats = DatasetStatistics()
            from_csv = stats.from_csv(path)
            direct = stats.compute(records)
            assert from_csv["total_records"] == direct["total_records"]

    def test_empty_records_returns_empty(self):
        from datasets.telemetry.statistics import DatasetStatistics
        stats = DatasetStatistics()
        result = stats.compute([])
        assert result == {}


# ─────────────────────────────────────────────────────────────
# Pipeline Integration Tests
# ─────────────────────────────────────────────────────────────

class TestDatasetPipeline:
    def _make(self, tmpdir):
        from datasets.telemetry.pipeline import DatasetPipeline
        return DatasetPipeline(
            output_dir=tmpdir,
            csv_filename="test_fleet.csv",
            auto_export_every=100,
            drop_invalid=True,
        )

    def test_ingest_without_trip_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = self._make(tmpdir)
            result = pipeline.ingest(_mock_state())
            assert result is None

    def test_ingest_with_trip_returns_record(self):
        from datasets.telemetry.schema import TelemetryRecord
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = self._make(tmpdir)
            pipeline.start_trip("D01", "V01", "T01")
            result = pipeline.ingest(_mock_state(), speed=60.0)
            assert isinstance(result, TelemetryRecord)

    def test_end_trip_flushes_to_csv(self):
        from datasets.telemetry.exporter import CSVExporter
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = self._make(tmpdir)
            pipeline.start_trip("D01", "V01", "T01")
            for _ in range(5):
                pipeline.ingest(_mock_state())
            pipeline.end_trip()

            csv_path = os.path.join(tmpdir, "test_fleet.csv")
            assert os.path.exists(csv_path)
            exp = CSVExporter(csv_path)
            assert exp.record_count() == 5

    def test_buffer_size_increments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = self._make(tmpdir)
            pipeline.start_trip("D01", "V01", "T01")
            for _ in range(3):
                pipeline.ingest(_mock_state())
            assert pipeline.buffer_size == 3

    def test_export_clears_buffer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = self._make(tmpdir)
            pipeline.start_trip("D01", "V01", "T01")
            for _ in range(5):
                pipeline.ingest(_mock_state())
            pipeline.export()
            assert pipeline.buffer_size == 0

    def test_get_statistics_returns_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = self._make(tmpdir)
            pipeline.start_trip("D01", "V01", "T01")
            for _ in range(10):
                pipeline.ingest(_mock_state())
            stats = pipeline.get_statistics()
            assert isinstance(stats, dict)
            assert stats.get("total_records", 0) == 10

    def test_multiple_trips_accumulate_in_csv(self):
        from datasets.telemetry.exporter import CSVExporter
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = self._make(tmpdir)
            for i in range(3):
                pipeline.start_trip(f"D0{i}", "V01", f"T0{i}")
                for _ in range(4):
                    pipeline.ingest(_mock_state())
                pipeline.end_trip()

            exp = CSVExporter(os.path.join(tmpdir, "test_fleet.csv"))
            assert exp.record_count() == 12
