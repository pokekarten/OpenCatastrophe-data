# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""AdV LoD2 roof-form code gate for bounded NRW CityJSON exposure diagnostics.

The codes identify *roof form*, not covering material, wind vulnerability,
construction year, code compliance, or a single canonical building roof where
there are several parts. No original provider XML or building rows are stored.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree

ROOF_CODELIST_URL = (
    "https://repository.gdi-de.org/schemas/adv/citygml/Codelisten/"
    "RoofTypeTypeAdV.xml"
)
MAX_CODELIST_BYTES = 16384
_GML = "{http://www.opengis.net/gml}"
_CODE_RE = re.compile(r"[0-9]{4}\Z", re.ASCII)

# Fifteen short, functional code definitions independently checked against
# the original AdV GML Dictionary and AdV LoD1/LoD2 Prüfplan, item 2240.
# The original XML is an external source of truth, not included in this repo.
ROOF_CODES: dict[str, str] = {
    "1000": "Flachdach",
    "2100": "Pultdach",
    "2200": "Versetztes Pultdach",
    "3100": "Satteldach",
    "3200": "Walmdach",
    "3300": "Krüppelwalmdach",
    "3400": "Mansardendach",
    "3500": "Zeltdach",
    "3600": "Kegeldach",
    "3700": "Kuppeldach",
    "3800": "Sheddach",
    "3900": "Bogendach",
    "4000": "Turmdach",
    "5000": "Mischform",
    "9999": "Sonstiges",
}
AMBIGUOUS_ROOF_CODES = frozenset(("5000", "9999"))


class RoofCodeError(ValueError):
    """Code drift, an invalid source value, or unsafe original XML."""


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise RoofCodeError("redirect blocked: fixed official code-list URL required")


def classify(code: object) -> str:
    """Return an exact AdV roof code only, never infer a broader hazard class."""
    if type(code) is not str or code not in ROOF_CODES:
        raise RoofCodeError("unrecognized or malformed AdV roofType code")
    return code


def _code_for_object(item: dict) -> str | None:
    attr = item.get("attributes")
    if attr is None:
        return None
    if not isinstance(attr, dict):
        raise RoofCodeError("invalid CityJSON attributes container")
    if "roofType" not in attr or attr["roofType"] is None:
        return None
    return classify(attr["roofType"])


def audit_cityjson_roof_codes(raw: bytes) -> dict:
    """Summarize only code frequencies and per-root ambiguity, never object IDs."""
    if not isinstance(raw, bytes) or not raw or len(raw) > 65536:
        raise RoofCodeError("invalid bounded CityJSON response")
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RoofCodeError("invalid UTF-8 CityJSON") from exc
    if not isinstance(doc, dict) or doc.get("type") != "CityJSON":
        raise RoofCodeError("not a CityJSON document")
    objs = doc.get("CityObjects")
    if not isinstance(objs, dict) or not objs or len(objs) > 100:
        raise RoofCodeError("invalid or unbounded CityObjects")
    roots = {name: obj for name, obj in objs.items()
             if isinstance(obj, dict) and obj.get("type") == "Building"}
    parts = {name: obj for name, obj in objs.items()
             if isinstance(obj, dict) and obj.get("type") == "BuildingPart"}
    if not roots or len(roots) > 5 or len(roots) + len(parts) != len(objs):
        raise RoofCodeError("unexpected building / part population")
    root_codes, part_codes = Counter(), Counter()
    missing_root, ambiguous_root, specific_root = 0, 0, 0
    multi_code_parts = 0
    part_codes_for_roots: dict[str, set[str]] = {name: set() for name in roots}
    for key, obj in roots.items():
        code = _code_for_object(obj)
        if code is None:
            missing_root += 1
        else:
            root_codes[code] += 1
            if code in AMBIGUOUS_ROOF_CODES:
                ambiguous_root += 1
            else:
                specific_root += 1
    for obj in parts.values():
        code = _code_for_object(obj)
        if code is not None:
            part_codes[code] += 1
        parents = obj.get("parents")
        if not isinstance(parents, list) or len(parents) != 1 or parents[0] not in roots:
            raise RoofCodeError("BuildingPart must have exactly one known parent")
        if code is not None:
            part_codes_for_roots[parents[0]].add(code)
    multi_code_parts = sum(len(codes) > 1 for codes in part_codes_for_roots.values())
    missing_root_with_part_code = sum(
        _code_for_object(root) is None and bool(part_codes_for_roots[name])
        for name, root in roots.items()
    )
    return {
        "roof_code_profile": "oc-adv-roof-type-forms-v0",
        "reference": ROOF_CODELIST_URL,
        "root_buildings": len(roots),
        "building_parts": len(parts),
        "root_roof_code_counts": dict(sorted(root_codes.items())),
        "part_roof_code_counts": dict(sorted(part_codes.items())),
        "root_specific_roof_form": specific_root,
        "root_mixed_or_other_roof_form": ambiguous_root,
        "root_missing_roof_form": missing_root,
        "root_missing_with_part_roof": missing_root_with_part_code,
        "roots_with_multiple_part_roof_codes": multi_code_parts,
        "roof_covering_material_inferred": False,
        "single_building_roof_imputed_from_parts": False,
        "vulnerability_class_assigned": False,
        "insurance_exposure_admitted": False,
    }


