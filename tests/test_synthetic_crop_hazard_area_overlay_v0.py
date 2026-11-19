# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only deterministic crop flood/hail area regression tests."""
from __future__ import annotations

import unittest
from shapely.geometry import box, mapping, Polygon
from research_runners.synthetic_crop_hazard_area_overlay_v0 import OverlayError, overlay


def fixture():
    parcels = {
        'schema': 'synthetic-crop-parcels-v0', 'crs': 'EPSG:3035',
        'synthetic_only': True, 'external_source_rows_used': 0,
        'parcels': [
            {'parcel_id': 'SYNTH-CROP-001', 'crop_class': 'SYNTH-WHEAT',
             'geometry': mapping(box(0, 0, 100, 100))},
            {'parcel_id': 'SYNTH-CROP-002', 'crop_class': 'SYNTH-MAIZE',
             'geometry': mapping(box(100, 0, 200, 100))},
        ],
    }
    hazard = {
        'schema': 'synthetic-crop-hazard-v0', 'crs': 'EPSG:3035',
        'synthetic_only': True, 'external_source_rows_used': 0,
        'event_id': 'SYNTH-EVENT-001', 'peril': 'flood', 'unit': 'm',
        'zones': [
            {'zone_id': 'SYNTH-ZONE-001', 'intensity': 1, 'nodata': False,
             'geometry': mapping(box(0, 0, 150, 100))},
            {'zone_id': 'SYNTH-ZONE-002', 'intensity': 2, 'nodata': False,
             'geometry': mapping(box(50, 0, 100, 100))},
            {'zone_id': 'SYNTH-ZONE-003', 'intensity': None, 'nodata': True,
             'geometry': mapping(box(150, 0, 200, 100))},
        ],
    }
    return parcels, hazard


class CropOverlayTests(unittest.TestCase):
    def test_overlap_max_intensity_and_nodata_area_conservation(self):
        fields, hazard = fixture()
        result = overlay(fields, hazard)
        self.assertEqual(result['parcel_count'], 2)
        first, second = result['synthetic_parcels']
        self.assertEqual(first['total_area_m2'], 10000)
        self.assertEqual(first['intensity_bands'], [
            {'intensity': 2.0, 'area_m2': 5000.0},
            {'intensity': 1.0, 'area_m2': 5000.0},
        ])
        self.assertEqual(first['outside_support_unknown_area_m2'], 0)
        self.assertEqual(second['observed_synthetic_support_area_m2'], 5000)
        self.assertEqual(second['explicit_nodata_area_m2'], 5000)
        self.assertEqual(result['totals']['observed_synthetic_support_area_m2'], 15000)
        self.assertFalse(result['insured_losses_calculated'])

    def test_uncovered_is_unknown_not_dry(self):
        fields, hazard = fixture()
        hazard['zones'] = hazard['zones'][:1]
        second = overlay(fields, hazard)['synthetic_parcels'][1]
        self.assertEqual(second['outside_support_unknown_area_m2'], 5000)
        self.assertEqual(second['explicit_nodata_area_m2'], 0)

    def test_zero_intensity_is_explicit_dry_coverage(self):
        fields, hazard = fixture()
        hazard['zones'] = [{
            'zone_id': 'SYNTH-ZONE-001', 'intensity': 0, 'nodata': False,
            'geometry': mapping(box(0, 0, 200, 100)),
        }]
        report = overlay(fields, hazard)
        self.assertEqual(report['totals']['observed_synthetic_support_area_m2'], 20000)
        self.assertEqual(report['synthetic_parcels'][0]['intensity_bands'][0]['intensity'], 0.0)

    def test_nodata_and_numeric_overlap_blocks(self):
        fields, hazard = fixture()
        hazard['zones'][2]['geometry'] = mapping(box(100, 0, 180, 100))
        with self.assertRaisesRegex(OverlayError, 'nodata overlaps'):
            overlay(fields, hazard)

    def test_overlapping_parcels_block(self):
        fields, hazard = fixture()
        fields['parcels'][1]['geometry'] = mapping(box(50, 0, 200, 100))
        with self.assertRaisesRegex(OverlayError, 'overlapping fields'):
            overlay(fields, hazard)

    def test_wrong_unit_hail_vs_flood_blocks(self):
        fields, hazard = fixture()
        hazard['peril'] = 'hail'
        with self.assertRaisesRegex(OverlayError, 'unit'):
            overlay(fields, hazard)
        hazard['unit'] = 'mm'
        report = overlay(fields, hazard)
        self.assertEqual(report['intensity_unit'], 'mm')

    def test_nonsynthetic_and_real_source_metadata_block(self):
        fields, hazard = fixture()
        fields['external_source_rows_used'] = 1
        with self.assertRaisesRegex(OverlayError, 'only invented'):
            overlay(fields, hazard)
        fields, hazard = fixture()
        fields['synthetic_only'] = False
        with self.assertRaisesRegex(OverlayError, 'only invented'):
            overlay(fields, hazard)

    def test_duplicate_zone_ids_and_negative_hazard_block(self):
        fields, hazard = fixture()
        hazard['zones'][1]['zone_id'] = hazard['zones'][0]['zone_id']
        with self.assertRaisesRegex(OverlayError, 'duplicate'):
            overlay(fields, hazard)
        fields, hazard = fixture()
        hazard['zones'][0]['intensity'] = -1
        with self.assertRaisesRegex(OverlayError, 'bounded physical'):
            overlay(fields, hazard)

    def test_holes_preserve_polygonal_area(self):
        fields, hazard = fixture()
        fields['parcels'] = fields['parcels'][:1]
        outer_with_hole = Polygon(
            [(0, 0), (100, 0), (100, 100), (0, 100)],
            holes=[[(25, 25), (75, 25), (75, 75), (25, 75)]],
        )
        fields['parcels'][0]['geometry'] = mapping(outer_with_hole)
        hazard['zones'] = hazard['zones'][:1]
        report = overlay(fields, hazard)
        self.assertEqual(report['totals']['total_area_m2'], 7500)
        self.assertEqual(report['totals']['observed_synthetic_support_area_m2'], 7500)

    def test_output_does_not_invent_loss(self):
        fields, hazard = fixture()
        report = overlay(fields, hazard)
        self.assertTrue(report['uncovered_area_is_unknown_not_zero_hazard'])
        self.assertEqual(report['original_source_rows_used'], 0)
        self.assertFalse(report['cat_model_ready'])
        self.assertFalse(report['insurer_tiv_used'])


if __name__ == '__main__':
    unittest.main()
