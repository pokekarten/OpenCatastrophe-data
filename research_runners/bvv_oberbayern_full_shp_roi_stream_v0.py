#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Stream the one complete original Bavarian HU-BY SHP member, research-only.

Verify full raw-deflate CRC32 + SHA256, exact 2,703,736 source record frames,
and every footprint intersecting the frozen GHSL E2020 32x32 research ROI.
No geodata, source coordinates, individual records or original bytes saved.
No independent 2020 survey vintage or CAT model admission is claimed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import ssl
import struct
import sys
import zlib
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, ProxyHandler, HTTPSHandler, build_opener

from research_runners.by_hausumringe_oberbayern_zip_prefix_v0 import URL, SOURCE, NoRedirect
from research_runners.by_hausumringe_oberbayern_shp_first_original_v0 import (
    START, NAME, ZIP_HEADER_BYTES, COMPRESSED_MEMBER_BYTES,
    UNCOMPRESSED_SHP_BYTES, ORIGINAL_DIRECTORY_CRC32_CLAIM,
)
from research_runners.by_hausumringe_oberbayern_shx_v0 import EXPECTED_SHX_ENTRIES
from research_runners.by_hausumringe_oberbayern_zip_central_v0 import TOTAL, FROZEN
from scripts.verify_ghsl_built_r2023a_native_prefix_v0 import PRODUCTS

SOURCE_PREFIX_SHA256 = "8a3c95bbbca493b192f6923fa4b6060798f561775f647bd34ffd4fc3af316f80"
SOURCE_SHP_HEADER_SHA256 = "f312c12beea148041db5ebf9727ad2aca59e036bef4665aae47402008f02bb09"
SOURCE_SHX_MAX_CONTENT_BYTES = 10284
SOURCE_SHX_MIN_CONTENT_BYTES = 112
WINDOW_GLOBAL_COL_ROW = (22973, 4899)
WINDOW_SIDE = 32
CHUNK = 65536
MAX_BUFFER = 2 * CHUNK + SOURCE_SHX_MAX_CONTENT_BYTES
MAX_PENDING_ROI_FEATURES = 2048  # bounded transient GEOS batch
MAX_ORIGINAL_SEGMENT_BYTES = 8 * 1024 * 1024  # 20 short read-only HTTP 206 requests
READ_BYTES = ZIP_HEADER_BYTES + COMPRESSED_MEMBER_BYTES
END = START + READ_BYTES - 1
RANGE = f"bytes={START}-{END}"
GHSL_SOURCE_EPOCH = 2020


class FullSHPBlocked(ValueError):
    """Original source, complete file or bounded ROI evidence unavailable."""


def frozen_ghsl_bbox():
    s, v = PRODUCTS["surface"], PRODUCTS["volume"]
    if (max(abs(s["origin"][i]-v["origin"][i]) for i in (0, 1)) > 1e-8 or
            max(abs(s["scale"][i]-v["scale"][i]) for i in (0, 1)) > 1e-8):
        raise FullSHPBlocked("original GHSL-S/V study grids differ")
    c, r = WINDOW_GLOBAL_COL_ROW
    x0, y0 = s["origin"]
    dx, dy = s["scale"]
    bbox = (x0+c*dx, y0-(r+WINDOW_SIDE)*dy,
            x0+(c+WINDOW_SIDE)*dx, y0-r*dy)
    if not (11.4 < bbox[0] < bbox[2] < 11.8 and
            47.9 < bbox[1] < bbox[3] < 48.4):
        raise FullSHPBlocked("reviewed JRC study extent drift")
    return bbox


def frozen_roi_geometries():
    """Densify fixed EPSG:4326 cell envelope before projecting to EPSG:25832."""
    try:
        from pyproj import Transformer
        from shapely.geometry import Polygon
    except ImportError as exc:
        raise FullSHPBlocked("pinned PROJ/GEOS required") from exc
    w, s, e, n = frozen_ghsl_bbox()
    tx = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
    side = 32
    path = ([(w+(e-w)*i/side, s) for i in range(side)] +
            [(e, s+(n-s)*i/side) for i in range(side)] +
            [(e-(e-w)*i/side, n) for i in range(side)] +
            [(w, n-(n-s)*i/side) for i in range(side)])
    roi = Polygon([tx.transform(lon, lat) for lon, lat in path])
    if not roi.is_valid or not 100_000_000 < roi.area < 2_000_000_000:
        raise FullSHPBlocked("invalid reprojected GHSL original study ROI")
    return roi, (w, s, e, n)


