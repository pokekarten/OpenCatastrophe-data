# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only TIFF first-4KiB structural parser and STAC consistency tests."""

from __future__ import annotations

from copy import deepcopy
import re
import struct
import unittest

from research_runners.noaa_michael_stac_preflight_v0 import STAC_ROOT
from research_runners.noaa_michael_tiff_header_v0 import TIFFHeaderError, preflight


def item() -> dict:
    tile = "20181011aC0844330w294330n"
    w, s, e, n = -84.7251, 29.6999, -84.6999, 29.7251
    dx, dy = (e - w) / 9340, (n - s) / 9340
    return {
        "type": "Feature", "id": tile, "stac_version": "1.0.0",
        "bbox": [w, s, e, n],
        "geometry": {"type": "Polygon", "coordinates": [
            [[w, s], [w, n], [e, n], [e, s], [w, s]]
        ]},
        "properties": {
            "datetime": "2018-10-11T00:00:00Z",
            "start_datetime": "2018-10-11T00:00:00+00:00",
            "end_datetime": "2018-10-14T00:00:00+00:00",
            "license": "NLPL",
        },
        "assets": {tile: {
            "href": STAC_ROOT + tile + ".tif",
            "type": "image/tiff", "proj:epsg": 4326,
            "proj:shape": [9340, 9340],
            "proj:transform": [w, dx, 0, n, 0, -dy],
            "eo:bands": [{"description": x} for x in ("red", "green", "blue", "alpha")],
            "raster:bands": [{"data_type": "uint8"} for _ in range(4)],
        }},
        "links": [{"rel": "self", "href": STAC_ROOT + "stac/" + tile + ".json"}],
    }


def synthetic_tiff() -> bytes:
    """Construct a valid source-shaped IFD without copying any provider bytes."""
    s = item()["bbox"]
    scale_x, scale_y = (s[2] - s[0]) / 9340, (s[3] - s[1]) / 9340
    tags = [
        (256, 3, [9340]),
        (257, 3, [9340]),
        (258, 3, [8, 8, 8, 8]),
        (259, 3, [8]),
        (262, 3, [2]),
        (277, 3, [4]),
        (284, 3, [1]),
        (306, 2, ["2018:10:11 23:59:59\x00"]),
        (322, 3, [512]),
        (323, 3, [512]),
        (324, 4, [6000] * 361),
        (325, 4, [1000] * 361),
        (338, 3, [2]),
        (33550, 12, [scale_x, scale_y, 0.0]),
        (33922, 12, [0.0, 0.0, 0.0, s[0], s[3], 0.0]),
        (34735, 3, [1, 1, 0, 1, 2048, 0, 1, 4326]),
    ]
    buf = bytearray(4096)
    struct.pack_into("<4sI", buf, 0, b"II*\x00", 8)
    struct.pack_into("<H", buf, 8, len(tags))
    offset = 256
    formats = {3: "H", 4: "I", 12: "d"}
    for i, (tag, typ, values) in enumerate(tags):
        raw = values[0].encode("ascii") if typ == 2 else struct.pack(
            "<" + formats[typ] * len(values), *values
        )
        count = len(raw) if typ == 2 else len(values)
        entry = 10 + i * 12
        if len(raw) <= 4:
            buf[entry:entry + 8] = struct.pack("<HHI", tag, typ, count)
            buf[entry + 8:entry + 12] = raw.ljust(4, b"\x00")
        else:
            struct.pack_into("<HHII", buf, entry, tag, typ, count, offset)
            if offset + len(raw) > len(buf):
                raise AssertionError("synthetic evidence exceeds 4 KiB")
            buf[offset:offset + len(raw)] = raw
            offset += len(raw)
    struct.pack_into("<I", buf, 10 + 12 * len(tags), 0)
    return bytes(buf)


def modify_tag(buf: bytes, tag_id: int, *, new_inline: int | None = None,
               new_count: int | None = None, new_offset: int | None = None) -> bytes:
    data = bytearray(buf)
    count = struct.unpack_from("<H", data, 8)[0]
    for i in range(count):
        pos = 10 + 12 * i
        if struct.unpack_from("<H", data, pos)[0] == tag_id:
            if new_inline is not None:
                struct.pack_into("<I", data, pos + 8, new_inline)
            if new_count is not None:
                struct.pack_into("<I", data, pos + 4, new_count)
            if new_offset is not None:
                struct.pack_into("<I", data, pos + 8, new_offset)
            return bytes(data)
    raise AssertionError("tag absent")


