# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic exact-footprint cross-vintage Luxembourg overlay and fail-closed tests."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

HAS_GEO=all(importlib.util.find_spec(x) is not None for x in
            ("shapely","pyproj","pyarrow"))
if HAS_GEO:
    import pyarrow as pa
    import pyarrow.parquet as pq
    from pyproj import Transformer
    from shapely.geometry import box
    from shapely.ops import transform
    from tests.test_luxembourg_gpkg_schema_window_v0 import write_source
    from research_runners import luxembourg_geobase2026_eubucco_bounded_pair_v0 as mod


@unittest.skipUnless(HAS_GEO,"requires pinned PyArrow, PyProj and Shapely")
class Geobase2026EubuccoOriginalPairTests(unittest.TestCase):
    def setUp(self):
        temp=TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.gpkg=Path(temp.name)/"synthetic-geobase.gpkg"
        self.parquet=Path(temp.name)/"synthetic-eubucco.parquet"
        write_source(self.gpkg,count=3)
        native_to_3035=Transformer.from_crs(2169,3035,always_xy=True)
        area=transform(native_to_3035.transform,box(75000,75000,75020,75020))
        pq.write_table(pa.table({
            "id":pa.array(["SYN-EUBUCCO"]),
            "region_id":pa.array(["LU000"]),
            "geometry":pa.array([area.wkb],type=pa.binary()),
            "geometry_source":pa.array(["gov-luxembourg"]),
            "height_source":pa.array(["gov-luxembourg"]),
        }),self.parquet,compression="NONE")
        native_to_wgs84=Transformer.from_crs(2169,4326,always_xy=True)
        self.lon,self.lat=native_to_wgs84.transform(75010,75010)

    def audit(self,**kwargs):
        sha1=hashlib.sha256(self.gpkg.read_bytes()).hexdigest()
        sha2=hashlib.sha256(self.parquet.read_bytes()).hexdigest()
        with (patch.object(mod,"GEOBASE_SHA",sha1),
              patch.object(mod,"EUBUCCO_SHA",sha2),
              patch.object(mod,"GEOBASE_COUNT",3),
              patch.object(mod,"EUBUCCO_COUNT",1)):
            args=dict(lon=self.lon,lat=self.lat,halfwidth=30,cap=5,
                      geobase_sha=sha1,eubucco_sha=sha2,
                      geobase_layer="buildings",geobase_id="building_ref")
            args.update(kwargs)
            return mod.run(self.gpkg,self.parquet,**args)

    def test_identical_polygon_is_candidate_never_proven_identity(self):
        r=self.audit()
        self.assertEqual(r["original_pair_features"]["geobase2026"],1)
        self.assertEqual(r["original_pair_features"]["eubucco_v0_2"],1)
        self.assertEqual(r["geobase2026_roof_unspecified_polygon_classification"]
                         ["unique_candidates_iou_gte_0_60"],1)
        self.assertFalse(r["source_pair_independent_ground_truth"])
        self.assertFalse(r["historical_building_identity_crosswalk_verified"])
        self.assertFalse(r["model_input_admitted"])
        self.assertNotIn("SYN-EUBUCCO",json.dumps(r))
        self.assertNotIn("B-1",json.dumps(r))

    def test_wrong_source_digest_rejected(self):
        with self.assertRaisesRegex(mod.CrosscheckError,"pins"):
            self.audit(geobase_sha="0"*64)

    def test_unknown_region_rejected(self):
        with self.assertRaisesRegex(mod.CrosscheckError,"bounds"):
            self.audit(lon=13.1)

    def test_unbounded_window_and_per_source_cap_rejected(self):
        with self.assertRaisesRegex(mod.CrosscheckError,"bounds"):
            self.audit(halfwidth=10000)
        with self.assertRaisesRegex(mod.CrosscheckError,"bounds"):
            self.audit(cap=50000)

    def test_eubucco_region_mismatch_fails_closed(self):
        table=pq.read_table(self.parquet)
        idx=table.schema.get_field_index("region_id")
        table=table.set_column(idx,"region_id",pa.array(["BE100"]))
        pq.write_table(table,self.parquet,compression="NONE")
        with self.assertRaisesRegex(mod.CrosscheckError,"region|NUTS3"):
            self.audit()


if __name__=="__main__":
    unittest.main()
