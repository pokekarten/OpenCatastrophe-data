# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Local original US Census TIGER/Line 2026 national COUNTY ZIP preflight.

No download, source-rights admission, model-region assignment, insurer exposure
or topology-completeness claim. Archive hash is observed unless independently
supplied/attested by a separately verified publisher source receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import sys
import zipfile

STEM = "tl_2026_us_county"
EXPECTED = {f"{STEM}.{ext}" for ext in ("shp", "shx", "dbf", "prj", "cpg")}
MANDATORY = {f"{STEM}.{ext}" for ext in ("shp", "shx", "dbf", "prj")}
MAX_ZIP_BYTES = 125_000_000
MAX_MEMBER_BYTES = 350_000_000
MAX_TOTAL_UNPACKED = 600_000_000
MAX_DBF_BYTES = 30_000_000
MAX_RECORDS = 10_000
EXPECTED_SCOPE = "US_CENSUS_TIGER_2026_COUNTY_EQUIVALENTS"
SHA256 = re.compile(r"[a-f0-9]{64}\Z")


class CensusZipError(ValueError):
    pass


def _fail(message):
    raise CensusZipError(message)


def _read_member(archive, name, limit):
    with archive.open(name) as member:
        data = member.read(limit + 1)
    if len(data) > limit:
        _fail("uncompressed member exceeds explicit budget")
    return data


def _shape_header(raw, kind):
    if len(raw) < 100 or struct.unpack(">i", raw[:4])[0] != 9994:
        _fail(f"{kind}: invalid Shapefile code")
    file_length = struct.unpack(">i", raw[24:28])[0] * 2
    if file_length != len(raw):
        _fail(f"{kind}: declared Shapefile length mismatch")
    version, shape_type = struct.unpack("<ii", raw[28:36])
    if version != 1000 or shape_type != 5:
        _fail(f"{kind}: expected exact Polygon shapefile")
    return file_length


def _dbf_summary(raw):
    if len(raw) < 33 or raw[0] not in (3,):
        _fail("DBF: unsupported source layout/version")
    count, header_len, record_len = struct.unpack("<IHH", raw[4:12])
    if not 1 <= count <= MAX_RECORDS or not 33 <= header_len < len(raw):
        _fail("DBF: invalid row count/header")
    if record_len <= 1 or header_len + record_len * count > len(raw):
        _fail("DBF: truncated records")
    if (header_len - 33) % 32 or raw[header_len - 1] != 13:
        _fail("DBF: malformed field descriptors")
    fields = {}
    position = 1
    for offset in range(32, header_len - 1, 32):
        d = raw[offset:offset+32]
        name = d[:11].split(b"\x00", 1)[0].decode("ascii", errors="strict")
        typ, size = d[11], d[16]
        if not name or name in fields or size == 0 or typ != ord("C"):
            # Only the exact ID columns are required to be character strings.
            if name in ("STATEFP", "COUNTYFP", "GEOID", "NAME"):
                _fail("DBF: invalid required string field")
            if not name or name in fields or size == 0:
                _fail("DBF: malformed field schema")
        fields[name] = (position, size, typ)
        position += size
    if position != record_len:
        _fail("DBF: record field widths do not match")
    for key in ("STATEFP", "COUNTYFP", "GEOID", "NAME"):
        if key not in fields or fields[key][2] != ord("C"):
            _fail("DBF: missing/invalid official county identity field")

    def value(record, field):
        start, width, _type = fields[field]
        return record[start:start+width].decode("ascii").strip()

    ids = set()
    orleans = 0
    for i in range(count):
        record = raw[header_len + i * record_len:header_len + (i+1)*record_len]
        if record[:1] != b" ":
            _fail("DBF: deleted record cannot be certified")
        state, county, geoid, name = (value(record, k) for k in
                                      ("STATEFP", "COUNTYFP", "GEOID", "NAME"))
        if (not re.fullmatch(r"[0-9]{2}", state)
            or not re.fullmatch(r"[0-9]{3}", county)
            or geoid != state+county
            or geoid in ids or not name):
            _fail("DBF: repeated or invalid official GEOID/county identity")
        ids.add(geoid)
        if geoid == "22071":
            if state != "22" or county != "071" or name != "Orleans":
                _fail("DBF: Orleans Parish code/name drift")
            orleans += 1
    if orleans != 1:
        _fail("DBF: missing or repeated Orleans Parish official GEOID")
    return count, len(fields)


