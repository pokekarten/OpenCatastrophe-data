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

    from scripts import acquire_cems_spurious_support_challenge as worker


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
class CemsSpuriousSupportAcquisitionTests(unittest.TestCase):
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

    def _run(self, mask, rp10, *, challenger=None):
        mask_bytes = self._geotiff(mask, dtype="float64")
        rp10_bytes = self._geotiff(rp10, dtype="float32")
        mask_sha = hashlib.sha256(mask_bytes).hexdigest()
        rp10_sha = hashlib.sha256(rp10_bytes).hexdigest()

        def rp10_opener(request, _timeout):
            return _Response(request.full_url, rp10_bytes)

        def mask_opener(request, _timeout):
            return _Response(request.full_url, mask_bytes)

        accepted_mask = {
            "filename": worker.SPURIOUS_FILENAME,
            "byte_count": len(mask_bytes),
            "sha256": mask_sha,
        }
        with (
            mock.patch.object(worker._rp10_profile, "ACCEPTED_BYTE_COUNT", len(rp10_bytes)),
            mock.patch.object(worker._rp10_profile, "ACCEPTED_SHA256", rp10_sha),
            mock.patch.dict(
                worker._mask_metadata.MASK_RECEIPTS,
                {worker.SPURIOUS_KIND: accepted_mask},
                clear=True,
            ),
            mock.patch.object(worker, "EXPECTED_CANDIDATE_SUPPORT_CELLS", 1),
        ):
            return worker.acquire_and_challenge_cems_spurious_support(
                rp10_opener=rp10_opener,
                mask_opener=mask_opener,
                clock=lambda: "2026-09-10T20:00:00Z",
                challenger=challenger or worker._challenge.challenge_spurious_support,
            )

    def _blank(self):
        return np.full((8, 8), np.nan, dtype="float64")

    def test_exact_synthetic_bytes_are_challenged_from_memory_then_removed(self) -> None:
        mask = self._blank()
        rp10 = self._blank().astype("float32")
        mask[3, 3] = 1.0
        rp10[3, 3] = 12.0
        dataset_names: list[str] = []

        def challenge(mask_dataset, rp10_dataset):
            dataset_names.extend((mask_dataset.name, rp10_dataset.name))
            return worker._challenge.challenge_spurious_support(mask_dataset, rp10_dataset)

        result = self._run(mask, rp10, challenger=challenge)

        self.assertEqual(
            result["challenge"]["verdict"],
            "NOT_FALSIFIED_BY_CURRENT_RP10_NECESSARY_CONDITION",
        )
        self.assertEqual(result["receipt_to_reader_binding"], "verified_bytes_memoryfile")
        self.assertEqual(len(dataset_names), 2)
        self.assertTrue(all(name.startswith("/vsimem/") for name in dataset_names))
        self.assertTrue(all(not Path(name).exists() for name in dataset_names))
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["mask_value_semantics_verified"])
        self.assertFalse(result["per_cell_scientific_correctness_verified"])
        self.assertFalse(result["benchmark_use_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertFalse(result["publication_authorized"])

    def test_scientific_necessary_condition_failure_is_valid_evidence(self) -> None:
        mask = self._blank()
        rp10 = self._blank().astype("float32")
        mask[3, 0] = 1.0
        rp10[3, 7] = 12.0

        result = self._run(mask, rp10)

        self.assertEqual(
            result["challenge"]["verdict"],
            "CURRENT_RP10_NECESSARY_CONDITION_FAIL",
        )
        self.assertEqual(result["challenge"]["candidate_farther_than_threshold_cells"], 1)

    def test_authority_drift_from_challenger_fails_closed(self) -> None:
        mask = self._blank()
        rp10 = self._blank().astype("float32")
        mask[3, 3] = 1.0
        rp10[3, 3] = 12.0

        def challenge(mask_dataset, rp10_dataset):
            result = worker._challenge.challenge_spurious_support(mask_dataset, rp10_dataset)
            result["benchmark_use_authorized"] = True
            return result

        with self.assertRaisesRegex(
            worker.CemsSpuriousSupportAcquisitionError,
            "exceeded authority ceiling",
        ):
            self._run(mask, rp10, challenger=challenge)

    def test_stage_b_candidate_count_drift_fails_closed(self) -> None:
        mask = self._blank()
        rp10 = self._blank().astype("float32")
        mask[3, 3] = 1.0
        rp10[3, 3] = 12.0

        def challenge(mask_dataset, rp10_dataset):
            result = worker._challenge.challenge_spurious_support(mask_dataset, rp10_dataset)
            result["candidate_support_cells"] = 2
            return result

        with self.assertRaisesRegex(
            worker.CemsSpuriousSupportAcquisitionError,
            "candidate support count differs",
        ):
            self._run(mask, rp10, challenger=challenge)

    def test_receipt_identity_mismatch_blocks_before_raster_challenge(self) -> None:
        mask = self._blank()
        rp10 = self._blank().astype("float32")
        mask[3, 3] = 1.0
        rp10[3, 3] = 12.0
        mask_bytes = self._geotiff(mask, dtype="float64")
        rp10_bytes = self._geotiff(rp10, dtype="float32")
        challenger = mock.Mock()

        def rp10_opener(request, _timeout):
            return _Response(request.full_url, rp10_bytes)

        def mask_opener(request, _timeout):
            return _Response(request.full_url, mask_bytes)

        with (
            mock.patch.object(worker._rp10_profile, "ACCEPTED_BYTE_COUNT", len(rp10_bytes)),
            mock.patch.object(worker._rp10_profile, "ACCEPTED_SHA256", "0" * 64),
        ):
            with self.assertRaisesRegex(
                worker.CemsSpuriousSupportAcquisitionError,
                "RP10 receipt SHA-256 differs",
            ):
                worker.acquire_and_challenge_cems_spurious_support(
                    rp10_opener=rp10_opener,
                    mask_opener=mask_opener,
                    challenger=challenger,
                )

        challenger.assert_not_called()


if __name__ == "__main__":
    unittest.main()
