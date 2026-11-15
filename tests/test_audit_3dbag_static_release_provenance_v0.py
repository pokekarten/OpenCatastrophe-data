# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""All source metadata fixtures here are invented, never real property files."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_3dbag_static_release_provenance_v0 import (
    EXPECTED_CRS, EXPECTED_DATE, EXPECTED_ID, EXPECTED_VERSION,
    ReleaseProvenanceError, load, main, validate,
)


def source():
    return {
        "identificationInfo": {
            "citation": {
                "title": "3DBAG",
                "edition": EXPECTED_VERSION,
                "date": EXPECTED_DATE,
                "dateType": "creation",
                "identifier": EXPECTED_ID,
            },
            "resourceConstraints": [{
                "accessConstraints": "otherRestrictions",
                "otherConstraints": [{
                    "href": "http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1",
                    "text": "Naamensvermelding verplicht, 3DBAG door TU Delft en 3DGI",
                }],
            }],
        },
        "referenceSystemInfo": [{
            "referenceSystemIdentifier": EXPECTED_CRS,
        }],
        "dataQualityInfo": {
            "lineage": {
                "source": [{"source": "fictional-source"}],
                "processStep": [{"step": "synthetic-fixture"}],
            },
        },
    }


def header(*, release=EXPECTED_VERSION):
    return {
        "type": "CityJSON",
        "version": "2.0",
        "metadata": {
            "referenceSystem": EXPECTED_CRS,
            "version": release,
            "fullMetadataUrl": "https://data.3dbag.nl/v20250903/metadata.json",
        },
    }


class StaticReleaseReceiptTests(unittest.TestCase):
    def test_metadata_pins_known_release_but_not_live_api(self):
        r = validate(source())
        self.assertEqual(r["release_id"], EXPECTED_VERSION)
        self.assertTrue(r["original_cc_by_4_attribution_found"])
        self.assertFalse(r["static_cityjson_header_exact_release_match"])
        self.assertFalse(r["live_individual_building_api_release_verified"])
        self.assertFalse(r["actual_building_volume_verified_for_this_release"])
        self.assertFalse(r["source_admitted"])
        self.assertFalse(r["insurance_rebuild_cost_or_tiv_authorised"])

    def test_static_header_with_explicit_release_may_match(self):
        r = validate(source(), static_cityjson_header=header())
        self.assertTrue(r["static_cityjson_header_exact_release_match"])
        self.assertFalse(r["live_individual_building_api_release_verified"])

    def test_cityjson_serialisation_version_not_source_release(self):
        with self.assertRaisesRegex(ReleaseProvenanceError, "not pinned"):
            validate(source(), static_cityjson_header=header(release="2.0"))
        for key, value in (("referenceSystem", "EPSG:4326"),
                           ("fullMetadataUrl", "https://evil.example/metadata.json")):
            with self.subTest(key=key):
                h = header()
                h["metadata"][key] = value
                with self.assertRaises(ReleaseProvenanceError):
                    validate(source(), static_cityjson_header=h)

    def test_version_identifier_date_and_crs_drift_fails_closed(self):
        for key, value in (("date", "2026-02-21"), ("edition", "v2026.02.21"),
                           ("identifier", "not-the-identified-release")):
            with self.subTest(key=key):
                doc = source()
                doc["identificationInfo"]["citation"][key] = value
                with self.assertRaises(ReleaseProvenanceError):
                    validate(doc)
        doc = source()
        doc["referenceSystemInfo"][0]["referenceSystemIdentifier"] = "EPSG:4326"
        with self.assertRaises(ReleaseProvenanceError):
            validate(doc)

    def test_without_attribution_and_lineage_cannot_pass(self):
        doc = source()
        doc["identificationInfo"]["resourceConstraints"][0]["otherConstraints"] = []
        with self.assertRaises(ReleaseProvenanceError):
            validate(doc)
        doc = source()
        doc["dataQualityInfo"]["lineage"]["source"] = []
        with self.assertRaises(ReleaseProvenanceError):
            validate(doc)

    def test_cli_only_reads_metadata_and_emits_sha256_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "metadata.json"
            h = Path(temp) / "static-header.json"
            p.write_text(json.dumps(source()), encoding="utf-8")
            h.write_text(json.dumps(header()), encoding="utf-8")
            self.assertEqual(main(["--release-metadata", str(p),
                                   "--static-cityjson-header", str(h)]), 0)
            self.assertEqual(len(load(p)[1]), 64)
            p.write_text('{"metadata":1,"metadata":2}', encoding="utf-8")
            with self.assertRaises(ReleaseProvenanceError):
                load(p)
            self.assertEqual(main(["--release-metadata", str(p)]), 2)


if __name__ == "__main__":
    unittest.main()