def audit_original_zip(raw: bytes, *, independently_pinned_sha256=None):
    """Verify archive structure and source identity; no stored/raw geometry output."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_ZIP_BYTES:
        _fail("original Census ZIP is missing or above source byte cap")
    actual = hashlib.sha256(raw).hexdigest()
    if independently_pinned_sha256 is not None:
        if (type(independently_pinned_sha256) is not str or
                SHA256.fullmatch(independently_pinned_sha256) is None or
                actual != independently_pinned_sha256):
            _fail("independent original ZIP SHA-256 mismatch")
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except (zipfile.BadZipFile, OSError) as exc:
        raise CensusZipError("invalid original Census ZIP container") from exc
    with archive:
        info = archive.infolist()
        names = [i.filename for i in info]
        if len(names) != len(set(names)) or not MANDATORY.issubset(names):
            _fail("wrong, duplicate or missing source ZIP files")
        if not set(names).issubset(EXPECTED):
            _fail("extra archive member or path traversal")
        if any(i.is_dir() or i.file_size > MAX_MEMBER_BYTES or
               i.compress_size > MAX_ZIP_BYTES or
               (i.external_attr >> 16) & 0o170000 == 0o120000
               for i in info):
            _fail("unsafe or oversized ZIP member")
        if sum(i.file_size for i in info) > MAX_TOTAL_UNPACKED:
            _fail("total uncompressed archive budget exceeded")
        try:
            shp = _read_member(archive, f"{STEM}.shp", MAX_MEMBER_BYTES)
            shx = _read_member(archive, f"{STEM}.shx", 150_000)
            dbf = _read_member(archive, f"{STEM}.dbf", MAX_DBF_BYTES)
            prj = _read_member(archive, f"{STEM}.prj", 16_384).decode("ascii")
            if f"{STEM}.cpg" in names:
                cpg = _read_member(archive, f"{STEM}.cpg", 512).decode("ascii").strip()
                if not cpg or not re.fullmatch(r"[A-Za-z0-9._ -]{1,80}", cpg):
                    _fail("unexpected character encoding marker")
        except (UnicodeError, RuntimeError, zipfile.BadZipFile) as exc:
            raise CensusZipError("invalid member decoding/CRC") from exc
        _shape_header(shp, "SHP")
        _shape_header(shx, "SHX")
        if ((len(shx)-100) % 8) != 0:
            _fail("SHX: record index length mismatch")
        count, field_count = _dbf_summary(dbf)
        if (len(shx) - 100)//8 != count:
            _fail("SHX/DBF county feature counts disagree")
        if ("GEOGCS" not in prj and "GEOGCRS" not in prj) or not (
                "North_American_1983" in prj or "NAD_1983" in prj):
            _fail("original CRS is not expected NAD83 geographic")
        if "Degree" not in prj and "degree" not in prj:
            _fail("original projected/unknown coordinate units")
    return {
        "profile": "OC_CENSUS_TIGER_2026_COUNTY_ORIGINAL_ZIP_QC_V0",
        "source_scope": EXPECTED_SCOPE,
        "source_zip_bytes": len(raw),
        "source_zip_sha256_observed": actual,
        "sha256_matched_independent_pin": independently_pinned_sha256 is not None,
        "dbf_feature_count": count,
        "shx_index_feature_count": count,
        "dbf_field_count": field_count,
        "orleans_parish_geoid_22071_verified": True,
        "file_header_type": "Polygon",
        "source_crs": "NAD83 geographic (PRJ declaration, no coordinate transform)",
        "complete_polygon_topology_verified": False,
        "countrywide_completeness_verified": False,
        "provider_bytes_persisted": False,
        "insurance_exposure_verified": False,
        "model_input_admitted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--independent-sha256", default=None)
    args = parser.parse_args(argv)
    source = args.source_zip
    if source.is_symlink() or not source.is_file() or source.stat().st_size > MAX_ZIP_BYTES:
        _fail("not a bounded regular original ZIP")
    data = source.read_bytes()
    print(json.dumps(audit_original_zip(
        data, independently_pinned_sha256=args.independent_sha256),
        indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (OSError, CensusZipError) as exc:
        print("BLOCKED:", exc, file=sys.stderr)
        sys.exit(2)
