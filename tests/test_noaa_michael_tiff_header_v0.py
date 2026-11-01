# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only TIFF first-4KiB structural parser and STAC consistency tests."""

from __future__ import annotations

from copy import deepcopy
import re
import struct
import unittest
import zlib

from research_runners.noaa_michael_stac_preflight_v0 import STAC_ROOT
from research_runners.noaa_fema_envelope_overlap_v0 import (
    EnvelopeOverlapError, build_proven_transparent_block_query,
)
from research_runners.noaa_michael_alpha_tile_probe_v0 import (
    AlphaTileProofError, probe_zero_block,
)
from research_runners.noaa_michael_tiff_header_v0 import TIFFHeaderError, preflight, compare_provider_directory_size


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

    def test_original_tiff_main_ifd_can_disprove_directory_size_claim(self):
        # Synthetic IFD with the exact public source block endpoint:
        # current IFD requires at least 67,126,397 bytes while the NOAA
        # public HTML index displays 18.94 MB for this filename.
        h = header_with_tile_payload(360, 1039, offset=67125358)
        report = compare_provider_directory_size(h, item(), 18.94)
        self.assertEqual(report["main_tiff_ifd_minimum_bytes"], 67126397)
        self.assertTrue(report["directory_html_size_insufficient_for_main_ifd"])
        self.assertFalse(report["exact_http_content_length_verified"])
        self.assertFalse(report["original_full_file_sha256_verified"])
        self.assertFalse(report["model_input_admitted"])
        self.assertFalse(report["asset_byte_identity_admitted"])
        self.assertNotIn("source_bytes", report)
        for invalid in (float("nan"), float("inf"), 0, -1, True, "18.94"):
            with self.subTest(value=str(invalid)):
                with self.assertRaises(TIFFHeaderError):
                    compare_provider_directory_size(h, item(), invalid)
        # A *consistent* larger directory claim cannot itself authenticate
        # original bytes, file length or producer identity.
        large = compare_provider_directory_size(h, item(), 70.0)
        self.assertFalse(large["directory_html_size_insufficient_for_main_ifd"])
        self.assertFalse(large["exact_http_content_length_verified"])

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


def header_with_tile_payload(tile_index: int, length: int, offset: int = 64665046) -> bytes:
    """Patch only synthetic IFD tile offset/count cells for a source-sized block."""
    data = bytearray(synthetic_tiff())
    n = struct.unpack_from("<H", data, 8)[0]
    pointers = {}
    for i in range(n):
        p = 10 + 12 * i
        tag = struct.unpack_from("<H", data, p)[0]
        if tag in (324, 325):
            pointers[tag] = struct.unpack_from("<I", data, p + 8)[0]
    if len(pointers) != 2:
        raise AssertionError("synthetic array metadata absent")
    struct.pack_into("<I", data, pointers[324] + 4 * tile_index, offset)
    struct.pack_into("<I", data, pointers[325] + 4 * tile_index, length)
    return bytes(data)


