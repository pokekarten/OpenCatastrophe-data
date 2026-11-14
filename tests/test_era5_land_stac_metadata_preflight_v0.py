# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline/synthetic tests only. No CDS login or ERA5 data downloads."""
from __future__ import annotations

import copy
import json
import unittest

from scripts.era5_land_stac_metadata_preflight_v0 import (
    COLLECTION, DOI, LICENSE_LINK, MAX_BYTES, ORIGINAL_URL,
    ERA5MetadataBlocked, inspect_metadata,
)


def fixture() -> dict:
    return {
        "type": "Collection",
        "id": COLLECTION,
        "stac_version": "1.1.0",
        "title": "Synthetic test of ERA5-Land catalogue contract",
        "license": "CC-BY-4.0",
        "sci:doi": DOI,
        "providers": [{"name": "ECMWF"}],
        "links": [
            {"rel": "self", "href": ORIGINAL_URL, "type": "application/json"},
            {"rel": "license", "href": LICENSE_LINK},
            {"rel": "retrieve", "href": "https://not-called.invalid/data"},
        ],
        "extent": {
            "spatial": {"bbox": [[0.0, -89.0, 360.0, 89.0]]},
            "temporal": {"interval": [[
                "1950-01-01T00:00:00+00:00",
                "2026-11-06T00:00:00+00:00",
            ]]},
        },
        "cads:sanity_check": {"status": "available"},
        "updated": "2026-11-12T00:00:00Z",
    }


def check(obj: dict):
    return inspect_metadata(json.dumps(obj, sort_keys=True).encode("utf-8"))


class ERA5LandSTACMetadataTests(unittest.TestCase):
    def test_valid_synthetic_metadata_does_not_admit_model_or_claim_original(self):
        out = check(fixture())
        self.assertEqual(out["source_id"], "copernicus.c3s.era5-land")
        self.assertEqual(out["catalogue_doi"], DOI)
        self.assertFalse(out["matches_original_2026_11_12_stac_receipt"])
        self.assertFalse(out["provider_authenticity_independently_proven"])
        self.assertTrue(out["underlying_cds_retrieval_requires_account_and_terms_acceptance"])
        self.assertTrue(out["represents_modelled_reanalysis_not_independent_event_observations"])
        self.assertEqual(out["original_grib_netcdf_values_read"], 0)
        self.assertEqual(out["network_requests_performed_by_validator"], 0)
        self.assertEqual(out["external_links_followed"], 0)
        self.assertFalse(out["scientific_model_input_approved"])
        self.assertNotIn("not-called.invalid", json.dumps(out))

    def test_wrong_provider_id_doi_license_or_stac_version_rejected(self):
        variants = [
            ("id", "reanalysis-era5-single-levels"),
            ("type", "FeatureCollection"),
            ("license", "unknown"),
            ("stac_version", "0.9.0"),
            ("sci:doi", "unreviewed-doi"),
            ("providers", [{"name": "Unknown"}]),
        ]
        for field, value in variants:
            with self.subTest(field=field):
                doc = fixture()
                doc[field] = value
                with self.assertRaises(ERA5MetadataBlocked):
                    check(doc)

    def test_untrusted_license_and_self_links_rejected(self):
        for index, value in ((0, "https://evil.invalid/stac"),
                             (1, "https://evil.invalid/terms")):
            doc = fixture()
            doc["links"][index]["href"] = value
            with self.subTest(index=index), self.assertRaises(ERA5MetadataBlocked):
                check(doc)

    def test_spatial_temporal_and_availability_drift_rejected(self):
        cases = [
            ("bbox", lambda d: d["extent"]["spatial"].update(bbox=[[-180, -90, 180, 90]])),
            ("start", lambda d: d["extent"]["temporal"]["interval"][0].__setitem__(0, "1940-01-01T00:00:00+00:00")),
            ("end", lambda d: d["extent"]["temporal"]["interval"][0].__setitem__(1, None)),
            ("status", lambda d: d["cads:sanity_check"].update(status="unsupported")),
        ]
        for name, change in cases:
            with self.subTest(name=name):
                doc = copy.deepcopy(fixture())
                change(doc)
                with self.assertRaises(ERA5MetadataBlocked):
                    check(doc)

    def test_invalid_json_duplicate_keys_nonfinite_and_size_rejected(self):
        cases = [
            b"", b"x" * (MAX_BYTES + 1),
            b'{"id":"one","id":"two"}', b'{"x":NaN}', b'{"x":1e999}',
            "not-bytes", b"\xff\xfe",
        ]
        for raw in cases:
            with self.subTest(raw=repr(raw)[:60]), self.assertRaises(ERA5MetadataBlocked):
                inspect_metadata(raw)


if __name__ == "__main__":
    unittest.main()
