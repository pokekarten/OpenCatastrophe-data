# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only invented tiny parcel polygons and synthetic OGC cursor links."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlencode

from scripts.assemble_pdok_parcel_pages_v0 import (
    ROOT, ParcelBagError, assemble, main,
)

BBOX = [5.0, 52.0, 5.005, 52.005]
PATH = "https://api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1/collections/perceel/items"


def uri(cursor=None, *, bbox=None, limit=1, host=PATH):
    q = {"bbox": ",".join(map(str, BBOX)) if bbox is None else bbox,
         "f": "json", "limit": str(limit)}
    if cursor is not None:
        q["cursor"] = cursor
    return host + "?" + urlencode(q)


def feature(i, offset=0):
    x, y = 5.0001 + offset, 52.0001
    geom = {"type": "Polygon", "coordinates": [[
        [x, y], [x + .0002, y], [x + .0002, y + .0002],
        [x, y + .0002], [x, y],
    ]]}
    return {"type": "Feature",
            "properties": {"identificatie_lokaal_id": "P" + str(i),
                           "status_historie_waarde": "Geldig"},
            "geometry": geom}


def page(i, self_cursor, next_cursor, *, stamp="2026-11-05T07:00:00Z"):
    links = [{"rel": "self", "href": uri(self_cursor)}]
    if next_cursor is not None:
        links.append({"rel": "next", "href": uri(next_cursor)})
    return {"type": "FeatureCollection", "timeStamp": stamp,
            "links": links, "numberReturned": 1,
            "features": [feature(i, i * .0003)]}


def fixture():
    return [
        page(0, None, "cursor-1"),
        page(1, "cursor-1", None, stamp="2026-11-05T07:00:12Z"),
    ]


class AssemblyTests(unittest.TestCase):
    def test_two_pages_complete_distinct_and_not_admitted(self):
        data = assemble(fixture(), bbox=BBOX, limit=1)
        self.assertEqual(data["numberReturned"], 2)
        self.assertEqual(len(data["features"]), 2)
        self.assertEqual(data["links"], [])
        receipt = data["_research_assembly_receipt"]
        self.assertEqual(receipt["original_page_count"], 2)
        self.assertEqual(receipt["distinct_parcel_features"], 2)
        self.assertTrue(receipt["complete_link_chain_observed"])
        self.assertFalse(receipt["atomic_provider_snapshot_verified"])
        self.assertFalse(receipt["data_rights_or_model_admission_verified"])
        self.assertEqual(receipt["timestamp_gap_seconds"], 12)

    def test_rejects_missing_middle_page_or_still_advertised_next(self):
        with self.assertRaisesRegex(ParcelBagError, "last OGC page still"):
            assemble(fixture()[:1], bbox=BBOX, limit=1)
        files = fixture()
        files[0]["links"] = [files[0]["links"][0]]
        with self.assertRaisesRegex(ParcelBagError, "truncated"):
            assemble(files, bbox=BBOX, limit=1)

    def test_rejects_duplicated_ids_and_wrong_cursor(self):
        pages = fixture()
        pages[1]["features"][0]["properties"]["identificatie_lokaal_id"] = "P0"
        with self.assertRaisesRegex(ParcelBagError, "duplicate parcel ID"):
            assemble(pages, bbox=BBOX, limit=1)
        pages = fixture()
        pages[1]["links"][0]["href"] = uri("other-cursor")
        with self.assertRaisesRegex(ParcelBagError, "broken OGC"):
            assemble(pages, bbox=BBOX, limit=1)

    def test_rejects_external_host_and_bounding_box_or_page_limit_drift(self):
        for malicious_url in (
            uri(host="https://evil.example/ogc/items"),
            uri(bbox="5,52,5.006,52.005"),
            uri(limit=2),
            uri() + "&limit=1",
            uri(host="http://api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1/collections/perceel/items"),
        ):
            with self.subTest(url=malicious_url), self.assertRaises(ParcelBagError):
                pages = fixture()
                pages[0]["links"][0]["href"] = malicious_url
                assemble(pages, bbox=BBOX, limit=1)

    def test_rejects_sensitive_owner_fields_and_invalid_geometry(self):
        pages = fixture()
        pages[0]["features"][0]["properties"]["eigenaar"] = "not_allowed"
        with self.assertRaises(ParcelBagError):
            assemble(pages, bbox=BBOX, limit=1)
        pages = fixture()
        pages[0]["features"][0]["geometry"]["coordinates"][0].pop()
        with self.assertRaises(ParcelBagError):
            assemble(pages, bbox=BBOX, limit=1)

    def test_rejects_one_hour_elapsed_in_paged_api(self):
        pages = fixture()
        pages[1]["timeStamp"] = "2026-11-05T09:00:00Z"
        with self.assertRaisesRegex(ParcelBagError, "more than one hour"):
            assemble(pages, bbox=BBOX, limit=1)

    def test_cli_private_output_and_no_provider_public_bytes(self):
        pages = fixture()
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            inputs = [folder / (str(i) + ".json") for i in range(2)]
            for path, page_json in zip(inputs, pages):
                path.write_text(json.dumps(page_json), encoding="utf-8")
            out = folder / "private-result.json"
            args = ["--pages", str(inputs[0]), str(inputs[1]),
                    "--bbox", ",".join(map(str, BBOX)), "--limit", "1",
                    "--out", str(out)]
            self.assertEqual(main(args), 0)
            self.assertEqual(json.loads(out.read_text())["numberReturned"], 2)
            self.assertEqual(main(args[:-1] + [str(ROOT / "private.json")]), 2)
            self.assertFalse((ROOT / "private.json").exists())

    def test_single_page_complete_without_cursor(self):
        p = page(0, None, None)
        self.assertEqual(assemble([p], bbox=BBOX, limit=1)["numberReturned"], 1)


if __name__ == "__main__":
    unittest.main()