class NOAAOriginalDeflateAlphaTileTests(unittest.TestCase):
    def test_zero_block_exact_source_shape_is_proved_but_not_whole_image(self):
        # The real NOAA center block had the same compressed SHA-256 as
        # zlib.compress(1,048,576 zero bytes, level=6), without copying it.
        comp = zlib.compress(bytes(512 * 512 * 4), level=6)
        self.assertEqual(len(comp), 1039)
        self.assertEqual(
            __import__("hashlib").sha256(comp).hexdigest(),
            "1e6d5d105f8ee78fd7a403adeac8aef4913dc356ac3f66d3ab300309a1ca8a66",
        )
        p = probe_zero_block(header_with_tile_payload(180, len(comp)), item(), 180, comp)
        self.assertEqual(p["block_row"], 9)
        self.assertEqual(p["block_column"], 9)
        self.assertEqual(p["original_compressed_byte_offset"], 64665046)
        self.assertEqual(p["original_compressed_byte_count"], 1039)
        self.assertEqual(p["proven_transparent_pixels_in_this_block_only"], 512 * 512)
        self.assertTrue(p["block_all_alpha_pixels_transparent_proven"])
        for field in ("original_full_file_hash_verified", "other_raster_blocks_covered",
                      "whole_image_alpha_coverage_measured",
                      "source_image_fema_label_independence_proven",
                      "fema_point_pixel_intersection_proven", "model_input_admitted"):
            self.assertFalse(p[field])

    def test_two_source_edge_blocks_are_clipped_not_full_pixel_squares(self):
        # Real NOAA byte-range checks showed original source blocks 18 and
        # 360 match the fully-zero Deflate stream of block 180 byte-for-byte.
        # Synthetic bytes are generated here; no provider pixels committed.
        comp = zlib.compress(bytes(512 * 512 * 4), level=6)
        samples = (
            (18, 26029152, 124 * 512),
            (360, 67125358, 124 * 124),
        )
        counts = []
        for index, offset, expected_visible_extent in samples:
            with self.subTest(index=index):
                h = header_with_tile_payload(index, len(comp), offset=offset)
                report = probe_zero_block(h, item(), index, comp)
                self.assertTrue(report["block_all_alpha_pixels_transparent_proven"])
                self.assertEqual(
                    report["proven_transparent_pixels_in_this_block_only"],
                    expected_visible_extent,
                )
                self.assertEqual(report["original_compressed_byte_offset"], offset)
                self.assertFalse(report["whole_image_alpha_coverage_measured"])
                counts.append(report["proven_transparent_pixels_in_this_block_only"])
        self.assertEqual(sum(counts) + 512 * 512, 341008)

    def test_nonzero_block_not_auto_promoted_to_positive_alpha_pixels(self):
        rgba = bytearray(512 * 512 * 4)
        rgba[3] = 255
        compressed = zlib.compress(rgba)
        p = probe_zero_block(header_with_tile_payload(180, len(compressed)),
                             item(), 180, compressed)
        self.assertFalse(p["decoded_block_all_channels_zero"])
        self.assertFalse(p["block_all_alpha_pixels_transparent_proven"])
        self.assertEqual(p["proven_transparent_pixels_in_this_block_only"], 0)

    def test_corrupt_header_compression_and_tile_index_fail(self):
        comp = zlib.compress(bytes(512 * 512 * 4))
        header = header_with_tile_payload(180, len(comp))
        for bad in (True, -1, 361, 1.2, None):
            with self.subTest(index=bad):
                with self.assertRaises(AlphaTileProofError):
                    probe_zero_block(header, item(), bad, comp)
        with self.assertRaises(AlphaTileProofError):
            probe_zero_block(b"MM" + header[2:], item(), 180, comp)
        with self.assertRaisesRegex(AlphaTileProofError, "byte count"):
            probe_zero_block(header, item(), 180, comp[:-1])

    def test_truncated_corrupt_and_bomb_bounded(self):
        comp = zlib.compress(bytes(512 * 512 * 4))
        broken = b"X" + comp[1:]
        with self.assertRaisesRegex(AlphaTileProofError, "malformed"):
            probe_zero_block(header_with_tile_payload(180, len(broken)),
                             item(), 180, broken)
        excessive = zlib.compress(bytes(512 * 512 * 4 + 1))
        with self.assertRaisesRegex(AlphaTileProofError, "mis-sized"):
            probe_zero_block(header_with_tile_payload(180, len(excessive)),
                             item(), 180, excessive)
        trailing = comp + b"extra"
        with self.assertRaisesRegex(AlphaTileProofError, "excess"):
            probe_zero_block(header_with_tile_payload(180, len(trailing)),
                             item(), 180, trailing)

    def test_source_proven_transparent_tile_builds_only_count_query(self):
        comp = zlib.compress(bytes(512 * 512 * 4), level=6)
        header = header_with_tile_payload(180, len(comp))
        q = build_proven_transparent_block_query(item(), header, 180, comp)
        self.assertEqual(q["original_raster_block_index"], 180)
        self.assertTrue(q["block_fully_transparent_proven"])
        self.assertEqual(q["query"]["where"],
                         "DIS_NUMBER = 'DR-4399' AND ASMT_TYPE = 'RS' AND DMG_TYPE = 'WI'")
        self.assertEqual(q["query"]["inSR"], "4326")
        self.assertEqual(q["query"]["returnCountOnly"], "true")
        self.assertEqual(q["query"]["returnGeometry"], "false")
        bbox = [float(v) for v in q["query"]["geometry"].split(",")]
        source = item()["bbox"]
        expected = [
            source[0] + 4608 * (source[2] - source[0]) / 9340,
            source[3] - 5120 * (source[3] - source[1]) / 9340,
            source[0] + 5120 * (source[2] - source[0]) / 9340,
            source[3] - 4608 * (source[3] - source[1]) / 9340,
        ]
        for a, b in zip(bbox, expected):
            self.assertAlmostEqual(a, b, places=10)
        self.assertFalse(q["independent_fema_label_source_proven"])
        self.assertFalse(q["model_input_admitted"])
        self.assertNotIn("image_bytes", q)
        self.assertNotIn("features", q["query"])

    def test_nonzero_block_cannot_build_proven_transparent_query(self):
        rgba = bytearray(512 * 512 * 4)
        rgba[3] = 1
        compressed = zlib.compress(rgba)
        header = header_with_tile_payload(180, len(compressed))
        with self.assertRaisesRegex(EnvelopeOverlapError, "not proven transparent"):
            build_proven_transparent_block_query(item(), header, 180, compressed)

    def test_unmatched_tile_length_blocks_source_spatial_query(self):
        comp = zlib.compress(bytes(512 * 512 * 4), level=6)
        with self.assertRaisesRegex(EnvelopeOverlapError, "did not pass proof"):
            build_proven_transparent_block_query(
                item(), header_with_tile_payload(180, len(comp) + 1), 180, comp
            )

    def test_tiff_header_does_not_prove_another_asset(self):
        comp = zlib.compress(bytes(512 * 512 * 4))
        wrong = item()
        wrong["assets"][wrong["id"]]["proj:epsg"] = 3857
        with self.assertRaisesRegex(AlphaTileProofError, "header"):
            probe_zero_block(header_with_tile_payload(180, len(comp)),
                             wrong, 180, comp)
        with self.assertRaisesRegex(AlphaTileProofError, "compressed size"):
            probe_zero_block(header_with_tile_payload(180, 1_000_001),
                             item(), 180, comp)


if __name__ == "__main__":
    unittest.main()