def verify_original_ad_v_xml(raw: bytes, *, media_type: str = "text/xml") -> dict:
    """Check the *original* official XML is exactly the reviewed codebook.

    Reject DTD/entities; never persist or print the third-party XML.
    """
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_CODELIST_BYTES:
        raise RoofCodeError("invalid or oversized official code-list response")
    if media_type.split(";", 1)[0].strip().lower() not in {"text/xml", "application/xml"}:
        raise RoofCodeError("unexpected official code-list content type")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise RoofCodeError("DTD/ENTITY prohibited for untrusted XML")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as exc:
        raise RoofCodeError("malformed official XML") from exc
    if root.tag != _GML + "Dictionary":
        raise RoofCodeError("not the official GML Dictionary shape")
    entries = root.findall(".//" + _GML + "Definition")
    codes: dict[str, str] = {}
    for entry in entries:
        names = entry.findall(_GML + "name")
        keyed = [
            name for name in names
            if name.attrib.get("codeSpace") == "http://www.adv-online.de/codespaces"
        ]
        labels = [name for name in names if "codeSpace" not in name.attrib]
        if len(keyed) != 1 or len(labels) != 1:
            raise RoofCodeError("ambiguous official GML code / label")
        code, label = (keyed[0].text or "").strip(), (labels[0].text or "").strip()
        if not _CODE_RE.fullmatch(code) or not label or code in codes:
            raise RoofCodeError("invalid / duplicate official roof code")
        codes[code] = label
    if codes != ROOF_CODES:
        raise RoofCodeError("official code-list drift: require explicit reviewed update")
    return {
        "profile": "oc-adv-roof-codebook-original-byte-attestation-v0",
        "source": ROOF_CODELIST_URL,
        "original_xml_bytes": len(raw),
        "original_xml_sha256": hashlib.sha256(raw).hexdigest(),
        "reviewed_code_count": len(codes),
        "codebook_exact_match": True,
        "raw_xml_embedded": False,
        "vulnerability_mapping_approved": False,
    }


def fetch_official_xml() -> tuple[bytes, str]:
    """Exactly one official HTTPS GET, 16KB maximum, no retry or redirect."""
    req = Request(
        ROOF_CODELIST_URL,
        headers={
            "Accept": "application/xml,text/xml",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-roof-code-source-verifier/0",
        },
        method="GET",
    )
    try:
        with build_opener(_NoRedirects()).open(req, timeout=12) as res:
            if res.status != 200 or res.geturl() != ROOF_CODELIST_URL:
                raise RoofCodeError("unexpected source response or effective URL")
            if res.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise RoofCodeError("unexpected compressed official XML")
            length = res.headers.get("Content-Length")
            if length is not None:
                try:
                    value = int(length)
                except ValueError as exc:
                    raise RoofCodeError("malformed original XML Content-Length") from exc
                if value <= 0 or value > MAX_CODELIST_BYTES:
                    raise RoofCodeError("original XML exceeds byte cap")
            return res.read(MAX_CODELIST_BYTES + 1), res.headers.get("Content-Type", "")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RoofCodeError(f"official XML HTTP failed: {type(exc).__name__}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--verify-official", action="store_true", help="One bounded original XML GET")
    options.add_argument("--offline-xml", help="Synthetic local XML test fixture only")
    args = parser.parse_args(argv)
    try:
        if args.verify_official:
            raw, media = fetch_official_xml()
        else:
            from pathlib import Path
            path = Path(args.offline_xml)
            if path.stat().st_size > MAX_CODELIST_BYTES:
                raise RoofCodeError("XML exceeds byte budget")
            raw, media = path.read_bytes(), "text/xml"
        result = verify_original_ad_v_xml(raw, media_type=media)
        result["live_http_verified"] = bool(args.verify_official)
    except (RoofCodeError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
