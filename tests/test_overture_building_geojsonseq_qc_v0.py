# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests of source-bounded WGS84 geodesic footprint screening."""
import json
import unittest

from scripts.overture_building_geojsonseq_qc_v0 import (
    RELEASE, GeometryQCError, quality_check,
)

KEY = ('release/2026-10-21.0/theme=buildings/type=building/'
       'part-00000-85375c54-5dfb-57c7-b21d-8b5e5245ad06-c000.zstd.parquet')


def feature(x=6.13, y=49.61, size=.0001):
    return {
        'type': 'Feature',
        'geometry': {'type': 'Polygon',
                     'coordinates': [[[x,y],[x+size,y],[x+size,y+size],
                                      [x,y+size],[x,y]]]},
        'properties': {
            'id': 'fea28f69-7afa-460c-b270-61ef74cd340c',
            'height': 12.0,
            'num_floors': 3,
            'bbox': {'xmin': x, 'ymin': y, 'xmax': x+size, 'ymax': y+size},
            'sources': [{'dataset': 'synthetic-source'}],
        },
    }


def encoded(*rows):
    return ('\n'.join(json.dumps(row, allow_nan=True) for row in rows) + '\n').encode()


def run(*rows):
    return quality_check(encoded(*rows), release=RELEASE, original_s3_key=KEY)


