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
MAX_INPUT_BYTES = 2 * 1024 * 1024


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
    file_size = row.get("file_size")
    if file_size is not None and (type(file_size) is not int or file_size <= 0):
        raise CataloguePreflightError("target file_size must be a positive integer or null")
    gspatial = _https_url_or_null(row.get("gspatialjp_dataset_url"), "gspatialjp_dataset_url")
    if not isinstance(row.get("gspatialjp_files"), list):
        raise CataloguePreflightError("target gspatialjp_files must be an array")
    # Deliberately do not dereference, copy, download, persist or return any file URL.
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
        "provider_file_size_known": file_size is not None,
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
        "provider_file_size_known": candidate["provider_file_size_known"],
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="local catalogue JSON supplied separately")
    args = parser.parse_args(argv)
    try:
        size = args.input.stat().st_size
        if not 0 < size <= MAX_INPUT_BYTES:
            raise CataloguePreflightError("input byte bound exceeded")
        result = preflight_bytes(args.input.read_bytes())
    except (OSError, CataloguePreflightError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
