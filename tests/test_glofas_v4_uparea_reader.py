# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.glofas_v4_uparea_reader import (
    DRESDEN_STATION_LATITUDE_WGS84,
    DRESDEN_STATION_LONGITUDE_WGS84,
    EXPECTED_CANDIDATE_COUNT,
    OFFICIAL_FILL_VALUE,
    GlofasUpareaError,
    canonical_extraction_bytes,
    extraction_sha256,
    read_dresden_glofas_v4_uparea,
)
from scripts.hydrology_grid_matching import (
    DRESDEN_DRAINAGE_AREA_KM2,
    GLOFAS_V4_LATITUDE_COUNT,
    GLOFAS_V4_LONGITUDE_COUNT,
    GLOFAS_V4_MAX_LATITUDE_CENTER,
    GLOFAS_V4_MIN_LONGITUDE_CENTER,
    GLOFAS_V4_GRID_RESOLUTION_DEGREES,
    glofas_v4_candidate_grid_points,
    select_dresden_glofas_grid_cell,
)

NETCDF4_AVAILABLE = importlib.util.find_spec("netCDF4") is not None

if NETCDF4_AVAILABLE:
    import netCDF4


@unittest.skipUnless(NETCDF4_AVAILABLE, "requires requirements-glofas-acquisition.txt")
class GlofasV4UpareaReaderTests(unittest.TestCase):
    def _write_synthetic_ancillary(
        self,
        path: Path,
        *,
        latitude_count: int = GLOFAS_V4_LATITUDE_COUNT,
        unit: str = "m2",
        coordinate_drift_index: int | None = None,
        missing_candidate_index: int | None = None,
        nonpositive_candidate_index: int | None = None,
        data_model: str = "NETCDF4",
    ) -> tuple:
        points = glofas_v4_candidate_grid_points(
            station_latitude=DRESDEN_STATION_LATITUDE_WGS84,
            station_longitude=DRESDEN_STATION_LONGITUDE_WGS84,
        )
        with netCDF4.Dataset(path, mode="w", format=data_model) as dataset:
            dataset.createDimension("latitude", latitude_count)
            dataset.createDimension("longitude", GLOFAS_V4_LONGITUDE_COUNT)

            latitude = dataset.createVariable("latitude", "f8", ("latitude",))
            latitude.standard_name = "latitude"
            latitude.long_name = "latitude"
            latitude.units = "degrees_north"
            latitude.axis = "Y"
            latitude[:] = [
                GLOFAS_V4_MAX_LATITUDE_CENTER - GLOFAS_V4_GRID_RESOLUTION_DEGREES * index
                for index in range(latitude_count)
            ]
            if coordinate_drift_index is not None and coordinate_drift_index < latitude_count:
                latitude[coordinate_drift_index] = float(latitude[coordinate_drift_index]) + 0.001

            longitude = dataset.createVariable("longitude", "f8", ("longitude",))
            longitude.standard_name = "longitude"
            longitude.long_name = "longitude"
            longitude.units = "degrees_east"
            longitude.axis = "X"
            longitude[:] = [
                GLOFAS_V4_MIN_LONGITUDE_CENTER + GLOFAS_V4_GRID_RESOLUTION_DEGREES * index
                for index in range(GLOFAS_V4_LONGITUDE_COUNT)
            ]

            uparea = dataset.createVariable(
                "uparea",
                "f4",
                ("latitude", "longitude"),
                fill_value=OFFICIAL_FILL_VALUE,
                chunksizes=(1, GLOFAS_V4_LONGITUDE_COUNT),
            )
            uparea.long_name = "Upstream area of each river pixel"
            uparea.units = unit
            uparea.missing_value = OFFICIAL_FILL_VALUE

            if latitude_count == GLOFAS_V4_LATITUDE_COUNT:
                for index, point in enumerate(points):
                    if index == missing_candidate_index:
                        continue
                    value = 60_000.0 * 1_000_000.0
                    if index == 10:
                        value = DRESDEN_DRAINAGE_AREA_KM2 * 1_000_000.0
                    if index == nonpositive_candidate_index:
                        value = 0.0
                    uparea[point.latitude_index, point.longitude_index] = value
        return points

    def test_reads_only_frozen_candidate_values_and_emits_exact_artifact_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "uparea_glofas_v4_0.nc"
            points = self._write_synthetic_ancillary(path)
            payload = path.read_bytes()
            result = read_dresden_glofas_v4_uparea(
                path,
                storage_reference="external://glofas-v4/uparea_glofas_v4_0.nc",
            )

        evidence = result.evidence
        self.assertEqual(evidence["profile_version"], "1.0.0")
        self.assertEqual(evidence["candidate_count"], EXPECTED_CANDIDATE_COUNT)
        self.assertEqual(evidence["defined_candidate_count"], EXPECTED_CANDIDATE_COUNT)
        self.assertEqual(len(result.grid_cells), EXPECTED_CANDIDATE_COUNT)
        self.assertEqual(evidence["artifact"]["byte_size"], len(payload))
        self.assertEqual(evidence["artifact"]["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(evidence["software"]["netcdf4_python"], netCDF4.__version__)
        self.assertEqual(
            [(row["latitude_index"], row["longitude_index"]) for row in evidence["candidates"]],
            [(point.latitude_index, point.longitude_index) for point in points],
        )

    def test_extracted_cells_feed_existing_selector_without_new_selection_logic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "uparea_glofas_v4_0.nc"
            points = self._write_synthetic_ancillary(path)
            result = read_dresden_glofas_v4_uparea(
                path,
                storage_reference="external://glofas-v4/selector.nc",
            )
        selected = select_dresden_glofas_grid_cell(
            station_latitude=DRESDEN_STATION_LATITUDE_WGS84,
            station_longitude=DRESDEN_STATION_LONGITUDE_WGS84,
            candidates=result.grid_cells,
        )
        self.assertEqual(selected.cell.latitude, points[10].latitude)
        self.assertEqual(selected.cell.longitude, points[10].longitude)
        self.assertLess(selected.relative_drainage_area_mismatch, 1e-6)

    def test_fill_value_is_explicitly_recorded_as_missing_and_not_passed_to_selector(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "uparea_glofas_v4_0.nc"
            points = self._write_synthetic_ancillary(path, missing_candidate_index=0)
            result = read_dresden_glofas_v4_uparea(
                path,
                storage_reference="external://glofas-v4/missing.nc",
            )
        self.assertEqual(result.evidence["candidate_count"], EXPECTED_CANDIDATE_COUNT)
        self.assertEqual(result.evidence["defined_candidate_count"], EXPECTED_CANDIDATE_COUNT - 1)
        first = result.evidence["candidates"][0]
        self.assertEqual((first["latitude_index"], first["longitude_index"]), (
            points[0].latitude_index,
            points[0].longitude_index,
        ))
        self.assertEqual(first["status"], "missing")
        self.assertIsNone(first["upstream_area_m2"])
        self.assertIsNone(first["upstream_area_km2"])
        self.assertEqual(len(result.grid_cells), EXPECTED_CANDIDATE_COUNT - 1)

    def test_wrong_unit_dimension_or_coordinate_grid_fails_closed(self) -> None:
        cases = (
            {"unit": "km2"},
            {"latitude_count": GLOFAS_V4_LATITUDE_COUNT - 1},
            {"coordinate_drift_index": 778},
        )
        for index, kwargs in enumerate(cases):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / f"invalid-{index}.nc"
                self._write_synthetic_ancillary(path, **kwargs)
                with self.assertRaises(GlofasUpareaError):
                    read_dresden_glofas_v4_uparea(
                        path,
                        storage_reference=f"external://glofas-v4/invalid-{index}.nc",
                    )

    def test_classic_netcdf_is_rejected_even_when_reader_can_open_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "classic.nc"
            self._write_synthetic_ancillary(path, data_model="NETCDF3_CLASSIC")
            with self.assertRaisesRegex(GlofasUpareaError, "must be NetCDF4"):
                read_dresden_glofas_v4_uparea(
                    path,
                    storage_reference="external://glofas-v4/classic.nc",
                )

    def test_defined_nonpositive_uparea_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "zero.nc"
            self._write_synthetic_ancillary(path, nonpositive_candidate_index=0)
            with self.assertRaisesRegex(GlofasUpareaError, "finite and positive"):
                read_dresden_glofas_v4_uparea(
                    path,
                    storage_reference="external://glofas-v4/zero.nc",
                )

    def test_symlink_and_preopen_identity_change_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "uparea.nc"
            self._write_synthetic_ancillary(path)
            link = root / "link.nc"
            try:
                os.symlink(path, link)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable in this environment")
            with self.assertRaisesRegex(GlofasUpareaError, "non-symlink"):
                read_dresden_glofas_v4_uparea(
                    link,
                    storage_reference="external://glofas-v4/link.nc",
                )

            actual = path.stat()
            replaced = SimpleNamespace(
                st_dev=actual.st_dev,
                st_ino=actual.st_ino + 1,
                st_size=actual.st_size,
                st_mtime_ns=actual.st_mtime_ns,
                st_mode=actual.st_mode,
            )
            with patch("scripts.glofas_v4_uparea_reader.os.fstat", return_value=replaced):
                with self.assertRaisesRegex(GlofasUpareaError, "opened safely"):
                    read_dresden_glofas_v4_uparea(
                        path,
                        storage_reference="external://glofas-v4/replaced.nc",
                    )

    def test_canonical_evidence_identity_is_deterministic_and_strict_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "uparea.nc"
            self._write_synthetic_ancillary(path)
            first = read_dresden_glofas_v4_uparea(
                path,
                storage_reference="external://glofas-v4/deterministic.nc",
            ).evidence
            second = read_dresden_glofas_v4_uparea(
                path,
                storage_reference="external://glofas-v4/deterministic.nc",
            ).evidence
        self.assertEqual(canonical_extraction_bytes(first), canonical_extraction_bytes(second))
        self.assertEqual(extraction_sha256(first), extraction_sha256(second))
        json.loads(canonical_extraction_bytes(first).decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
