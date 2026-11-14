# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only negative regressions for Dutch NBPW projected WFS geometry."""

from __future__ import annotations

import json
import unittest

from scripts.screen_nbpw_rdnew_multiline_v0 import (
    MAX_RESPONSE_BYTES,
    NbpwGeometryError,
    screen_nbpw_projected_multiline,
)


def _original(*, xy: list[list[float]] | None = None) -> bytes:
    points = xy if xy is not None else [[155000, 463000], [155100, 463100]]
    return json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"norm": "synthetic_only"},
                    "geometry": {"type": "MultiLineString", "coordinates": [points]},
                }
            ],
        }
    ).encode("utf-8")


class NbpwRdNewScreenTests(unittest.TestCase):
    def test_projected_synthetic_line_returns_nonadmission_summary(self) -> None:
        result = screen_nbpw_projected_multiline(_original(), declared_crs="EPSG:28992")
        self.assertEqual(result["bbox_rdnew"], [155000, 463000, 155100, 463100])
        self.assertEqual(result["vertices"], 2)
        self.assertEqual(result["crs_verification"], "range_plausibility_only")
        self.assertFalse(result["rights_approved"])
        self.assertFalse(result["scientifically_validated"])
        self.assertFalse(result["model_admission"])

    def test_rejects_geojson_lonlat_assumed_to_be_rd_new(self) -> None:
        with self.assertRaisesRegex(NbpwGeometryError, "outside"):
            screen_nbpw_projected_multiline(_original(xy=[[5.1, 52.0], [5.2, 52.1]]), declared_crs="EPSG:28992")

    def test_rejects_without_explicit_source_crs(self) -> None:
        with self.assertRaisesRegex(NbpwGeometryError, "independently declared"):
            screen_nbpw_projected_multiline(_original(), declared_crs="EPSG:4326")

    def test_rejects_html_error_and_oversize_response(self) -> None:
        for original in [b"<html>200 success</html>", b"x" * (MAX_RESPONSE_BYTES + 1)]:
            with self.subTest(size=len(original)), self.assertRaises(NbpwGeometryError):
                screen_nbpw_projected_multiline(original, declared_crs="EPSG:28992")

    def test_rejects_duplicate_keys_and_nonfinite(self) -> None:
        examples = [
            b'{"type":"FeatureCollection","type":"FeatureCollection","features":[]}',
            _original().replace(b"155000", b"NaN"),
        ]
        for original in examples:
            with self.subTest(original=original[:35]), self.assertRaises(NbpwGeometryError):
                screen_nbpw_projected_multiline(original, declared_crs="EPSG:28992")

    def test_rejects_boolean_ordinates_and_empty_geometry(self) -> None:
        with self.assertRaises(NbpwGeometryError):
            screen_nbpw_projected_multiline(_original(xy=[[True, 463000], [155100, 463100]]), declared_crs="EPSG:28992")
        empty = _original().replace(b"MultiLineString", b"Point")
        with self.assertRaises(NbpwGeometryError):
            screen_nbpw_projected_multiline(empty, declared_crs="EPSG:28992")


if __name__ == "__main__":
    unittest.main()
