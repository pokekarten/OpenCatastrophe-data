# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed structural preflight for one frozen PLATEAU CityGML catalogue release.

No HTTP, ZIP downloads, model admissions, per-building output or API authorization.
The input is an independently supplied catalogue JSON file, never a committed
provider fixture. This verifies its declared structure, not provenance or rights.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

TARGET_CITY_CODE = "13104"  # Shinjuku, from the official PLATEAU API documentation
TARGET_YEAR = 2024
# The provider says the unfiltered catalogue normally exceeds 2 MB; this is an
# offline input budget only, distinct from the unapproved 64 KiB network probe
# ceiling in the source access contract. Larger inputs still fail closed.
MAX_INPUT_BYTES = 8 * 1024 * 1024


class CataloguePreflightError(ValueError):
    """Unsafe, ambiguous, or non-target PLATEAU catalogue input."""


def _strict_pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    obj: dict[str, object] = {}
    for key, value in items:
        if key in obj:
            raise CataloguePreflightError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_nonfinite(value: str) -> None:
    raise CataloguePreflightError("non-finite JSON value")


def _year(value: object, label: str) -> int:
    if type(value) is not int or not (2000 <= value <= 2100):
        raise CataloguePreflightError(f"{label} must be a concrete integer fiscal year")
    return value


def _https_url_or_null(value: object, label: str) -> bool:
    """Validate stored metadata links only; a valid URL is not permission to fetch."""
    if value is None:
        return False
    if not isinstance(value, str) or len(value) > 2048:
        raise CataloguePreflightError(f"{label} must be a bounded HTTPS URL or null")
    if any(ch.isspace() or ord(ch) < 32 for ch in value):
        raise CataloguePreflightError(f"{label} contains whitespace or control characters")
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise CataloguePreflightError(f"{label} has malformed URL authority") from exc
    if (
        parsed.scheme != "https" or not host or parsed.username is not None
        or parsed.password is not None or parsed.query or parsed.fragment
        or port not in (None, 443) or not parsed.path.startswith("/")
    ):
        raise CataloguePreflightError(f"{label} must be a public credential-free HTTPS URL without query or fragment")
    if not re.fullmatch(r"[a-z0-9.-]+", host, re.ASCII):
        raise CataloguePreflightError(f"{label} hostname is not canonical ASCII DNS")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if (address is not None and not address.is_global) or host in {"localhost", "localhost."} or host.endswith((".local", ".internal", ".localhost")):
        raise CataloguePreflightError(f"{label} must not target a non-public hostname")
    if any(part in (".", "..") for part in parsed.path.split("/")) or "\\" in parsed.path:
        raise CataloguePreflightError(f"{label} URL path is not canonical")
    return True


def _fixed_composite_url(value: object, *, fiscal_year: int) -> bool:
    """PLATEAU's recommended stable-by-year path must never resolve a latest alias."""
    if value is None:
        return False
    _https_url_or_null(value, "citygml.composite_url")
    parsed = urlsplit(value)
    expected = f"/datacatalog/citygml/{TARGET_CITY_CODE}-{fiscal_year}/citygml.zip"
    if parsed.hostname != "api.plateauview.mlit.go.jp" or parsed.path != expected:
        raise CataloguePreflightError("target composite URL must pin the fixed municipality and fiscal year")
    return True


