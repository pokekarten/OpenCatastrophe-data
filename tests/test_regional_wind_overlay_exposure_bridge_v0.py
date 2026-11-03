# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-pinned local integration for synthetic weather geometry and samples."""
from __future__ import annotations

from hashlib import sha256
import json
import unittest

from research_runners.regional_wind_overlay_exposure_bridge_v0 import run_bridge, BridgeError
from research_runners.regional_exposure_hazard_join_v0 import InputError
from research_runners.regional_wind_footprint_overlay_v0 import OverlayError


def rect(x1, y1, x2, y2):
    return {"type": "Polygon", "coordinates": [[
        [x1,y1], [x2,y1], [x2,y2], [x1,y2], [x1,y1]]]}


def geometry():
    return (
        {"schema_version":"nuts2-polygons-v0", "nuts_version":"2021",
         "crs":"EPSG:3035", "source_sha256":"a"*64,
         "features":[{"nuts2":"DE21","geometry":rect(0,0,2000,1000)},
                     {"nuts2":"DE22","geometry":rect(2000,0,3000,1000)}]},
        {"schema_version":"storm-grid-v0", "source_id":"SYNTHETIC-NOT-C3S",
         "source_sha256":"b"*64, "crs":"EPSG:3035",
         "event_id":"SYNTH-EVENT-1", "event_date":"2021-10-23",
         "peril":"extratropical_windstorm",
         "grid_cells":[
             {"cell_id":"c1","geometry":rect(0,0,1000,1000),"max_gust_mps":10},
             {"cell_id":"c2","geometry":rect(1000,0,2000,1000),"max_gust_mps":30},
         ]},
    )


def exposures():
    return [
        {"record_id":"SYNTH-EX-1","dataset_id":"SYNTHETIC-NOT-EIOPA",
         "as_of_date":"2020-12-31","nuts_version":"2021","nuts2":"DE21",
         "peril":"windstorm","occupancy":"residential","sum_insured_eur":1000000,
         "market_scope":"insurance_sample_not_full_market"},
        {"record_id":"SYNTH-EX-2","dataset_id":"SYNTHETIC-NOT-EIOPA",
         "as_of_date":"2020-12-31","nuts_version":"2021","nuts2":"DE21",
         "peril":"windstorm","occupancy":"commercial_including_industrial",
         "sum_insured_eur":800000, "market_scope":"insurance_sample_not_full_market"},
    ]