class NativeSHPStream:
    """Original SHP parser with a fixed-size byte buffer and ROI-only geometries."""

    def __init__(self, *, expected_records=EXPECTED_SHX_ENTRIES,
                 expected_bytes=UNCOMPRESSED_SHP_BYTES,
                 expected_header_sha=SOURCE_SHP_HEADER_SHA256, roi=None):
        self.expected_records = expected_records
        self.expected_bytes = expected_bytes
        self.expected_header_sha = expected_header_sha
        self.roi = roi
        self.bounds = roi.bounds if roi is not None else None
        self.buf = bytearray()
        self.total = self.records = self.shape_polygons = 0
        self.max_original_record_content = 0
        self.roi_bbox_candidates = self.roi_intersecting = 0
        self.roi_invalid_rings = self.roi_invalid_geometries = 0
        self.roi_area_sum = 0.0
        self.roi_clipped_geometries = []
        self.roi_union_levels = []  # binary-carry union, O(log number of batches)
        self.roi_union_batches = 0
        self.sha = hashlib.sha256()
        self.crc = 0
        self.header_seen = False

    def feed(self, block: bytes):
        if type(block) is not bytes or len(block) > CHUNK*4:
            raise FullSHPBlocked("unbounded decoded Shape chunk")
        if self.total + len(block) > self.expected_bytes:
            raise FullSHPBlocked("original Shape length overrun")
        self.total += len(block)
        self.sha.update(block)
        self.crc = zlib.crc32(block, self.crc)
        self.buf.extend(block)
        self._drain()
        if len(self.buf) > MAX_BUFFER:
            raise FullSHPBlocked("streaming source record buffer exceeded")

    def _drain(self):
        if not self.header_seen:
            if len(self.buf) < 100:
                return
            h = bytes(self.buf[:100])
            if self.expected_header_sha is not None and hashlib.sha256(h).hexdigest() != self.expected_header_sha:
                raise FullSHPBlocked("frozen full-stream original SHP header SHA mismatch")
            if (struct.unpack_from(">I", h, 0)[0] != 9994 or
                    any(struct.unpack_from(">5I", h, 4)) or
                    struct.unpack_from(">I", h, 24)[0]*2 != self.expected_bytes or
                    struct.unpack_from("<II", h, 28) != (1000, 5)):
                raise FullSHPBlocked("native original Shapefile header changed")
            x0, y0, x1, y1 = struct.unpack_from("<4d", h, 36)
            if not (all(math.isfinite(k) for k in (x0, y0, x1, y1)) and
                    250000 < x0 < x1 < 950000 and
                    5_000_000 < y0 < y1 < 5_900_000):
                raise FullSHPBlocked("original SHP UTM32 source bbox invalid")
            del self.buf[:100]
            self.header_seen = True
        while len(self.buf) >= 8:
            number, words = struct.unpack_from(">II", self.buf, 0)
            size = words * 2
            if (number != self.records+1 or
                    not SOURCE_SHX_MIN_CONTENT_BYTES <= size <= SOURCE_SHX_MAX_CONTENT_BYTES):
                raise FullSHPBlocked("nonsequential original record or wrong original SHX content-length range")
            if len(self.buf) < size+8:
                break
            body = bytes(self.buf[8:8+size])
            del self.buf[:size+8]
            self.records += 1
            self.max_original_record_content = max(size, self.max_original_record_content)
            self._inspect_record(body)
            if self.records % 250_000 == 0:
                print(f"RESEARCH_PROGRESS native_frames={self.records} roi_candidates={self.roi_bbox_candidates}", flush=True)

    def _inspect_record(self, body: bytes):
        if struct.unpack_from("<I", body, 0)[0] != 5:
            raise FullSHPBlocked("source Shape type not Polygon (5)")
        self.shape_polygons += 1
        xmin, ymin, xmax, ymax = struct.unpack_from("<4d", body, 4)
        if (not all(math.isfinite(k) for k in (xmin, ymin, xmax, ymax))
                or not (250000 < xmin < xmax < 950000
                        and 5_000_000 < ymin < ymax < 5_900_000)):
            raise FullSHPBlocked("original Shape record bbox nonfinite or outside source UTM32 envelope")
        # Validate native geometry framing for EVERY official record, not only
        # bbox candidates. Otherwise a wrong non-ROI part/point frame could
        # be silently counted as a complete original source inventory.
        parts, points = struct.unpack_from("<II", body, 36)
        if (not 1 <= parts <= 128 or not 4 <= points <= 10000
                or len(body) != 44 + 4*parts + 16*points):
            raise FullSHPBlocked("original complete-source Polygon part/point frame invalid")
        offsets = struct.unpack_from("<" + "I"*parts, body, 44)
        if (offsets[0] != 0 or
                any(offsets[i] >= offsets[i+1] for i in range(parts-1))):
            raise FullSHPBlocked("original source Polygon part indices invalid")
        if self.roi is None:
            return
        w, s, e, n = self.bounds
        if xmax < w or xmin > e or ymax < s or ymin > n:
            return
        self.roi_bbox_candidates += 1
        self._inspect_roi(body, (xmin, ymin, xmax, ymax))

    def _inspect_roi(self, body, bbox):
        from shapely.geometry import LinearRing, Polygon, MultiPolygon
        length = len(body)
        if length < 44:
            raise FullSHPBlocked("incomplete original ROI Polygon")
        parts, points = struct.unpack_from("<II", body, 36)
        if not (1 <= parts <= 128 and 4 <= points <= 10000 and
                length == 44+4*parts+16*points):
            raise FullSHPBlocked("native ROI part/point sizes invalid")
        offsets = struct.unpack_from("<"+"I"*parts, body, 44)
        if offsets[0] != 0 or any(offsets[i] >= offsets[i+1] for i in range(parts-1)):
            raise FullSHPBlocked("native ROI ring offset drift")
        starts = tuple(offsets)+(points,)
        rings = []
        x0, y0, x1, y1 = bbox
        for part in range(parts):
            first, last = starts[part], starts[part+1]
            if last-first < 4:
                raise FullSHPBlocked("original ROI ring too short")
            vertices = []
            for i in range(first, last):
                x, y = struct.unpack_from("<dd", body, 44+4*parts+16*i)
                if (not math.isfinite(x) or not math.isfinite(y) or
                        not x0-1e-6 <= x <= x1+1e-6 or
                        not y0-1e-6 <= y <= y1+1e-6):
                    raise FullSHPBlocked("source ROI vertex outside record bbox")
                vertices.append((x, y))
            if vertices[0] != vertices[-1]:
                raise FullSHPBlocked("original ROI ring not closed")
            ring = LinearRing(vertices)
            if not ring.is_valid or not ring.is_simple:
                self.roi_invalid_rings += 1
                raise FullSHPBlocked("original ROI ring topology invalid")
            rings.append(ring)
        shells = [Polygon(r) for r in rings if not r.is_ccw]
        holes = [Polygon(r) for r in rings if r.is_ccw]
        if not shells:
            raise FullSHPBlocked("no ESRI clockwise ROI shell")
        grouped_holes = {i: [] for i in range(len(shells))}
        for hole in holes:
            parents = [(shell.area, i) for i, shell in enumerate(shells) if shell.contains(hole)]
            if not parents:
                raise FullSHPBlocked("ESRI ROI hole without shell")
            grouped_holes[min(parents)[1]].append(list(hole.exterior.coords))
        built = [Polygon(list(shell.exterior.coords), grouped_holes[i])
                 for i, shell in enumerate(shells)]
        geo = built[0] if len(built)==1 else MultiPolygon(built)
        if not geo.is_valid:
            self.roi_invalid_geometries += 1
            raise FullSHPBlocked("original ROI multipolygon topology invalid")
        if geo.intersects(self.roi):
            clipped = geo.intersection(self.roi)
            if not clipped.is_valid:
                raise FullSHPBlocked("original ROI clip invalid")
            self.roi_intersecting += 1
            self.roi_area_sum += clipped.area
            self.roi_clipped_geometries.append(clipped)
            if len(self.roi_clipped_geometries) >= MAX_PENDING_ROI_FEATURES:
                self._flush_roi_union()

    def _flush_roi_union(self):
        """Exact hierarchical GEOS union of bounded 2048-shape batches.

        Each unioned geometry is ephemeral in RAM. The doubling-level
        accumulator avoids retaining every original Polygon and avoids
        repeatedly unioning the entire growing region per source record.
        """
        if not self.roi_clipped_geometries:
            return
        from shapely.ops import unary_union
        combined = unary_union(self.roi_clipped_geometries)
        self.roi_clipped_geometries.clear()
        if not combined.is_valid:
            raise FullSHPBlocked("invalid GEOS union over a native source ROI batch")
        self.roi_union_batches += 1
        level = 0
        while level < len(self.roi_union_levels) and self.roi_union_levels[level] is not None:
            combined = unary_union((combined, self.roi_union_levels[level]))
            self.roi_union_levels[level] = None
            if not combined.is_valid:
                raise FullSHPBlocked("invalid GEOS hierarchical ROI overlap union")
            level += 1
        if level == len(self.roi_union_levels):
            self.roi_union_levels.append(combined)
        else:
            self.roi_union_levels[level] = combined
        if len(self.roi_union_levels) > 24:
            raise FullSHPBlocked("excessive original study union levels")

    def finish(self):
        if (not self.header_seen or self.buf or
                self.records != self.expected_records or self.total != self.expected_bytes):
            raise FullSHPBlocked("full original source records/decoded bytes incomplete")
        result = {
            "profile": "oc-bvv-original-oberbayern-complete-shp-ghsl-roi-v0",
            "source_id": SOURCE,
            "original_full_decoded_shape_bytes": self.total,
            "original_full_decoded_shape_sha256": self.sha.hexdigest(),
            "original_full_decoded_shape_crc32": f"{self.crc:08x}",
            "original_full_native_records_checked": self.records,
            "original_shape_polygons_checked": self.shape_polygons,
            "original_max_content_bytes": self.max_original_record_content,
            "roi_bbox_candidates": self.roi_bbox_candidates,
            "roi_original_polygon_records_intersecting": self.roi_intersecting,
            "roi_invalid_geos_rings": self.roi_invalid_rings,
            "roi_invalid_geos_polygons": self.roi_invalid_geometries,
            "original_source_epoch_is_2020": False,
            "ghsl_source_epoch": 2020,
            "roi_complete_for_this_verified_SHAPE_archive_only": True,
            "original_cadastre_survey_vintage_verified": False,
            "historical_2020_ground_truth_verified": False,
            "ghsl_actual_accuracy_or_tiv_validated": False,
            "source_coordinates_geometries_or_bytes_persisted": False,
            "model_input_approved": False,
        }
        if self.roi is not None:
            from shapely.ops import unary_union
            self._flush_roi_union()
            fragments = [g for g in self.roi_union_levels if g is not None]
            geo = unary_union(fragments) if fragments else None
            if geo is not None and not geo.is_valid:
                raise FullSHPBlocked("invalid final GEOS ROI polygon union")
            union = geo.area if geo is not None else 0.0
            result.update({
                "roi_geos_union_batches_completed": self.roi_union_batches,
                "roi_geos_union_active_levels": len(fragments),
                "projected_utm32_study_roi_area_m2": round(self.roi.area,3),
                "roi_original_polygon_areas_sum_pre_union_m2": round(self.roi_area_sum,3),
                "roi_original_polygon_areas_union_m2": round(union,3),
                "roi_original_polygon_overlap_area_m2": round(self.roi_area_sum-union,3),
                "roi_polygon_count_is_not_number_of_insured_buildings": True,
            })
        self.roi_clipped_geometries.clear()
        self.roi_union_levels.clear()
        return result


