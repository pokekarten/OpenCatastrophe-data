# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only checks for WRI original GeoTIFF byte-range metadata gate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from research_runners.wri_aqueduct_original_tiff_range_preflight_v0 import (
    GEO_RANGE, IFD_RANGE, TiffGateError, inspect_original_tiff_ranges,
)

ROOT = Path(__file__).resolve().parents[1]

ENTRIES = [
    (256, 3, 1, 43200), (257, 3, 1, 21600), (258, 3, 1, 32),
    (259, 3, 1, 5), (262, 3, 1, 1),
    (273, 4, 21600, 44906842), (277, 3, 1, 1),
    (278, 3, 1, 1), (279, 4, 21600, 44820442),
    (284, 3, 1, 1), (317, 3, 1, 1), (339, 3, 1, 3),
    (33550, 12, 3, 44993248), (33922, 12, 6, 44993272),
    (34735, 3, 32, 44993320), (34736, 12, 2, 44993384),
    (34737, 2, 8, 44993400), (42113, 2, 6, 44993242),
]
GEO_KEYS = [1, 1, 0, 7, 1024, 0, 1, 2, 1025, 0, 1, 1,
            2048, 0, 1, 4326, 2049, 34737, 7, 0, 2054, 0, 1, 9102,
            2057, 34736, 1, 1, 2059, 34736, 1, 0]


def fixtures():
    header = bytearray(1024)
    struct.pack_into("<4sI", header, 0, b"II*\x00", IFD_RANGE[0])
    ifd = bytearray(2048)
    struct.pack_into("<H", ifd, 0, len(ENTRIES))
    for i, item in enumerate(ENTRIES):
        struct.pack_into("<HHII", ifd, 2 + i * 12, *item)
    geo = bytearray(208)
    geo[44993242 - GEO_RANGE[0]:44993248 - GEO_RANGE[0]] = b"-9999\x00"
    struct.pack_into("<3d", geo, 44993248 - GEO_RANGE[0], 1/120, 1/120, 0)
    struct.pack_into("<6d", geo, 44993272 - GEO_RANGE[0], 0, 0, 0, -180, 90, 0)
    struct.pack_into("<32H", geo, 44993320 - GEO_RANGE[0], *GEO_KEYS)
    return bytes(header), bytes(ifd), bytes(geo)


def inspect(parts):
    return inspect_original_tiff_ranges(
        *parts, *(hashlib.sha256(x).hexdigest() for x in parts)
    )


class OriginalWriTiffRangeTests(unittest.TestCase):
    def test_valid_metadata_keeps_nodata_and_insurance_blocked(self):
        out = inspect(fixtures())
        self.assertEqual([out["tiff_width"], out["tiff_height"]], [43200, 21600])
        self.assertEqual(out["original_nodata"], -9999)
        self.assertEqual(out["physrisk_zarr_fill_value_separately_observed"], 0)
        self.assertFalse(out["nodata_to_zarr_fill_transformation_verified"])
        self.assertFalse(out["pixel_values_read"])
        self.assertFalse(out["source_geotiff_cellwise_reconciled"])
        self.assertFalse(out["annual_occurrence_catalogue_provided"])
        self.assertFalse(out["model_input_admitted"])

    def test_reject_wrong_tiff_magic_and_ifd_offset(self):
        a, b, c = fixtures()
        for broken in (b"MM\x00*" + a[4:], a[:4] + b"\x00\x00\x00\x00" + a[8:]):
            with self.assertRaises(TiffGateError):
                inspect((broken, b, c))

    def test_reject_wrong_width_and_float_format_or_compression(self):
        a, b, c = fixtures()
        for tag, value in ((256, 42000), (258, 16), (259, 1), (339, 1), (278, 12)):
            changed = bytearray(b)
            pos = 2 + next(i for i, e in enumerate(ENTRIES) if e[0] == tag) * 12
            struct.pack_into("<I", changed, pos + 8, value)
            with self.subTest(tag=tag):
                with self.assertRaises(TiffGateError):
                    inspect((a, bytes(changed), c))

    def test_reject_different_georeference_or_nodata(self):
        a, b, c = fixtures()
        variants = []
        nodata = bytearray(c)
        nodata[44993242-GEO_RANGE[0]:44993248-GEO_RANGE[0]] = b"-9998\x00"
        variants.append(bytes(nodata))
        scale = bytearray(c)
        struct.pack_into("<d", scale, 44993248-GEO_RANGE[0], 1 / 60)
        variants.append(bytes(scale))
        origin = bytearray(c)
        struct.pack_into("<d", origin, 44993272-GEO_RANGE[0] + 24, -179)
        variants.append(bytes(origin))
        epsg = bytearray(c)
        struct.pack_into("<H", epsg, 44993320-GEO_RANGE[0] + 15 * 2, 3857)
        variants.append(bytes(epsg))
        for case in variants:
            with self.assertRaises(TiffGateError):
                inspect((a, b, case))

    def test_original_range_hash_and_length_enforced(self):
        a, b, c = fixtures()
        with self.assertRaisesRegex(TiffGateError, "SHA256 mismatch"):
            inspect_original_tiff_ranges(a, b, c, "0" * 64,
                                         hashlib.sha256(b).hexdigest(),
                                         hashlib.sha256(c).hexdigest())
        with self.assertRaises(TiffGateError):
            inspect((a[:-1], b, c))
        with self.assertRaises(TiffGateError):
            inspect((a, b + b"x", c))

    def test_duplicate_tag_blocks(self):
        a, b, c = fixtures()
        broken = bytearray(b)
        pos = 2 + 12
        struct.pack_into("<H", broken, pos, 256)
        with self.assertRaisesRegex(TiffGateError, "duplicate"):
            inspect((a, bytes(broken), c))

    def test_cli_source_paths_immutable(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            parts = fixtures()
            inputs = [p / name for name in ("original-header", "original-ifd", "original-geo")]
            for file, payload in zip(inputs, parts):
                file.write_bytes(payload)
            out = p / "receipt.json"
            cmd = [
                sys.executable,
                str(ROOT / "research_runners/wri_aqueduct_original_tiff_range_preflight_v0.py"),
                *(str(f) for f in inputs),
                "--expected-header-sha256", hashlib.sha256(parts[0]).hexdigest(),
                "--expected-ifd-sha256", hashlib.sha256(parts[1]).hexdigest(),
                "--expected-geo-sha256", hashlib.sha256(parts[2]).hexdigest(),
                "--out", str(out),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(out.read_text())["model_input_admitted"])
            invalid = subprocess.run(cmd[:-1] + [str(inputs[0])],
                                     capture_output=True, text=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertEqual(inputs[0].read_bytes(), parts[0])


if __name__ == "__main__":
    unittest.main()
