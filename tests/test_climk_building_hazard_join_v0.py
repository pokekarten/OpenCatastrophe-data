# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import unittest
from research_runners.climk_building_hazard_join_v0 import join_points


def cell(west,identity,gust):
    return {'geometry':{'coordinates':[[[west,50],[west+1,50],[west+1,51],[west,51],[west,50]]]},
            'properties':{'areaperil_id':identity,'gust_mps':gust,'weather_missing':gust is None}}


def point(identity,x,y=50.5):
    return {'building_id':identity,'longitude':x,'latitude':y}


class BuildingHazardJoinTests(unittest.TestCase):
    def test_shared_edge_has_exactly_one_owner_and_missing_is_not_zero(self):
        rows=join_points([cell(6,1,30),cell(7,2,None)],
                         [point('a',6),point('b',7),point('c',8)])
        self.assertEqual([r['status'] for r in rows],['matched','missing_weather','outside_exported_grid'])
        self.assertEqual([r['areaperil_id'] for r in rows],[1,2,None])
        self.assertIsNone(rows[1]['gust_mps'])
        self.assertEqual(join_points([cell(6,1,0)],[point('calm',6.5)])[0]['status'],'matched')

    def test_duplicate_ids_nonfinite_coordinates_and_overlaps_rejected(self):
        for points in ([point('a',6.2),point('a',6.4)],
                       [point('a',float('nan'))],[point('a',float('inf'))],
                       [point('a',6.5,91)]):
            with self.subTest(points=points),self.assertRaises(ValueError):
                join_points([cell(6,1,30)],points)
        with self.assertRaises(ValueError):
            join_points([cell(6,1,30),cell(6,2,40)],[point('a',6.5)])
