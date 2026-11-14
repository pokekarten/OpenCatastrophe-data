# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure synthetic original-GISCO-ID test data; no source API traffic."""
from __future__ import annotations

import hashlib
import json
import unittest

from research_runners.eurostat_gisco_2021_independent_grid_id_v0 import (
    GISCOIdentityError, verify_original_gisco_cell,
)


def synthetic(*, grid=None, country=None):
    grid = grid or {
        "grid_id": "XY_CRS3035RES1000mN5399000E5018000",
        "uid": 31415,
        "nuts3_id": "XY001",
        "OBJECTID": "XY_CRS3035RES1000mN5399000E5018000",
    }
    country = country or {"cntr_id": "XY", "OBJECTID": "XY"}
    g = json.dumps([{"attributes": grid}], separators=(",", ":")).encode()
    c = json.dumps([{"attributes": country}], separators=(",", ":")).encode()
    return g, c


def verify(g, c, **kw):
    return verify_original_gisco_cell(
        g, c, raster_x_m=kw.pop("x", 5018500),
        raster_y_m=kw.pop("y", 5399500),
        grid_sha256=kw.pop("grid_sha", hashlib.sha256(g).hexdigest()),
        country_sha256=kw.pop("country_sha", hashlib.sha256(c).hexdigest()),
        **kw,
    )


class SourceIdentity(unittest.TestCase):
    def test_valid_grid_and_country_without_population_claim(self):
        grid, country = synthetic()
        value = verify(grid, country)
        self.assertEqual(value["grid_id"], "XY_CRS3035RES1000mN5399000E5018000")
        self.assertEqual(value["nuts3_id"], "XY001")
        self.assertFalse(value["independent_2021_v3_population_count_verified"])
        self.assertFalse(value["scientific_model_input_admitted"])
        self.assertFalse(value["commercial_underwriting_authorized"])
        self.assertNotIn("31415", json.dumps(value))

    def test_moved_pixel_or_different_grid_id_blocked(self):
        g, c = synthetic()
        with self.assertRaisesRegex(GISCOIdentityError, "differs"):
            verify(g, c, x=5019500)
        with self.assertRaisesRegex(GISCOIdentityError, "not a centre"):
            verify(g, c, y=5399000)

    def test_country_and_nuts3_mismatch_blocked(self):
        g, c = synthetic(country={"cntr_id": "ZZ", "OBJECTID": "ZZ"})
        with self.assertRaisesRegex(GISCOIdentityError, "country/NUTS3"):
            verify(g, c)
        g, c = synthetic(grid={
            "grid_id": "XY_CRS3035RES1000mN5399000E5018000",
            "uid": 0, "nuts3_id": "XY001",
            "OBJECTID": "XY_CRS3035RES1000mN5399000E5018000",
        })
        with self.assertRaisesRegex(GISCOIdentityError, "UID"):
            verify(g, c)

    def test_response_digest_duplicate_json_and_extra_fields_blocked(self):
        g, c = synthetic()
        with self.assertRaisesRegex(GISCOIdentityError, "SHA-256 mismatch"):
            verify(g, c, grid_sha="0" * 64)
        invalid = b'[{"attributes":{"grid_id":"XY","grid_id":"XY"}}]'
        with self.assertRaisesRegex(GISCOIdentityError, "duplicate"):
            verify(invalid, c)
        g, c = synthetic(grid={
            "grid_id": "XY_CRS3035RES1000mN5399000E5018000",
            "uid": 1, "nuts3_id": "XY001",
            "OBJECTID": "XY_CRS3035RES1000mN5399000E5018000",
            "private_person": "never",
        })
        with self.assertRaisesRegex(GISCOIdentityError, "attributes"):
            verify(g, c)

    def test_invalid_input_and_response_envelope_block(self):
        grid, country = synthetic()
        with self.assertRaisesRegex(GISCOIdentityError, "response size"):
            verify(b"x" * 2049, country)
        with self.assertRaisesRegex(GISCOIdentityError, "integral"):
            verify(grid, country, x=True)
        with self.assertRaisesRegex(GISCOIdentityError, "official feature"):
            verify(b"[]", country)


if __name__ == "__main__":
    unittest.main()
