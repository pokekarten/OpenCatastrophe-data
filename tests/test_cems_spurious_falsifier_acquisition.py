# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

DEPS_AVAILABLE = all(
    importlib.util.find_spec(name) is not None
    for name in ("numpy", "pyproj", "rasterio")
)

if DEPS_AVAILABLE:
    import numpy as np
    from rasterio.io import MemoryFile
    from rasterio.transform import from_origin

    from scripts import acquire_cems_spurious_falsifier_diagnostics as worker


class _Socket:
    def settimeout(self, _timeout: float) -> None:
        pass


class _Response:
    def __init__(self, url: str, payload: bytes):
        self.status = 200
        self._url = url
        self._payload = payload
        self._offset = 0
        self._oc_response_socket = _Socket()
        self.headers = {
            "Content-Type": "image/tiff",
            "Content-Length": str(len(payload)),
        }

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


@unittest.skipUnless(
    DEPS_AVAILABLE,
    "requires requirements-cems-mask-support-challenge.txt",
)
class CemsSpuriousFalsifierDiagnosticAcquisitionTests(unittest.TestCase):
    def _geotiff(self, data, *, dtype: str) -> bytes:
        transform = from_origin(10.0, 50.0, 0.01, 0.01)
        with MemoryFile() as memory:
            with memory.open(
                driver="GTiff",
                width=data.shape[1],
                height=data.shape[0],
                count=1,
                dtype=dtype,
                crs="EPSG:4326",
                transform=transform,
                nodata=-9999.0,
            ) as dataset:
                dataset.write(data.astype(dtype), 1)
            return memory.read()

    def _blank(self):
        return np.full((8, 8), np.nan, dtype="float64")

    def _bounded_derivation(self):
        distance = worker.EXPECTED_DISTANCE_THRESHOLD_METRES + 100.0
        component = {
            "component_count": 1,
            "min_size": 1,
            "median_size": 1.0,
            "max_size": 1,
            "largest_10_sizes": [1],
        }
        diagnostic = {
            "schema_version": worker._diagnostic.SCHEMA_VERSION,
            "source_issue": worker.SOURCE_ISSUE,
            "stage_d_source_issue": 823,
            "stage_d_verdict": worker._diagnostic.STAGE_D_VERDICT,
            "stage_d_disposition": worker._diagnostic.STAGE_D_DISPOSITION,
            "falsifier_count": worker.EXPECTED_FALSIFIER_CELLS,
            "distance_threshold_metres": worker.EXPECTED_DISTANCE_THRESHOLD_METRES,
            "falsifier_digest_sha256": "a" * 64,
            "falsifier_digest_encoding": (
                "big_endian_struct_>qqd_row_col_nearest_distance_metres"
            ),
            "raster_cell_bbox": {
                "min_row": 1,
                "max_row": 1,
                "min_column": 1,
                "max_column": 1,
            },
            "cell_centre_bounds": {
                "min_longitude": 10.0,
                "max_longitude": 10.0,
                "min_latitude": 50.0,
                "max_latitude": 50.0,
            },
            "nearest_distance_summary_metres": {
                "minimum": distance,
                "q25_nearest_rank": distance,
                "median_nearest_rank": distance,
                "q75_nearest_rank": distance,
                "q95_nearest_rank": distance,
                "q99_nearest_rank": distance,
                "maximum": distance,
            },
            "first_16_falsifiers": [
                {
                    "row": 1,
                    "column": 1,
                    "longitude": 10.0,
                    "latitude": 50.0,
                    "nearest_distance_metres": distance,
                }
            ],
            "components_4_neighbour": dict(component),
            "components_8_neighbour": dict(component),
            "edge_envelope_falsifier_cells": 0,
            "interior_falsifier_cells": worker.EXPECTED_FALSIFIER_CELLS,
            "max_row_offset": worker.EXPECTED_MAX_ROW_OFFSET,
            "max_col_offset": worker.EXPECTED_MAX_COL_OFFSET,
            "diagnostic_only": True,
            "small_channel_filter_reconstructed": False,
            "mask_value_semantics_verified": False,
            "per_cell_scientific_correctness_verified": False,
            "benchmark_use_authorized": False,
            "model_use_authorized": False,
            "publication_authorized": False,
            "external_bytes_persisted": False,
        }
        return {
            "schema_version": worker._derive.SCHEMA_VERSION,
            "source_issue": worker.SOURCE_ISSUE,
            "stage_d_source_issue": 823,
            "candidate_support_cells": worker.EXPECTED_CANDIDATE_SUPPORT_CELLS,
            "rp10_seed_cells": worker.EXPECTED_RP10_SEED_CELLS,
            "candidate_farther_than_threshold_cells": worker.EXPECTED_FALSIFIER_CELLS,
            "distance_threshold_metres": worker.EXPECTED_DISTANCE_THRESHOLD_METRES,
            "max_row_offset": worker.EXPECTED_MAX_ROW_OFFSET,
            "max_col_offset": worker.EXPECTED_MAX_COL_OFFSET,
            "global_nearest_row_pruning_lower_bound_metres_per_radian": (
                worker.EXPECTED_LOWER_BOUND_METRES_PER_RADIAN
            ),
            "diagnostic": diagnostic,
            "diagnostic_only": True,
            "small_channel_filter_reconstructed": False,
            "mask_value_semantics_verified": False,
            "per_cell_scientific_correctness_verified": False,
            "benchmark_use_authorized": False,
            "model_use_authorized": False,
            "publication_authorized": False,
            "external_bytes_persisted": False,
        }

    def _run(self, *, deriver=None):
        mask = self._blank()
        rp10 = self._blank().astype("float32")
        mask[1, 1] = 1.0
        rp10[1, 1] = 12.0
        mask_bytes = self._geotiff(mask, dtype="float64")
        rp10_bytes = self._geotiff(rp10, dtype="float32")
        mask_sha = hashlib.sha256(mask_bytes).hexdigest()
        rp10_sha = hashlib.sha256(rp10_bytes).hexdigest()

        def rp10_opener(request, _timeout):
            return _Response(request.full_url, rp10_bytes)

        def mask_opener(request, _timeout):
            return _Response(request.full_url, mask_bytes)

        accepted_mask = {
            "filename": worker._stage_d_worker.SPURIOUS_FILENAME,
            "byte_count": len(mask_bytes),
            "sha256": mask_sha,
        }
        patches = (
            mock.patch.object(
                worker._stage_d_worker._rp10_profile,
                "ACCEPTED_BYTE_COUNT",
                len(rp10_bytes),
            ),
            mock.patch.object(
                worker._stage_d_worker._rp10_profile,
                "ACCEPTED_SHA256",
                rp10_sha,
            ),
            mock.patch.dict(
                worker._stage_d_worker._mask_metadata.MASK_RECEIPTS,
                {worker._stage_d_worker.SPURIOUS_KIND: accepted_mask},
                clear=True,
            ),
            mock.patch.object(worker, "EXPECTED_CANDIDATE_SUPPORT_CELLS", 1),
            mock.patch.object(worker, "EXPECTED_RP10_SEED_CELLS", 1),
            mock.patch.object(worker, "EXPECTED_FALSIFIER_CELLS", 1),
        )
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            if deriver is None:
                deriver = lambda *_args, **_kwargs: self._bounded_derivation()
            return worker.acquire_and_diagnose_cems_spurious_falsifiers(
                rp10_opener=rp10_opener,
                mask_opener=mask_opener,
                clock=lambda: "2026-09-11T18:30:00Z",
                deriver=deriver,
            )

    def test_exact_synthetic_bytes_are_bound_to_memoryfiles_before_deriver(self) -> None:
        dataset_names: list[str] = []
        captured_kwargs: dict[str, int] = {}

        def deriver(mask_dataset, rp10_dataset, **kwargs):
            dataset_names.extend((mask_dataset.name, rp10_dataset.name))
            captured_kwargs.update(kwargs)
            return self._bounded_derivation()

        result = self._run(deriver=deriver)

        self.assertEqual(result["receipt_to_reader_binding"], "verified_bytes_memoryfile")
        self.assertEqual(len(dataset_names), 2)
        self.assertTrue(all(name.startswith("/vsimem/") for name in dataset_names))
        self.assertTrue(all(not Path(name).exists() for name in dataset_names))
        self.assertEqual(captured_kwargs["expected_candidate_support_cells"], 1)
        self.assertEqual(captured_kwargs["expected_rp10_seed_cells"], 1)
        self.assertEqual(captured_kwargs["expected_falsifier_cells"], 1)
        self.assertTrue(result["diagnostic_only"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["benchmark_use_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertFalse(result["publication_authorized"])

    def test_receipt_identity_mismatch_blocks_before_deriver(self) -> None:
        mask = self._blank()
        rp10 = self._blank().astype("float32")
        mask[1, 1] = 1.0
        rp10[1, 1] = 12.0
        mask_bytes = self._geotiff(mask, dtype="float64")
        rp10_bytes = self._geotiff(rp10, dtype="float32")
        deriver = mock.Mock()

        def rp10_opener(request, _timeout):
            return _Response(request.full_url, rp10_bytes)

        def mask_opener(request, _timeout):
            return _Response(request.full_url, mask_bytes)

        with mock.patch.object(
            worker._stage_d_worker._rp10_profile,
            "ACCEPTED_BYTE_COUNT",
            len(rp10_bytes),
        ), mock.patch.object(
            worker._stage_d_worker._rp10_profile,
            "ACCEPTED_SHA256",
            "0" * 64,
        ):
            with self.assertRaisesRegex(
                worker.CemsSpuriousFalsifierDiagnosticAcquisitionError,
                "exact receipt acquisition failed",
            ):
                worker.acquire_and_diagnose_cems_spurious_falsifiers(
                    rp10_opener=rp10_opener,
                    mask_opener=mask_opener,
                    deriver=deriver,
                )
        deriver.assert_not_called()

    def test_projection_leak_from_deriver_is_rejected(self) -> None:
        def deriver(*_args, **_kwargs):
            result = self._bounded_derivation()
            result["records"] = [(1, 1, 2223.0)]
            return result

        with self.assertRaisesRegex(
            worker.CemsSpuriousFalsifierDiagnosticAcquisitionError,
            "derivation projection keys drifted",
        ):
            self._run(deriver=deriver)

    def test_projection_leak_from_bounded_diagnostic_is_rejected(self) -> None:
        def deriver(*_args, **_kwargs):
            result = self._bounded_derivation()
            result["diagnostic"]["records"] = [(1, 1, 2223.0)]
            return result

        with self.assertRaisesRegex(
            worker.CemsSpuriousFalsifierDiagnosticAcquisitionError,
            "diagnostic projection keys drifted",
        ):
            self._run(deriver=deriver)

    def test_count_geometry_and_authority_drift_fail_closed(self) -> None:
        mutations = (
            ("candidate_support_cells", 2, "candidate_support_cells"),
            ("max_row_offset", 22, "max_row_offset"),
            ("benchmark_use_authorized", True, "authority ceiling"),
        )
        for field, value, message in mutations:
            with self.subTest(field=field):
                def deriver(*_args, _field=field, _value=value, **_kwargs):
                    result = self._bounded_derivation()
                    result[_field] = _value
                    return result

                with self.assertRaisesRegex(
                    worker.CemsSpuriousFalsifierDiagnosticAcquisitionError,
                    message,
                ):
                    self._run(deriver=deriver)

    def test_invalid_digest_and_nonmonotone_distance_summary_fail_closed(self) -> None:
        def bad_digest(*_args, **_kwargs):
            result = self._bounded_derivation()
            result["diagnostic"]["falsifier_digest_sha256"] = "not-a-digest"
            return result

        with self.assertRaisesRegex(
            worker.CemsSpuriousFalsifierDiagnosticAcquisitionError,
            "digest is invalid",
        ):
            self._run(deriver=bad_digest)

        def bad_summary(*_args, **_kwargs):
            result = self._bounded_derivation()
            summary = result["diagnostic"]["nearest_distance_summary_metres"]
            summary["q25_nearest_rank"] = summary["maximum"] + 1.0
            return result

        with self.assertRaisesRegex(
            worker.CemsSpuriousFalsifierDiagnosticAcquisitionError,
            "ranks are not monotone",
        ):
            self._run(deriver=bad_summary)

    def test_pyproj_version_drift_blocks_before_acquisition(self) -> None:
        deriver = mock.Mock()
        with mock.patch.object(
            worker._stage_d_worker._challenge.pyproj,
            "__version__",
            "3.7.1",
        ):
            with self.assertRaisesRegex(
                worker.CemsSpuriousFalsifierDiagnosticAcquisitionError,
                "pyproj runtime differs",
            ):
                worker.acquire_and_diagnose_cems_spurious_falsifiers(
                    deriver=deriver,
                )
        deriver.assert_not_called()


if __name__ == "__main__":
    unittest.main()