class VerifiedOriginalSegmentStream:
    """One contiguous ZIP member assembled only from exact bounded HTTP-206 reads.

    Each segment's HTTP connection closes before its bytes are parsed. This
    prevents a slow GEOS union from starving a long-lived 166-MB response.
    Every source byte is still hashed/CRC-checked in one logical DEFLATE stream;
    no retries, no skips, no reused source offsets, no local file.
    """

    def __init__(self):
        self.next_source_offset = START
        self.active = b""
        self.active_pos = 0
        self.requests_verified = 0
        self.http_bytes_verified = 0
        self.validator_identity = None
        self.all_source_ranges_exact = True

    def _get_segment(self, start: int, end: int):
        """External read-only provider I/O; can be mocked in offline tests."""
        req = Request(URL, method="GET", headers={
            "Range": f"bytes={start}-{end}",
            "Accept-Encoding": "identity",
            "Accept": "application/zip",
            "User-Agent": "OpenCatastrophe-BVV-Exact-Original-SHP-Segmented-ROI/0.2",
        })
        try:
            with build_opener(
                ProxyHandler({}), NoRedirect(),
                HTTPSHandler(context=ssl.create_default_context()),
            ).open(req, timeout=60) as res:
                if res.status != 206 or res.geturl() != URL:
                    raise FullSHPBlocked("original segmented ZIP source ignored HTTP Range or redirected")
                headers = res.headers
                want = end - start + 1
                if headers.get("Content-Range") != f"bytes {start}-{end}/{TOTAL}":
                    raise FullSHPBlocked("source segmented ZIP Content-Range identity changed")
                if headers.get("Content-Length") not in (None, str(want)):
                    raise FullSHPBlocked("source segmented ZIP Content-Length drift")
                if headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise FullSHPBlocked("original segmented source HTTP encoding unexpected")
                if headers.get("Content-Type", "").split(";", 1)[0].strip().lower() not in (
                    "application/zip", "application/octet-stream", "binary/octet-stream"
                ):
                    raise FullSHPBlocked("source segmented ZIP MIME drift")
                # ETag and modification time are cross-request provenance
                # validators; complete original CRC still anchors source.
                validators = (headers.get("ETag"), headers.get("Last-Modified"))
                payload = res.read(want + 1)
        except (HTTPError, URLError, OSError, TimeoutError) as exc:
            raise FullSHPBlocked("fixed original ZIP segmented HTTPS source unavailable") from exc
        if len(payload) != want:
            raise FullSHPBlocked("bounded original ZIP source segment truncated or oversized")
        return payload, validators

    def _next_segment(self):
        if self.next_source_offset > END:
            return False
        start = self.next_source_offset
        end = min(END, start + MAX_ORIGINAL_SEGMENT_BYTES - 1)
        data, validators = self._get_segment(start, end)
        if type(data) is not bytes or len(data) != end - start + 1:
            raise FullSHPBlocked("untrusted original segment size or type")
        if self.validator_identity is None and self.requests_verified == 0:
            self.validator_identity = validators
        elif validators != self.validator_identity:
            raise FullSHPBlocked("original ZIP source ETag/Last-Modified changed across ranges")
        self.requests_verified += 1
        self.http_bytes_verified += len(data)
        self.next_source_offset = end + 1
        self.active = data
        self.active_pos = 0
        return True

    def read(self, amount: int) -> bytes:
        if type(amount) is not int or not 0 < amount <= CHUNK:
            raise FullSHPBlocked("source reader may only request one bounded chunk")
        if self.active_pos >= len(self.active):
            if not self._next_segment():
                return b""
        left = len(self.active) - self.active_pos
        take = min(amount, left)
        out = self.active[self.active_pos:self.active_pos + take]
        self.active_pos += take
        if self.active_pos == len(self.active):
            self.active = b""  # release each original segment before GEOS
            self.active_pos = 0
        return out

    def complete(self) -> bool:
        return (self.next_source_offset == END + 1 and
                self.http_bytes_verified == READ_BYTES and
                not self.active and self.active_pos == 0)