class QualityTests(unittest.TestCase):
    def test_good_area_sq_m_and_non_admission(self):
        out = run(feature())
        self.assertGreater(out['geodesic_area_m2_min'], 50)
        self.assertLess(out['geodesic_area_m2_max'], 150)
        self.assertEqual(out['height_field_present'], 1)
        self.assertEqual(out['floors_field_present'], 1)
        for k in ('input_original_source_bytes_verified', 'original_file_sha256_verified',
                  'gers_registry_identity_approved', 'independent_source_rights_approved',
                  'admitted_model_input', 'insured_value_inferred', 'neon_written'):
            self.assertIs(out[k], False)

    def test_geojsonseq_record_separator(self):
        self.assertEqual(quality_check(b'\x1e' + encoded(feature()), release=RELEASE,
                                       original_s3_key=KEY)['sampled_features'], 1)

    def test_two_different_ids_same_geometry_flagged(self):
        f2 = feature()
        f2['properties']['id'] = 'fae28f69-7afa-460c-b270-61ef74cd340c'
        self.assertEqual(run(feature(), f2)['identical_shape_with_different_id_candidates'], 1)

    def test_different_geometries_not_duplicate(self):
        a, b = feature(), feature(x=6.1303)
        b['properties']['id'] = 'fae28f69-7afa-460c-b270-61ef74cd340c'
        self.assertEqual(run(a,b)['identical_shape_with_different_id_candidates'], 0)

    def test_missing_optional_features(self):
        f = feature()
        for key in ('height','num_floors','sources','bbox'):
            del f['properties'][key]
        out = run(f)
        self.assertEqual((out['height_field_present'], out['floors_field_present'],
                          out['source_lineage_array_present']), (0,0,0))

    def test_reject_wrong_release(self):
        with self.assertRaises(GeometryQCError):
            quality_check(encoded(feature()), release='latest', original_s3_key=KEY)

    def test_reject_foreign_object_key(self):
        with self.assertRaises(GeometryQCError):
            quality_check(encoded(feature()), release=RELEASE,
                          original_s3_key=KEY.replace('type=building', 'type=building_part'))

    def test_reject_invalid_geojson_record(self):
        f=feature();f['type']='Point'
        with self.assertRaises(GeometryQCError):run(f)

    def test_reject_conflicting_feature_ids(self):
        f=feature();f['id']='fae28f69-7afa-460c-b270-61ef74cd340c'
        with self.assertRaises(GeometryQCError):run(f)

    def test_reject_duplicate_ids(self):
        with self.assertRaises(GeometryQCError):run(feature(),feature())

    def test_reject_invalid_polygon(self):
        f=feature();f['geometry']['coordinates'][0][2]=[6.13,49.61]
        with self.assertRaises(GeometryQCError):run(f)

    def test_reject_out_of_range_coordinates(self):
        with self.assertRaises(GeometryQCError):run(feature(x=181))

    def test_reject_bad_height(self):
        f=feature();f['properties']['height']=-4
        with self.assertRaises(GeometryQCError):run(f)

    def test_reject_boolean_floors(self):
        f=feature();f['properties']['num_floors']=True
        with self.assertRaises(GeometryQCError):run(f)

    def test_reject_wrong_bbox(self):
        f=feature();f['properties']['bbox']['xmin']=0
        with self.assertRaises(GeometryQCError):run(f)

    def test_reject_source_without_dataset(self):
        f=feature();f['properties']['sources']=[{'provider':'not-dataset'}]
        with self.assertRaises(GeometryQCError):run(f)

    def test_reject_unsafe_private_feature(self):
        f=feature();f['insured_value']=123
        with self.assertRaises(GeometryQCError):run(f)

    def test_reject_private_props(self):
        f=feature();f['properties']['insurer_account']='TOP-SECRET'
        with self.assertRaises(GeometryQCError):run(f)

    def test_reject_empty_file(self):
        with self.assertRaises(GeometryQCError):
            quality_check(b'',release=RELEASE,original_s3_key=KEY)

    def test_reject_more_than_64(self):
        with self.assertRaises(GeometryQCError):run(*(feature() for _ in range(65)))

    def test_reject_duplicate_json_key(self):
        raw=b'{"type":"Feature","type":"Feature","geometry":{},"properties":{}}\n'
        with self.assertRaises(GeometryQCError):
            quality_check(raw,release=RELEASE,original_s3_key=KEY)

    def test_reject_nonfinite_coordinates(self):
        f=feature();f['geometry']['coordinates'][0][0][0]=float('nan')
        with self.assertRaises(GeometryQCError):run(f)

    def test_reject_wide_polygon(self):
        with self.assertRaises(GeometryQCError):run(feature(size=.5))

    def test_reject_bogus_uuid(self):
        f=feature();f['properties']['id']='NO-UUID'
        with self.assertRaises(GeometryQCError):run(f)

    def test_reject_wrong_geometry_type(self):
        f=feature();f['geometry']={'type':'Point','coordinates':[6.13,49.61]}
        with self.assertRaises(GeometryQCError):run(f)

    def test_reject_bad_bbox_type(self):
        f=feature();f['properties']['bbox']['xmin']=True
        with self.assertRaises(GeometryQCError):run(f)


    def test_wgs84_area_varies_with_latitude(self):
        low = run(feature(x=6.13, y=5.0))['geodesic_area_m2_median']
        high = run(feature(x=6.13, y=75.0))['geodesic_area_m2_median']
        self.assertGreater(low, high * 3)

    def test_polygon_hole_subtracts_geodesic_area(self):
        outer = feature()
        holed = feature()
        ring = [[6.13002, 49.61002], [6.13008, 49.61002],
                [6.13008, 49.61008], [6.13002, 49.61008], [6.13002, 49.61002]]
        holed['geometry']['coordinates'].append(ring)
        self.assertLess(run(holed)['geodesic_area_m2_max'],
                        run(outer)['geodesic_area_m2_max'])

    def test_multipolygon_geodesic_area(self):
        f = feature()
        first = f['geometry']['coordinates']
        second = feature(x=6.131)['geometry']['coordinates']
        f['geometry'] = {'type': 'MultiPolygon', 'coordinates': [first, second]}
        del f['properties']['bbox']
        self.assertGreater(run(f)['geodesic_area_m2_min'],
                           run(feature())['geodesic_area_m2_min'] * 1.9)


if __name__ == '__main__':
    unittest.main()