class NOAATIFFHeaderTests(unittest.TestCase):
    def test_synthetic_geotiff_metadata_matches_stac_without_admission(self):
        p = preflight(synthetic_tiff(), item())
        self.assertEqual(p["raster_width_pixels"], 9340)
        self.assertEqual(p["raster_height_pixels"], 9340)
        self.assertEqual(p["tile_block_count"], 361)
        self.assertEqual(p["block_size_pixels"], [512, 512])
        self.assertEqual(p["declared_crs"], "EPSG:4326")
        self.assertEqual(p["tiff_datetime_calendar_day"], "2018-10-11")
        self.assertTrue(p["tiff_datetime_is_end_of_day_marker"])
        self.assertFalse(p["exact_flight_capture_time_verified"])
        self.assertTrue(re.fullmatch(r"[a-f0-9]{64}", p["partial_header_sha256"]))
        for k in ("original_full_file_hash_verified", "asset_identity_bound_by_full_hash",
                  "image_alpha_coverage_measured", "independent_fema_damage_validation_proven",
                  "model_input_admitted"):
            self.assertFalse(p[k])

    def test_header_determinism(self):
        x = synthetic_tiff()
        self.assertEqual(preflight(x, item()), preflight(bytes(bytearray(x)), deepcopy(item())))

    def test_reject_wrong_signature_short_or_big_header(self):
        good = synthetic_tiff()
        for bad in (b"", good[:400], good + b"\x00", b"MM*\x00" + good[4:]):
            with self.subTest(length=len(bad)):
                with self.assertRaisesRegex(TIFFHeaderError, "4096"):
                    preflight(bad, item())

    def test_reject_inconsistent_image_height_and_bits(self):
        for tag, wrong in ((257, 100), (256, 100), (259, 1), (338, 1)):
            with self.subTest(tag=tag):
                with self.assertRaises(TIFFHeaderError):
                    preflight(modify_tag(synthetic_tiff(), tag, new_inline=wrong), item())

    def test_reject_tiff_tile_count_mismatch(self):
        with self.assertRaisesRegex(TIFFHeaderError, "offset/byte-count"):
            preflight(modify_tag(synthetic_tiff(), 324, new_count=360), item())

    def test_reject_date_tag_with_wrong_day_or_missing_tag(self):
        b = bytearray(synthetic_tiff())
        count = struct.unpack_from("<H", b, 8)[0]
        for i in range(count):
            pos = 10 + i * 12
            if struct.unpack_from("<H", b, pos)[0] == 306:
                off = struct.unpack_from("<I", b, pos + 8)[0]
                b[off:off + 10] = b"2018:10:12"
                break
        with self.assertRaisesRegex(TIFFHeaderError, "day differs"):
            preflight(bytes(b), item())
        b = bytearray(synthetic_tiff())
        for i in range(count):
            pos = 10 + i * 12
            if struct.unpack_from("<H", b, pos)[0] == 306:
                struct.pack_into("<H", b, pos, 999)
                break
        with self.assertRaisesRegex(TIFFHeaderError, "required TIFF tag"):
            preflight(bytes(b), item())

    def test_reject_unavailable_array_outside_header(self):
        with self.assertRaisesRegex(TIFFHeaderError, "outside"):
            preflight(modify_tag(synthetic_tiff(), 34735, new_offset=4090), item())

    def test_reject_original_geo_epsg_not_declared(self):
        b = bytearray(synthetic_tiff())
        count = struct.unpack_from("<H", b, 8)[0]
        for i in range(count):
            pos = 10 + i * 12
            if struct.unpack_from("<H", b, pos)[0] == 34735:
                off = struct.unpack_from("<I", b, pos + 8)[0]
                struct.pack_into("<H", b, off + 7 * 2, 3857)
                break
        with self.assertRaisesRegex(TIFFHeaderError, "EPSG"):
            preflight(bytes(b), item())

    def test_reject_pixel_scale_or_bbox_drift(self):
        p = item()
        p["bbox"][0] -= 0.15
        with self.assertRaises(TIFFHeaderError):
            preflight(synthetic_tiff(), p)
        p = item()
        p["assets"][p["id"]]["proj:epsg"] = 3857
        with self.assertRaisesRegex(TIFFHeaderError, "upstream STAC"):
            preflight(synthetic_tiff(), p)

    def test_reject_missing_and_duplicate_ifd_tag(self):
        b = bytearray(synthetic_tiff())
        struct.pack_into("<H", b, 10, 256)
        struct.pack_into("<H", b, 22, 256)
        with self.assertRaisesRegex(TIFFHeaderError, "duplicate"):
            preflight(bytes(b), item())
        b = bytearray(synthetic_tiff())
        struct.pack_into("<H", b, 10, 999)
        with self.assertRaisesRegex(TIFFHeaderError, "required"):
            preflight(bytes(b), item())


if __name__ == "__main__":
    unittest.main()
