# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

PROFILE_DEPS_AVAILABLE = (
    importlib.util.find_spec("rasterio") is not None
    and importlib.util.find_spec("numpy") is not None
)

if PROFILE_DEPS_AVAILABLE:
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin

    from scripts import acquire_cems_europe_rp10_profile as worker
    from scripts import acquire_cems_europe_rp10_receipt as receipt_mod
    from scripts import profile_cems_europe_rp10_geotiff as profile_mod


class _Response:
    def __init__(self, payload: bytes):
        self._stream = io.BytesIO(payload)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)


@unittest.skipUnless(
    PROFILE_DEPS_AVAILABLE,
    "requires requirements-cems-geotiff-profile.txt",
)
class CemsRp10TrustedProfileTests(unittest.TestCase):
    def _payload(self) -> bytes:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.tif"
            with rasterio.open(
                path,
                "w",
                driver="GTiff",
                width=2,
                height=2,
                count=1,
                dtype="float32",
                crs="EPSG:4326",
                transform=from_origin(10.0, 50.0, 0.01, 0.01),
                nodata=-9999.0,
            ) as dataset:
                dataset.write(
                    np.array([[0.0, 1.0], [2.0, -9999.0]], dtype="float32"),
                    1,
                )
                dataset.update_tags(1, UNITTYPE="m")
            return path.read_bytes()

    def _run(self, payload: bytes, *, profiler=None, sha256: str | None = None):
        digest = sha256 or hashlib.sha256(payload).hexdigest()

        def opener(_request, _timeout):
            return _Response(payload)

        def fake_receipt_acquirer(*, opener, clock, monotonic):
            del monotonic
            collected = bytearray()
            with opener(object(), 1.0) as response:
                while True:
                    chunk = response.read(7)
                    if not chunk:
                        break
                    collected.extend(chunk)
            self.assertEqual(bytes(collected), payload)
            return {
                "schema_version": receipt_mod.SCHEMA_VERSION,
                "dataset_id": receipt_mod.DATASET_ID,
                "source_issue": receipt_mod.SOURCE_ISSUE,
                "release": receipt_mod.RELEASE,
                "release_date": receipt_mod.RELEASE_DATE,
                "doi": receipt_mod.DOI,
                "return_period_years": receipt_mod.RETURN_PERIOD_YEARS,
                "filename": receipt_mod.FILENAME,
                "requested_url": receipt_mod.SOURCE_URL,
                "final_url": receipt_mod.SOURCE_URL,
                "retrieved_at": clock(),
                "http_status": 200,
                "media_type": "image/tiff",
                "content_length_header": len(payload),
                "byte_count": len(payload),
                "sha256": digest,
                "external_bytes_persisted": False,
                "geotiff_semantics_verified": False,
                "benchmark_use_authorized": False,
                "publication_authorized": False,
                "model_use_authorized": False,
            }

        selected_profiler = profiler or profile_mod.profile_cems_rp10_geotiff
        with (
            mock.patch.object(
                worker._receipt,
                "acquire_cems_rp10_receipt",
                side_effect=fake_receipt_acquirer,
            ),
            mock.patch.object(profile_mod, "ACCEPTED_BYTE_COUNT", len(payload)),
            mock.patch.object(profile_mod, "ACCEPTED_SHA256", hashlib.sha256(payload).hexdigest()),
        ):
            return worker.acquire_and_profile_cems_rp10(
                opener=opener,
                clock=lambda: "2026-09-06T06:30:00Z",
                profiler=selected_profiler,
            )

    def test_exact_ephemeral_bytes_are_profiled_then_removed(self) -> None:
        payload = self._payload()
        seen_path: list[Path] = []

        def profiler(path):
            local = Path(path)
            seen_path.append(local)
            self.assertTrue(local.exists())
            self.assertEqual(local.read_bytes(), payload)
            return profile_mod.profile_cems_rp10_geotiff(local)

        result = self._run(payload, profiler=profiler)

        self.assertEqual(result["schema_version"], worker.SCHEMA_VERSION)
        self.assertEqual(result["profile_issue"], 802)
        self.assertEqual(result["receipt_byte_count"], len(payload))
        self.assertEqual(result["receipt_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(result["geotiff_profile"]["width"], 2)
        self.assertEqual(result["geotiff_profile"]["height"], 2)
        self.assertEqual(result["geotiff_profile"]["band_unit_tags"], [{"UNITTYPE": "m"}])
        self.assertFalse(result["geotiff_profile"]["raster_values_inspected"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["benchmark_use_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertEqual(len(seen_path), 1)
        self.assertFalse(seen_path[0].exists())

    def test_receipt_mismatch_blocks_before_profiler(self) -> None:
        payload = self._payload()
        profiler = mock.Mock()
        with self.assertRaisesRegex(
            worker.CemsRp10ProfileAcquisitionError,
            "SHA-256 differs from accepted #793 receipt",
        ):
            self._run(payload, profiler=profiler, sha256="0" * 64)
        profiler.assert_not_called()

    def test_profile_failure_does_not_leave_provider_bytes(self) -> None:
        payload = self._payload()
        seen_path: list[Path] = []

        def profiler(path):
            local = Path(path)
            seen_path.append(local)
            raise profile_mod.CemsRp10GeoTiffProfileError("synthetic failure")

        with self.assertRaisesRegex(
            worker.CemsRp10ProfileAcquisitionError,
            "GeoTIFF metadata profile failed",
        ):
            self._run(payload, profiler=profiler)
        self.assertEqual(len(seen_path), 1)
        self.assertFalse(seen_path[0].exists())


if __name__ == "__main__":
    unittest.main()
