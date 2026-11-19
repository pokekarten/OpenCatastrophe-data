# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic AOI-index source contract. Does not embed third-party raw data."""
import copy
import unittest

from research_runners.zenodo5795435_emsr165_aoi_original_index_v0 import (
    AOISourceBlocked, audit_index, audit_original_bytes,
)

RASTER = ("clm_flood.events_copernicus.ems_p_30m_0..0cm_"
          "20160301..20160531_eumap_epsg3035_v0.2.tif")


def row(aoi, x, y, ems="EMSR165", year=2016, season="spring", raster=RASTER):
    return {
        "type": "Feature",
        "properties": {
            "EMS_ID": ems, "EMS_AOI": aoi,
            "EMS_LINK": "https://emergency.copernicus.eu/mapping/list-of-components/" + ems,
            "YEAR_START": year, "YEAR_END": year, "SEASON": season,
            "geo_harmonizer_raster": raster,
        },
        "geometry": {"type": "Point", "coordinates": [x, y]},
    }


def envelope():
    return {
        "type": "FeatureCollection", "name": "clm_flood",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::3035"}},
        "features": [
            row("POISSY", 3740885.6, 2900951.1),
            row("MANTESLAJOLIE", 3722107.3, 2911777.9),
            row("PARIS", 3760184.1, 2890959.4),
            row("YERRES", 3765559.3, 2872379.4),
        ],
    }