def inspect_original_stream(response, *, status, response_url, headers, roi, verified_segments=False):
    if verified_segments:
        if not isinstance(response, VerifiedOriginalSegmentStream):
            raise FullSHPBlocked("segment trust requires exact verified source reader")
    else:
        if status != 206 or response_url != URL:
            raise FullSHPBlocked("original HTTPS source or Range ignored")
        if headers.get("Content-Range") != f"bytes {START}-{END}/{TOTAL}":
            raise FullSHPBlocked("original content range or full archive size drift")
        if headers.get("Content-Length") not in (None, str(READ_BYTES)):
            raise FullSHPBlocked("original Range response byte length drift")
        if headers.get("Content-Encoding","identity").lower() != "identity":
            raise FullSHPBlocked("unreviewed provider HTTP encoding")
        if headers.get("Content-Type","").split(";",1)[0].strip().lower() not in (
                "application/zip","application/octet-stream","binary/octet-stream"):
            raise FullSHPBlocked("unreviewed original ZIP MIME")
    head = response.read(ZIP_HEADER_BYTES)
    if len(head) != ZIP_HEADER_BYTES or head[:4] != b"PK\x03\x04":
        raise FullSHPBlocked("original ZIP member local header missing")
    version,flags,method,_,__,crc,compressed,uncompressed,name_len,extra = struct.unpack_from(
        "<HHHHHIIIHH", head, 4)
    if (version,flags,method,crc,compressed,uncompressed,name_len,extra) != (
            20,0,8,ORIGINAL_DIRECTORY_CRC32_CLAIM,COMPRESSED_MEMBER_BYTES,
            UNCOMPRESSED_SHP_BYTES,len(NAME),0):
        raise FullSHPBlocked("original ZIP source member coding/size/CRC claim drift")
    if (head[30:ZIP_HEADER_BYTES] != NAME or
            FROZEN["hausumringe.shp"] != (START,COMPRESSED_MEMBER_BYTES,UNCOMPRESSED_SHP_BYTES)):
        raise FullSHPBlocked("reviewed original Shapefile ZIP member identity drift")
    parser = NativeSHPStream(roi=roi)
    inflater = zlib.decompressobj(wbits=-15)
    whole_compressed = hashlib.sha256()
    first_range = hashlib.sha256()
    first_range.update(head)
    first_needed = 49152
    remaining = COMPRESSED_MEMBER_BYTES
    while remaining:
        data = response.read(min(CHUNK, remaining))
        if not data:
            raise FullSHPBlocked("original ZIP Shape range truncated")
        remaining -= len(data)
        whole_compressed.update(data)
        if first_needed:
            size = min(first_needed,len(data))
            first_range.update(data[:size])
            first_needed -= size
        while data:
            decoded = inflater.decompress(data, CHUNK*2)
            parser.feed(decoded)
            data = inflater.unconsumed_tail
            if data and not decoded:
                raise FullSHPBlocked("original Shape DEFLATE parser stalled")
    if first_needed or response.read(1):
        raise FullSHPBlocked("original ZIP Range has missing/extra source bytes")
    if verified_segments and not response.complete():
        raise FullSHPBlocked("original segmented source did not cover every byte exactly once")
    if (not inflater.eof or inflater.unconsumed_tail or inflater.unused_data
            or inflater.flush()):
        raise FullSHPBlocked("original compressed source stream has trailing/invalid frame")
    if first_range.hexdigest() != SOURCE_PREFIX_SHA256:
        raise FullSHPBlocked("original SHA frozen first 49197 provider bytes drift")
    result = parser.finish()
    if result["original_full_decoded_shape_crc32"] != f"{ORIGINAL_DIRECTORY_CRC32_CLAIM:08x}":
        raise FullSHPBlocked("complete original ZIP member CRC32 failure")
    result.update({
        "provider_original_206_segments_verified": (
            response.requests_verified if verified_segments else 1),
        "provider_source_range_mode": (
            "contiguous_exact_206_bounded_segments" if verified_segments else "single_full_206"),
        "source_etag_or_modified_validator_present": (
            any(response.validator_identity) if verified_segments else False),
        "official_source_url": URL,
        "original_member": "hausumringe.shp",
        "exact_source_range": RANGE,
        "full_original_compressed_member_sha256": whole_compressed.hexdigest(),
        "full_original_member_compressed_bytes": COMPRESSED_MEMBER_BYTES,
        "original_partial_first_49197_sha256": first_range.hexdigest(),
        "complete_original_zip_hash_verified": False,
        "official_BVV_HU_BY_CC_BY_4_license_only": True,
        "dataset_atom_rights_todo_marked": True,
        "source_bytes_committed_or_persisted": False,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    return result


def probe():
    roi,_ = frozen_roi_geometries()
    reader = VerifiedOriginalSegmentStream()
    return inspect_original_stream(
        reader, status=None, response_url=None, headers={},
        roi=roi, verified_segments=True,
    )


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live",action="store_true")
    args=parser.parse_args(argv)
    if not args.live:
        parser.error("original 166MB SHP segmented ranges require explicit reviewed-main --live")
    try:
        print(json.dumps(probe(),sort_keys=True,allow_nan=False))
        return 0
    except (FullSHPBlocked,ValueError,OverflowError,OSError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