def _concrete_row(row: object) -> dict[str, object]:
    if not isinstance(row, dict):
        raise CataloguePreflightError("citygml rows must be JSON objects")
    code = row.get("city_code")
    if not isinstance(code, str) or not re.fullmatch(r"\d{5}", code):
        raise CataloguePreflightError("citygml city_code must be five decimal digits")
    if code != TARGET_CITY_CODE:
        return {"city_code": code}
    if row.get("id") != code:
        raise CataloguePreflightError("target dataset ID must equal the city code")
    pref = row.get("pref_code")
    if not isinstance(pref, str) or not re.fullmatch(r"\d{2}", pref) or pref != code[:2]:
        raise CataloguePreflightError("target prefecture code must match city code")
    if not isinstance(row.get("city"), str) or not row["city"].strip():
        raise CataloguePreflightError("target city name is absent")
    year = _year(row.get("year"), "citygml.year")
    registration_year = _year(row.get("registration_year"), "citygml.registration_year")
    spec = row.get("spec")
    if not isinstance(spec, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,39}", spec):
        raise CataloguePreflightError("target PLATEAU spec is absent or malformed")
    types = row.get("feature_types")
    if not isinstance(types, list) or not types or any(
        not isinstance(v, str) or not re.fullmatch(r"[a-z0-9_]{2,32}", v) for v in types
    ) or len(types) != len(set(types)):
        raise CataloguePreflightError("target feature_types malformed or duplicate")
    gspatial = _https_url_or_null(row.get("gspatialjp_dataset_url"), "gspatialjp_dataset_url")
    linked_files = row.get("gspatialjp_files")
    if not isinstance(linked_files, list) or len(linked_files) > 1000:
        raise CataloguePreflightError("target gspatialjp_files must be a bounded array")
    # Provider file_size belongs to the nested gspatialjp_files entries, not
    # the CityGML row. The CMS zip and G-Spatial archive are distinct releases.
    gspatial_citygml_count = 0
    gspatial_citygml_all_sizes_known = True
    for index, item in enumerate(linked_files):
        if not isinstance(item, dict) or item.get("kind") not in {
            "citygml", "3dtiles_mvt", "related", "other",
        }:
            raise CataloguePreflightError("gspatial file kind missing or invalid")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip() or len(name) > 256:
            raise CataloguePreflightError("gspatial file name missing or invalid")
        if not _https_url_or_null(item.get("url"), f"gspatialjp_files[{index}].url"):
            raise CataloguePreflightError("gspatial file URL is required")
        size = item.get("file_size")
        if size is not None and (type(size) is not int or size <= 0 or size > 2**63 - 1):
            raise CataloguePreflightError("gspatial file_size must be a positive signed int64 or null")
        if item["kind"] == "citygml":
            gspatial_citygml_count += 1
            gspatial_citygml_all_sizes_known &= size is not None
    # Do not dereference, copy, download, persist or return any file URL.
    if not _https_url_or_null(row.get("url"), "citygml.url"):
        raise CataloguePreflightError("target original citygml.url is required")
    original_url = urlsplit(row["url"])
    if original_url.hostname == "api.plateauview.mlit.go.jp" and "-latest/" in original_url.path:
        raise CataloguePreflightError("an original source URL cannot be a mutable latest redirect")
    fixed_composite = _fixed_composite_url(row.get("composite_url"), fiscal_year=year)
    return {
        "city_code": code,
        "year": year,
        "registration_year": registration_year,
        "spec": spec,
        "bldg_advertised": "bldg" in types,
        "gspatial_citygml_file_count": gspatial_citygml_count,
        "gspatial_citygml_file_sizes_all_known": bool(gspatial_citygml_count) and gspatial_citygml_all_sizes_known,
        "gspatial_catalogue_page_known": gspatial,
        "fixed_year_composite_url_present": fixed_composite,
    }


def preflight_bytes(raw: bytes) -> dict[str, object]:
    if not 0 < len(raw) <= MAX_INPUT_BYTES:
        raise CataloguePreflightError("input exceeds the bounded metadata size or is empty")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_pairs,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CataloguePreflightError("invalid UTF-8 or JSON") from exc
    if not isinstance(payload, dict):
        raise CataloguePreflightError("catalogue must be a JSON object")
    rows = payload.get("citygml")
    latest = payload.get("latest_citygml")
    if not isinstance(rows, list) or not isinstance(latest, list):
        raise CataloguePreflightError("required citygml and latest_citygml arrays are absent")
    if len(rows) > 10000 or len(latest) > 10000:
        raise CataloguePreflightError("catalogue row budget exceeded")
    matches = []
    for row in rows:
        parsed = _concrete_row(row)
        if parsed["city_code"] == TARGET_CITY_CODE and parsed["year"] == TARGET_YEAR:
            matches.append(parsed)
    if len(matches) != 1:
        raise CataloguePreflightError("expected exactly one frozen Shinjuku 2024 CityGML record")
    mutable_latest_present = False
    for row in latest:
        if not isinstance(row, dict):
            raise CataloguePreflightError("latest_citygml rows must be objects")
        code = row.get("city_code")
        if not isinstance(code, str) or not re.fullmatch(r"\d{5}", code):
            raise CataloguePreflightError("latest_citygml city_code invalid")
        if code == TARGET_CITY_CODE:
            if row.get("year") != "latest":
                raise CataloguePreflightError("target latest_citygml year must be latest")
            mutable_latest_present = True
    candidate = matches[0]
    if not candidate["bldg_advertised"]:
        raise CataloguePreflightError("fixed CityGML release does not advertise bldg features")
    return {
        "source_id": "jp.mlit.plateau.citygml.3d-city-models",
        "target_city_code": TARGET_CITY_CODE,
        "target_fiscal_year": TARGET_YEAR,
        "registration_year": candidate["registration_year"],
        "source_spec": candidate["spec"],
        "bldg_advertised": True,
        "gspatial_citygml_file_count": candidate["gspatial_citygml_file_count"],
        "gspatial_citygml_file_sizes_all_known": candidate["gspatial_citygml_file_sizes_all_known"],
        "gspatial_catalogue_page_known": candidate["gspatial_catalogue_page_known"],
        "fixed_year_composite_url_present": candidate["fixed_year_composite_url_present"],
        "mutable_latest_alias_present_but_not_selected": mutable_latest_present,
        "input_byte_count": len(raw),
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "evidence": "offline_user_supplied_catalogue_structure_only",
        "provider_network_access": False,
        "provider_original_bytes_verified": False,
        "model_input_approved": False,
    }