class ZenodoGeoHarmonizerIndexTests(unittest.TestCase):
    def test_2016_emrs165_original_subset_has_four_not_montargis(self):
        r = audit_index(envelope())
        self.assertEqual(r["emsr165_aoi_points_in_this_archive"], 4)
        self.assertEqual(r["emsr165_aoi_names_in_this_archive"],
                         ["MANTESLAJOLIE", "PARIS", "POISSY", "YERRES"])
        self.assertFalse(r["montargis_name_present_for_emsr165"])
        self.assertFalse(r["emsn028_montargis_covered_by_this_rapid_index"])

    def test_original_index_uses_epsg3035_and_is_not_wgs84_geojson(self):
        r = audit_index(envelope())
        self.assertEqual(r["source_crs"], "urn:ogc:def:crs:EPSG::3035")
        self.assertFalse(r["treat_coordinates_as_wgs84_lon_lat"])

    def test_synthetic_aoi_centroids_never_become_extent_or_depth_truth(self):
        r = audit_index(envelope())
        for k in ("aoi_centroids_are_original_flood_extent_polygons",
                  "mosaic_pixels_are_event_specific_or_daily",
                  "building_or_property_water_depth_established",
                  "source_2016_peak_observation_proven",
                  "independent_2016_montargis_holdout_established",
                  "provider_raster_original_bytes_authenticated",
                  "risk_model_input_admitted"):
            self.assertFalse(r[k], k)

    def test_year_2000_vs_2020_raster_anomaly_is_flagged_not_repaired(self):
        d = envelope()
        d["features"].append(row(
            "AOI02", 4894286.9, 5038736.3, ems="EMSR441", year=2000,
            season="summer",
            raster="clm_flood.events_copernicus.ems_p_30m_0..0cm_"
                   "20200601..20200831_eumap_epsg3035_v0.2.tif",
        ))
        r = audit_index(d)
        self.assertEqual(r["original_index_year_mismatch_count"], 1)
        self.assertEqual(r["year_mismatch_activation_codes"], ["EMSR441"])
        self.assertTrue(r["year_2000_metadata_may_not_be_silently_corrected"])

    def test_unknown_year_mismatch_is_not_automatically_repaired(self):
        d = envelope()
        d["features"].append(row(
            "AOI01", 4800000, 5000000, ems="EMSR999", year=2019,
            raster="clm_flood.events_copernicus.ems_p_30m_0..0cm_"
                   "20200601..20200831_eumap_epsg3035_v0.2.tif",
        ))
        with self.assertRaises(AOISourceBlocked):
            audit_index(d)

    def test_2000_date_without_reviewed_exception_rejected(self):
        d = envelope()
        d["features"].append(row("AOI01", 4800000, 5000000, ems="EMSR999", year=2000))
        with self.assertRaises(AOISourceBlocked):
            audit_index(d)

    def test_missing_emrs165_aoi_is_not_full_coverage(self):
        d = envelope()
        d["features"] = d["features"][:3]
        with self.assertRaises(AOISourceBlocked):
            audit_index(d)

    def test_duplicate_named_emrs165_aoi_blocked(self):
        d = envelope()
        d["features"].append(copy.deepcopy(d["features"][0]))
        with self.assertRaises(AOISourceBlocked):
            audit_index(d)

    def test_fabricated_montargis_aoi_not_silently_admitted(self):
        d = envelope()
        d["features"].append(row("MONTARGIS", 3760000, 2900000))
        with self.assertRaises(AOISourceBlocked):
            audit_index(d)

    def test_emsn028_is_other_product_family(self):
        d = envelope()
        d["features"].append(row("MONTARGIS", 3760000, 2900000, ems="EMSN028"))
        with self.assertRaises(AOISourceBlocked):
            audit_index(d)

    def test_wrong_crs_and_missing_crs_block(self):
        for crs in ({"type": "name", "properties": {"name": "EPSG:4326"}}, None):
            d = envelope()
            d["crs"] = crs
            with self.subTest(crs=crs), self.assertRaises(AOISourceBlocked):
                audit_index(d)

    def test_wrong_geometry_family_and_lonlat_misread_blocked(self):
        for geom in ({"type": "Polygon", "coordinates": []},
                     {"type": "Point", "coordinates": [2.7, 48.0]},
                     {"type": "Point", "coordinates": [None, 2900951]},
                     {"type": "Point", "coordinates": [True, 2900951]},
                     {"type": "Point", "coordinates": [float("nan"), 2900951]}):
            d = envelope()
            d["features"][0]["geometry"] = geom
            with self.subTest(geom=geom), self.assertRaises(AOISourceBlocked):
                audit_index(d)

    def test_wrong_emsr165_mosaic_season_or_year_blocks(self):
        for key, value in (("SEASON", "summer"), ("YEAR_START", 2017),
                           ("geo_harmonizer_raster",
                            "clm_flood.events_copernicus.ems_p_30m_0..0cm_"
                            "20160601..20160831_eumap_epsg3035_v0.2.tif")):
            d = envelope()
            d["features"][0]["properties"][key] = value
            with self.subTest(key=key), self.assertRaises(AOISourceBlocked):
                audit_index(d)

    def test_untrusted_original_bytes_require_exact_zenodo_md5_and_length(self):
        for contents in (b"", b"{}", b"x" * 203733):
            with self.subTest(n=len(contents)), self.assertRaises(AOISourceBlocked):
                audit_original_bytes(contents)

    def test_injected_model_approval_does_not_pass_strict_source_root(self):
        d = envelope()
        d["admitted_for_cat_loss"] = True
        with self.assertRaises(AOISourceBlocked):
            audit_index(d)

    def test_calendar_counts_are_aoi_index_counts_not_independent_events(self):
        d = envelope()
        d["features"].append(row(
            "SYNTHETIC_OTHER", 4800000, 2900000, ems="EMSR888",
            year=2016, season="summer",
            raster="clm_flood.events_copernicus.ems_p_30m_0..0cm_"
                   "20160601..20160831_eumap_epsg3035_v0.2.tif",
        ))
        r = audit_index(d)
        self.assertEqual(r["2016_spring_index_aoi_point_rows"], 4)
        self.assertEqual(r["2016_summer_index_aoi_point_rows"], 1)
        self.assertFalse(r["mosaic_pixels_are_event_specific_or_daily"])


if __name__ == "__main__":
    unittest.main()
