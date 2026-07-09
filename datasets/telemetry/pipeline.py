import os
import time
import yaml
from typing import List, Optional, Dict, Any

from utils.logger import logger

from .schema import TelemetryRecord, WeatherCondition
from .collector import TelemetryCollector
from .validator import DataValidator
from .exporter import CSVExporter
from .statistics import DatasetStatistics


def _load_dataset_cfg() -> Dict[str, Any]:
    """Load dataset_config.yaml relative to project root, return dataset section."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg_path = os.path.join(root, "configs", "dataset_config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r") as f:
            raw = yaml.safe_load(f) or {}
        return raw.get("dataset", {})
    return {}




class DatasetPipeline:
    """
    End-to-end dataset generation pipeline.

    Thread-safety note: This class is NOT thread-safe. Use one instance per thread.
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        csv_filename: Optional[str] = None,
        auto_export_every: int = 500,
        drop_invalid: bool = True,
    ) -> None:
        cfg = _load_dataset_cfg()

        self._output_dir = output_dir or cfg.get("output_dir", "datasets/telemetry")
        _csv_filename = csv_filename or cfg.get("csv_filename", "fleet_telemetry.csv")
        self._csv_path = os.path.join(self._output_dir, _csv_filename)
        self._auto_export_every = auto_export_every or int(cfg.get("auto_export_every", 500))
        self._drop_invalid = drop_invalid

        os.makedirs(self._output_dir, exist_ok=True)

        self._validator = DataValidator()
        self._exporter = CSVExporter(self._csv_path)
        self._statistics = DatasetStatistics()

        # Current trip collector (set by start_trip)
        self._collector: Optional[TelemetryCollector] = None

        # In-memory buffer (flushed to CSV on auto-export or manual export)
        self._buffer: List[TelemetryRecord] = []
        self._total_records = 0

        logger.info(f"DatasetPipeline initialised. Output: {self._csv_path}")

    # ------------------------------------------------------------------
    # Trip lifecycle
    # ------------------------------------------------------------------

    def start_trip(
        self,
        driver_id: str,
        vehicle_id: str,
        trip_id: str,
        risk_low_thresh: float = 0.35,
        risk_med_thresh: float = 0.65,
    ) -> None:
        """Start collecting data for a new trip."""
        self._collector = TelemetryCollector(
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            trip_id=trip_id,
            risk_low_thresh=risk_low_thresh,
            risk_med_thresh=risk_med_thresh,
        )
        self._collector.start_trip()

    def end_trip(self) -> int:
        """
        End the current trip, flush remaining buffered records to CSV.

        Returns:
            Number of records written in this trip.
        """
        if self._collector:
            self._collector.end_trip()
            self._collector = None

        written = self._flush_buffer()
        logger.info(f"Trip ended. Flushed {written} records to CSV.")
        return written

    # ------------------------------------------------------------------
    # Per-frame ingestion
    # ------------------------------------------------------------------

    def ingest(
        self,
        state: Any,
        speed: float = 0.0,
        weather: str = WeatherCondition.UNKNOWN.value,
    ) -> Optional[TelemetryRecord]:
        """
        Process a single DriverState snapshot into a validated TelemetryRecord.
        Auto-exports when buffer reaches auto_export_every threshold.

        Returns:
            The validated TelemetryRecord, or None if invalid and drop_invalid=True.
        """
        if self._collector is None:
            logger.warning("ingest() called without an active trip. Call start_trip() first.")
            return None

        record = self._collector.collect(state, speed=speed, weather=weather)
        record = self._validator.repair_record(record)

        result = self._validator.validate_record(record)
        if not result.is_valid and self._drop_invalid:
            logger.debug(f"Dropped invalid record: {result.errors}")
            return None

        self._buffer.append(record)
        self._total_records += 1

        # Auto-export
        if len(self._buffer) >= self._auto_export_every:
            self._flush_buffer()

        return record

    # ------------------------------------------------------------------
    # Manual export & stats
    # ------------------------------------------------------------------

    def export(self, clean: bool = True) -> str:
        """
        Validate, clean, and export all buffered records to CSV.

        Args:
            clean: If True, run full deduplication on the buffer before export.

        Returns:
            Path to the written CSV file.
        """
        records = self._buffer
        if clean:
            records, stats = self._validator.clean_dataset(
                records,
                drop_invalid=self._drop_invalid,
                remove_duplicates=True,
            )
            logger.info(f"Clean stats: {stats}")

        path = self._exporter.append(records)
        self._buffer = []
        return path

    def get_statistics(self) -> Dict[str, Any]:
        """Compute stats on all records currently in the buffer."""
        if not self._buffer:
            # Try loading from CSV
            return self._statistics.from_csv(self._csv_path)
        return self._statistics.compute(self._buffer)

    def print_stats(self, verbose: bool = True) -> None:
        """Compute and print a formatted statistics report."""
        stats = self.get_statistics()
        report = self._statistics.report(stats, verbose=verbose)
        print(report)

    @property
    def buffer_size(self) -> int:
        return len(self._buffer)

    @property
    def total_records_ingested(self) -> int:
        return self._total_records

    @property
    def csv_path(self) -> str:
        return self._csv_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _flush_buffer(self) -> int:
        """Append buffer to CSV and clear it. Returns count written."""
        if not self._buffer:
            return 0
        count = len(self._buffer)
        self._exporter.append(self._buffer)
        self._buffer = []
        logger.debug(f"Flushed {count} records to CSV.")
        return count