GRAPHQL_MAX_INPUT_BYTES = 64 * 1024


def preflight_graphql_bytes(raw: bytes) -> dict[str, object]:
    """Inspect a previously supplied, single-city/year GraphQL metadata response.

    No network request or rights assessment is made. The GraphQL native record
    ID is not assumed to equal the city's five-digit administrative code.
    """
    if not 0 < len(raw) <= GRAPHQL_MAX_INPUT_BYTES:
        raise CataloguePreflightError("GraphQL metadata exceeds 64 KiB or is empty")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_pairs,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CataloguePreflightError("invalid UTF-8 or GraphQL JSON") from exc
    if not isinstance(payload, dict):
        raise CataloguePreflightError("GraphQL response must be an object")
    if payload.get("errors"):
        raise CataloguePreflightError("GraphQL errors must not be promoted as source metadata")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise CataloguePreflightError("GraphQL response data must be an object")
    rows = data.get("citygmlDatasets")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise CataloguePreflightError("GraphQL query must return exactly one CityGML row")
    row = rows[0]
    # Keep this projection exactly in sync with the documented
    # CityGMLDataset GraphQL type. Notably it has no fileSize field.
    required_fields = {
        "id", "cityCode", "prefectureCode", "year", "registrationYear",
        "url", "compositeUrl", "featureTypes", "metadataZipUrls",
    }
    if set(row) != required_fields:
        raise CataloguePreflightError("GraphQL CityGML selection is missing documented fields or includes unsupported fields")
    native_id = row["id"]
    if not isinstance(native_id, str) or not native_id.strip() or len(native_id) > 160:
        raise CataloguePreflightError("GraphQL native dataset ID is missing")
    if row["cityCode"] != TARGET_CITY_CODE:
        raise CataloguePreflightError("GraphQL cityCode differs from the pinned municipality")
    if row["prefectureCode"] != TARGET_CITY_CODE[:2]:
        raise CataloguePreflightError("GraphQL prefectureCode differs from the pinned municipality")
    if _year(row.get("year"), "GraphQL year") != TARGET_YEAR:
        raise CataloguePreflightError("GraphQL fiscal year differs from pinned 2024")
    registered_year = _year(row.get("registrationYear"), "GraphQL registrationYear")
    types = row.get("featureTypes")
    if not isinstance(types, list) or not types or any(
        not isinstance(v, str) or not re.fullmatch(r"[a-z0-9_]{2,32}", v)
        for v in types
    ) or len(types) != len(set(types)) or "bldg" not in types:
        raise CataloguePreflightError("GraphQL record must advertise unambiguous bldg features")
    if not _https_url_or_null(row.get("url"), "GraphQL url"):
        raise CataloguePreflightError("GraphQL original CMS URL must be HTTPS")
    if "-latest/" in urlsplit(row["url"]).path:
        raise CataloguePreflightError("GraphQL original URL must not be a latest alias")
    fixed_composite = _fixed_composite_url(row["compositeUrl"], fiscal_year=TARGET_YEAR)
    metadata_zips = row["metadataZipUrls"]
    if not isinstance(metadata_zips, list) or len(metadata_zips) > 100:
        raise CataloguePreflightError("GraphQL metadataZipUrls must be a bounded list")
    for metadata_url in metadata_zips:
        if not _https_url_or_null(metadata_url, "GraphQL metadataZipUrls item"):
            raise CataloguePreflightError("GraphQL metadata zip URL must be HTTPS")
    return {
        "source_id": "jp.mlit.plateau.citygml.3d-city-models",
        "target_city_code": TARGET_CITY_CODE,
        "target_fiscal_year": TARGET_YEAR,
        "registration_year": registered_year,
        "bldg_advertised": True,
        "cms_original_size_metadata_known": False,
        "metadata_zip_link_count": len(metadata_zips),
        "fixed_year_composite_url_present": fixed_composite,
        "input_byte_count": len(raw),
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "evidence": "offline_user_supplied_graphql_structure_only",
        "provider_network_access": False,
        "provider_original_bytes_verified": False,
        "model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="local catalogue JSON supplied separately")
    parser.add_argument(
        "--format", choices=("rest", "graphql"), default="rest",
        help="input metadata format (both use offline-only preflight)",
    )
    args = parser.parse_args(argv)
    try:
        size = args.input.stat().st_size
        max_bytes = GRAPHQL_MAX_INPUT_BYTES if args.format == "graphql" else MAX_INPUT_BYTES
        if not 0 < size <= max_bytes:
            raise CataloguePreflightError("input byte bound exceeded")
        raw = args.input.read_bytes()
        result = preflight_graphql_bytes(raw) if args.format == "graphql" else preflight_bytes(raw)
    except (OSError, CataloguePreflightError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
