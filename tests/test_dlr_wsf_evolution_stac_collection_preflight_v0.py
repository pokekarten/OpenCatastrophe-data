# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic-only tests for WSF Evolution STAC collection science boundary."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.dlr_wsf_evolution_stac_collection_preflight_v0 import (
    WSFMetadataBlocked, inspect_original_collection, interpret_detection_and_idc,
)

ROOT = Path(__file__).resolve().parents[1]


def doc():
    return {
        "type": "Collection", "id": "WSF_Evolution", "stac_version": "1.0.0",
        "license": "CC-BY-4.0",
        "description": "Global settlement evolution derived from Landsat-5/7, 1985-2015, 30m grid",
        "extent": {
            "spatial": {"bbox": [[-180, -90, 180, 90]]},
            "temporal": {"interval": [["1985-01-01T00:00:00Z", "2015-12-31T23:59:59.999Z"]]},
        },
        "providers": [{"name": "DLR/EOC Geoservice", "roles": ["host"]}],
        "links": [{"rel": "self", "href": "https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_Evolution?f=json"}],
    }


def blob(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify(data):
    raw = blob(data)
    return inspect_original_collection(raw, hashlib.sha256(raw).hexdigest())


class WSFCollectionTests(unittest.TestCase):
    def test_valid_metadata_preserves_non_admission(self):
        result = verify(doc())
        self.assertEqual(result["dataset_role"], "historical_settlement_detection_context_only")
        self.assertFalse(result["annual_coverage_measured_as_construction_years"])
        self.assertFalse(result["yearly_input_data_consistency_independently_checked"])
        self.assertFalse(result["original_raster_bytes_acquired"])
        self.assertFalse(result["model_input_admitted"])
        self.assertEqual(result["historical_years"], [1985, 2015])

    def test_wrong_identity_and_license_fail_closed(self):
        mutations = [
            ("id", "WSF_TRACKER"), ("type", "FeatureCollection"),
            ("stac_version", "2.0.0"), ("license", "proprietary"),
            ("description", "pixels"),
        ]
        for field, value in mutations:
            item = doc()
            item[field] = value
            with self.subTest(field=field), self.assertRaises(WSFMetadataBlocked):
                verify(item)

    def test_extent_drift_fails_closed(self):
        for path, changed in [
            (("spatial", "bbox"), [[-180, -60, 180, 78]]),
            (("temporal", "interval"), [["1990-01-01T00:00:00Z", "2015-12-31T23:59:59Z"]]),
            (("temporal", "interval"), [["1985-01-01T00:00:00Z", "2016-12-31T23:59:59Z"]]),
            (("temporal", "interval"), [["1985-01-01", "2015-12-31"]]),
        ]:
            item = doc()
            item["extent"][path[0]][path[1]] = changed
            with self.subTest(path=path, value=changed), self.assertRaises(WSFMetadataBlocked):
                verify(item)

    def test_bad_provider_and_external_self_link_fail_closed(self):
        d = doc(); d["providers"] = [{"name": "Unrelated host"}]
        with self.assertRaises(WSFMetadataBlocked): verify(d)
        for u in ["https://example.org/eoc/ogc/stac/v1/collections/WSF_Evolution", "http://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_Evolution", "https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/OTHER", "https://user:password@geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_Evolution", "https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_Evolution?token=secret", "https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_Evolution#private"]:
            d = doc(); d["links"][0]["href"] = u
            with self.subTest(url=u), self.assertRaises(WSFMetadataBlocked): verify(d)

    def test_sha_json_limits_and_duplicate_keys(self):
        r = blob(doc())
        with self.assertRaisesRegex(WSFMetadataBlocked, "SHA-256 mismatch"):
            inspect_original_collection(r, "0" * 64)
        for invalid in [b"", b"x" * 131073, b"\xff", b'{"id":"A","id":"B"}', b'{"foo":NaN}']:
            with self.subTest(invalid=invalid[:12]), self.assertRaises(WSFMetadataBlocked):
                inspect_original_collection(invalid, hashlib.sha256(invalid).hexdigest())

    def test_detection_year_and_idc_never_become_building_age(self):
        no_data = interpret_detection_and_idc(0, None)
        self.assertEqual(no_data["pixel_state"], "NO_DATA_NOT_NO_SETTLEMENT")
        self.assertIsNone(no_data["detection_year"])
        self.assertIsNone(no_data["construction_year"])
        expected = ["very_low", "low", "moderate", "fair", "good", "very_good"]
        for score in range(1, 7):
            row = interpret_detection_and_idc(1995, score)
            self.assertEqual(row["detection_year"], 1995)
            self.assertEqual(row["idc_quality"], expected[score-1])
            self.assertIsNone(row["construction_year"])
            self.assertFalse(row["model_input_admitted"])

    def test_bad_year_idc_and_unpaired_nodata_fail_closed(self):
        for year, idc in [(-1, None), (1, 3), (1984, 2), (2016, 6),
                          (1995, 0), (1995, 7), (1995, None), (0, 1),
                          (True, None), (1995, True), (2000.0, 5), (1995, "6")]:
            with self.subTest(year=year, idc=idc), self.assertRaises(WSFMetadataBlocked):
                interpret_detection_and_idc(year, idc)

    def test_cli_does_not_overwrite_source(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            original = folder / "original.json"
            output = folder / "receipt.json"
            raw = blob(doc())
            original.write_bytes(raw)
            cmd = [sys.executable, str(ROOT / "research_runners/dlr_wsf_evolution_stac_collection_preflight_v0.py"),
                   str(original), "--expected-sha256", hashlib.sha256(raw).hexdigest(), "--out", str(output)]
            run = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(result["model_input_admitted"])
            other = subprocess.run(cmd[:-1] + [str(original)], capture_output=True, text=True)
            self.assertNotEqual(other.returncode, 0)
            self.assertEqual(original.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