def canonical(x):
    return json.dumps(x, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()


def run(regions=None, storm=None, exp=None):
    a,b = geometry()
    original = tuple(map(canonical, (a if regions is None else regions,
                                    b if storm is None else storm,
                                    {"exposures":exposures() if exp is None else exp})))
    return run_bridge(*original, regions_sha256=sha256(original[0]).hexdigest(),
                      storm_sha256=sha256(original[1]).hexdigest(),
                      exposures_sha256=sha256(original[2]).hexdigest())


class RegionalWindBridgeTests(unittest.TestCase):
    def test_complete_region_with_matched_sample_no_loss(self):
        result=run()
        self.assertEqual(result["same_physical_event_id"],"SYNTH-EVENT-1")
        self.assertEqual(len(result["regionally_joined"]),2)
        self.assertEqual(result["regionally_joined"][0]["gust_mps"],30)
        self.assertEqual(result["full_coverage_region_count"],1)
        self.assertEqual(result["weather_incomplete_regions"],["DE22"])
        self.assertFalse(result["economic_or_insured_losses_calculated"])
        self.assertFalse(result["source_provider_hash_claims_independently_authenticated"])

    def test_partial_weather_quarantines_insured_sample_not_zero(self):
        a,b=geometry()
        b["grid_cells"].pop()
        result=run(storm=b)
        self.assertEqual(result["regionally_joined"],[])
        self.assertEqual(result["weather_incomplete_regions"],["DE21","DE22"])
        self.assertEqual(len(result["weather_not_evaluated_exposures"]),2)
        self.assertEqual({x["reason"] for x in result["weather_not_evaluated_exposures"]},
                         {"WIND_FOOTPRINT_INCOMPLETE_NOT_ZERO_WIND"})

    def test_wrong_nuts_vintage_not_joined(self):
        e=exposures()
        e[0]["nuts_version"]="2024"
        result=run(exp=e)
        self.assertEqual(len(result["regionally_joined"]),1)
        self.assertEqual(result["weather_not_evaluated_exposures"][0]["reason"],
                         "NUTS_VINTAGE_NOT_SAME_AS_HAZARD_GEOMETRY")

    def test_unknown_region_not_guessed(self):
        e=exposures()
        e[0]["nuts2"]="FR10"
        result=run(exp=e)
        self.assertEqual(len(result["regionally_joined"]),1)
        self.assertEqual(result["weather_not_evaluated_exposures"][0]["reason"],
                         "REGION_HAS_NO_BOUNDARY_IN_SOURCE")

    def test_full_weather_without_any_exposure_is_unmatched(self):
        result=run(exp=[])
        self.assertEqual(result["regionally_joined"],[])
        self.assertEqual(len(result["full_coverage_hazard_without_exposure"]),1)

    def test_exact_input_byte_pin_not_provider_signature(self):
        a,b=geometry()
        original=tuple(map(canonical,(a,b,{"exposures":exposures()})))
        with self.assertRaisesRegex(BridgeError,"bytes differ"):
            run_bridge(*original,regions_sha256="0"*64,
                       storm_sha256=sha256(original[1]).hexdigest(),
                       exposures_sha256=sha256(original[2]).hexdigest())
        self.assertFalse(run()["source_rights_and_scientific_release_verified"])

    def test_duplicate_json_key_is_rejected(self):
        a,b=geometry()
        original=(canonical(a),canonical(b),b'{"exposures":[],"exposures":[]}')
        with self.assertRaises(BridgeError):
            run_bridge(*original,
                       regions_sha256=sha256(original[0]).hexdigest(),
                       storm_sha256=sha256(original[1]).hexdigest(),
                       exposures_sha256=sha256(original[2]).hexdigest())

    def test_bad_exposure_rejected_before_weather_quarantine(self):
        a,b=geometry()
        b["grid_cells"].pop()
        e=exposures()
        e[0]["sum_insured_eur"]=-1
        with self.assertRaises(InputError):
            run(storm=b,exp=e)

    def test_duplicate_exposure_cannot_hide_in_uncovered_area(self):
        e=exposures()
        e[1]["record_id"]=e[0]["record_id"]
        with self.assertRaises(InputError):
            run(exp=e)

    def test_overlapping_regions_still_refused_by_geospatial_gate(self):
        a,b=geometry()
        a["features"][1]["geometry"]=rect(500,0,1000,100)
        with self.assertRaisesRegex(OverlayError,"overlapping NUTS2"):
            run(regions=a)

    def test_not_a_flood_adapter_without_physical_semantics(self):
        a,b=geometry()
        b["peril"]="pluvial_flood"
        with self.assertRaises(OverlayError):
            run(storm=b)

    def test_exposure_snapshot_after_event_is_temporally_blocked(self):
        a,b=geometry()
        b["event_date"]="2020-01-01"
        result=run(storm=b)
        self.assertEqual(result["regionally_joined"],[])
        self.assertEqual({x["reason"] for x in result["full_coverage_hazard_without_exposure"]},
                         {"exposure_snapshot_after_event_temporal_leakage"})

    def test_geography_and_exposure_order_does_not_change_matching(self):
        a,b=geometry()
        first=run(regions=a)
        a["features"].reverse()
        second=run(regions=a,exp=list(reversed(exposures())))
        self.assertEqual(first["regionally_joined"],second["regionally_joined"])
        self.assertEqual(first["weather_incomplete_regions"],second["weather_incomplete_regions"])


if __name__=="__main__":
    unittest.main()
