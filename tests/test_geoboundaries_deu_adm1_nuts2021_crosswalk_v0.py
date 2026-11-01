# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only conservative 2021 NUTS1/ADM1 geometry linkage regressions."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

from research_runners.geoboundaries_deu_adm1_nuts2021_crosswalk_v0 import (
    CROSSWALK_APP_ID, EUROSTAT_COMMIT, EUROSTAT_SHA256, EUROSTAT_SIZE,
    EXPECTED_NUTS, CrosswalkError, audit_crosswalk, build_crosswalk_staging,
    _parse_eurostat, resolve_nuts1_for_point,
)
from research_runners.geoboundaries_deu_adm1_cat_sqlite_v0 import (
    build_staging_from_bytes,
)
from tests.test_geoboundaries_deu_adm1_original_geojson_v0 import (
    raw, valid_collection,
)

HAS_SPATIAL = (
    importlib.util.find_spec("shapely") is not None
    and importlib.util.find_spec("pyproj") is not None
)


def pair():
    geo = valid_collection()
    codes = sorted(EXPECTED_NUTS)
    nuts = {"type": "FeatureCollection", "features": [
        {
            "type": "Feature",
            "properties": {"id": code, "na": f"reference-{code}"},
            "geometry": copy.deepcopy(g["geometry"]),
        } for code, g in zip(codes, geo["features"])
    ]}
    for k in range(107):
        nuts["features"].append({
            "type": "Feature",
            "properties": {"id": f"ZZ{k:03d}", "na": f"other-{k:03d}"},
            "geometry": copy.deepcopy(geo["features"][0]["geometry"]),
        })
    return geo, nuts


def validated(geo: dict, nuts: dict):
    a, b = raw(geo), raw(nuts)
    return audit_crosswalk(
        a, b, geo_sha256=hashlib.sha256(a).hexdigest(),
        geo_size=len(a), nuts_sha256=hashlib.sha256(b).hexdigest(),
        nuts_size=len(b),
    )


class OfficialSourceIdentityTests(unittest.TestCase):
    def test_immutable_source_revision_and_content_digest_present(self):
        self.assertEqual(EUROSTAT_COMMIT, "8186be451525164ea24b43560cb943fda7c5520c")
        self.assertEqual(EUROSTAT_SIZE, 194955)
        self.assertEqual(len(EUROSTAT_SHA256), 64)
        self.assertEqual(len(EXPECTED_NUTS), 16)

    def test_geojson_hash_drift_rejected_even_with_valid_fixture(self):
        _, nuts = pair()
        data = raw(nuts)
        with self.assertRaisesRegex(CrosswalkError, "SHA-256"):
            _parse_eurostat(data, expected_sha256="0" * 64, expected_size=len(data))
        with self.assertRaisesRegex(CrosswalkError, "byte count"):
            _parse_eurostat(data, expected_sha256=hashlib.sha256(data).hexdigest(),
                            expected_size=len(data) - 1)

    def test_duplicate_or_nonfinite_json_blocked(self):
        for bad in (
            b'{"type":"FeatureCollection","type":"FeatureCollection"}',
            b'{"features":NaN}',
        ):
            with self.assertRaises(CrosswalkError):
                _parse_eurostat(bad, expected_sha256=hashlib.sha256(bad).hexdigest(),
                                expected_size=len(bad))

    def test_missing_de_code_or_unreviewed_crs_rejected(self):
        _, nuts = pair()
        nuts["features"][0]["properties"]["id"] = "FR999"
        b = raw(nuts)
        with self.assertRaisesRegex(CrosswalkError, "missing/extra"):
            _parse_eurostat(b, expected_sha256=hashlib.sha256(b).hexdigest(),
                            expected_size=len(b))
        _, nuts = pair()
        nuts["crs"] = {"type": "name", "properties": {"name": "EPSG:3857"}}
        b = raw(nuts)
        with self.assertRaisesRegex(CrosswalkError, "CRS"):
            _parse_eurostat(b, expected_sha256=hashlib.sha256(b).hexdigest(),
                            expected_size=len(b))


@unittest.skipUnless(HAS_SPATIAL, "Reviewed spatial environment needed")
class IndependentPolygonMatchingTests(unittest.TestCase):
    def test_exact_synthetic_16_to_16_bijection_no_names_required(self):
        geo, nuts = pair()
        mapping, receipt = validated(geo, nuts)
        self.assertEqual(len(mapping), 16)
        self.assertEqual(set(x["nuts1_code"] for x in mapping), EXPECTED_NUTS)
        self.assertEqual(receipt["matched_distinct_nuts1_codes"], 16)
        self.assertEqual(receipt["minimum_geo_polygon_coverage"], 1.0)
        self.assertEqual(receipt["minimum_nuts_polygon_coverage"], 1.0)
        self.assertTrue(receipt["nuts2016_eubucco_modified_geography_not_covered"])
        self.assertFalse(receipt["insurer_exposure_or_real_building_rows_imported"])
        # Intentionally no match on label: source shapeName STATE-nn,
        # official reference labels reference-DE*, but geometries coincide.
        self.assertNotIn("shape_names", receipt)

    def test_non_bijective_and_drifted_nuts_geometry_fail(self):
        geo, nuts = pair()
        # Take all coordinate space from a different source region.
        nuts["features"][0]["geometry"] = copy.deepcopy(
            nuts["features"][1]["geometry"]
        )
        with self.assertRaises(CrosswalkError):
            validated(geo, nuts)
        geo, nuts = pair()
        # Width contraction to 10% retains a valid, positive-area polygon
        # but cannot be accepted as the same administrative coverage.
        poly = nuts["features"][0]["geometry"]["coordinates"][0]
        xmin = min(x for x, y in poly)
        for xy in poly:
            xy[0] = xmin + 0.1 * (xy[0] - xmin)
        with self.assertRaisesRegex(CrosswalkError, "high-coverage"):
            validated(geo, nuts)

    def test_build_independent_CAT2_sqlite_readonly_and_no_prod_writes(self):
        geo, nuts = pair()
        mapping, receipt = validated(geo, nuts)
        with tempfile.TemporaryDirectory(prefix="cat-nuts-") as tmp:
            out = Path(tmp) / "nuts2021.cat.sqlite"
            build_crosswalk_staging(mapping, receipt, out)
            self.assertTrue(out.exists())
            with sqlite3.connect(out) as db:
                self.assertEqual(db.execute("PRAGMA application_id").fetchone()[0],
                                 CROSSWALK_APP_ID)
                self.assertEqual(db.execute("SELECT count(*) FROM region_mapping").fetchone()[0],
                                 16)
                self.assertEqual(db.execute("SELECT model_input_approved FROM provenance").fetchone()[0],
                                 0)
            with self.assertRaises(Exception):
                build_crosswalk_staging(mapping, receipt, out)
            # Positive query with synthetic stage is intentionally forbidden
            # by the real-source SHA gate on read side.
            geobytes = raw(geo)
            geodb = Path(tmp) / "geo.cat.sqlite"
            build_staging_from_bytes(
                geobytes, expected_sha256=hashlib.sha256(geobytes).hexdigest(),
                expected_size=len(geobytes), output_path=geodb,
            )
            with self.assertRaisesRegex(CrosswalkError, "unapproved source"):
                resolve_nuts1_for_point(geodb, out, 6.25, 48.25)


if __name__ == "__main__":
    unittest.main()
