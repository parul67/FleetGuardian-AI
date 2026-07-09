"""
datasets/telemetry/exporter.py
-------------------------------
CSVExporter – persists TelemetryRecord lists to CSV with atomic writes.

Features:
  - Ordered columns matching the specification
  - Append mode (avoids re-writing existing data)
  - Atomic temp-file swap to prevent partial writes
  - Auto-creates parent directories
"""
from __future__ import annotations

import csv
import os
import shutil
import tempfile
from typing import List, Optional

from utils.logger import logger
from .schema import TelemetryRecord


class CSVExporter:
    """
    Exports TelemetryRecord lists to CSV.

    Usage::

        exporter = CSVExporter("datasets/telemetry/fleet_telemetry.csv")
        exporter.export(records)               # overwrite / create
        exporter.append(new_records)           # append rows only
    """

    # Ordered CSV columns (22 specified columns, no internal fields)
    COLUMNS: List[str] = TelemetryRecord.csv_columns()

    def __init__(self, output_path: str) -> None:
        self.output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export(self, records: List[TelemetryRecord], overwrite: bool = True) -> str:
        """
        Write records to CSV, replacing existing file.

        Args:
            records:   Records to write.
            overwrite: If False and file exists, raises FileExistsError.

        Returns:
            Absolute path of the written CSV.
        """
        if not overwrite and os.path.exists(self.output_path):
            raise FileExistsError(f"CSV already exists: {self.output_path}. Use overwrite=True or append().")

        self._write_atomic(records, mode="w", write_header=True)
        logger.info(f"Exported {len(records)} records → {self.output_path}")
        return self.output_path

    def append(self, records: List[TelemetryRecord]) -> str:
        """
        Append records to an existing CSV (or create it with header if new).

        Returns:
            Absolute path of the CSV.
        """
        write_header = not os.path.exists(self.output_path) or os.path.getsize(self.output_path) == 0
        self._write_atomic(records, mode="a", write_header=write_header)
        logger.info(f"Appended {len(records)} records → {self.output_path}")
        return self.output_path

    def record_count(self) -> int:
        """Returns the number of data rows in the CSV (excluding header)."""
        if not os.path.exists(self.output_path):
            return 0
        with open(self.output_path, "r", newline="", encoding="utf-8") as f:
            return max(0, sum(1 for _ in f) - 1)  # -1 for header

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_atomic(
        self,
        records: List[TelemetryRecord],
        mode: str,
        write_header: bool,
    ) -> None:
        """Writes to a temp file then atomically renames to prevent partial writes."""
        dir_ = os.path.dirname(self.output_path)
        fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")

        try:
            with os.fdopen(fd, "w", newline="", encoding="utf-8") as tmp_f:
                # If appending, copy existing content first
                if mode == "a" and os.path.exists(self.output_path):
                    with open(self.output_path, "r", encoding="utf-8") as existing:
                        shutil.copyfileobj(existing, tmp_f)
                    write_header = False  # header already in existing

                writer = csv.DictWriter(
                    tmp_f,
                    fieldnames=self.COLUMNS,
                    extrasaction="ignore",
                    lineterminator="\n",
                )
                if write_header:
                    writer.writeheader()

                for rec in records:
                    row = rec.to_dict()
                    # Normalise booleans to int (0/1) for ML compatibility
                    row["phone_detected"] = int(row.get("phone_detected", False))
                    row["seatbelt_status"] = int(row.get("seatbelt_status", False))
                    writer.writerow(row)

            # Atomic replace
            shutil.move(tmp_path, self.output_path)
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
