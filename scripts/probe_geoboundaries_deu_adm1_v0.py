# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One bounded geoBoundaries DEU/ADM1 metadata probe; no geometry download.

A successful probe is a connectivity and provenance check, not dataset admission,
a geometry receipt, a current exposure baseline, or an insured-risk model input.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
from typing import Any, Callable
from urllib import error, request
from urllib.parse import urlsplit

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access" / "geoboundaries.gbopen.json"
PROBE_URL = "https://www.geoboundaries.org/api/current/gbOpen/DEU/ADM1/"
EXPECTED_ID = "DEU-ADM1-10402087"
EXPECTED_COMMIT = "9469f09"
EXPECTED_LICENSE = "Data license Germany - Attribution - Version 2.0"
EXPECTED_LICENSE_SOURCE = "www.govdata.de/dl-de/by-2-0"
EXPECTED_SOURCE = "Federal Agency for Cartography and Geodesy"
MAX_RESPONSE_BYTES = 65_536
TIMEOUT_SECONDS = 30
PROFILE = "oc-geoboundaries-deu-adm1-metadata-receipt-v0"
ASSET_NAMES = {
    "staticDownloadLink": "geoBoundaries-DEU-ADM1-all.zip",
    "gjDownloadURL": "geoBoundaries-DEU-ADM1.geojson",
    "tjDownloadURL": "geoBoundaries-DEU-ADM1.topojson",
    "simplifiedGeometryGeoJSON": "geoBoundaries-DEU-ADM1_simplified.geojson",
}
EXPECTED_ASSET_PREFIX = (
    "https://github.com/wmgeolab/geoBoundaries/raw/"
    + EXPECTED_COMMIT + "/releaseData/gbOpen/DEU/ADM1/"
)


class GeoBoundariesProbeError(ValueError):
    """An exact source, response, network or provenance gate was violated."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise GeoBoundariesProbeError("duplicate provider JSON property")
        output[key] = value
    return output


def _reject_constant(value: str) -> None:
    raise GeoBoundariesProbeError("non-finite JSON number in provider metadata")


def verify_frozen_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = validate_path(path)
    if (
        contract["access_id"] != "geoboundaries.gbopen"
        or contract["source_ids"] != ["geoboundaries.gbopen"]
        or contract["interface_type"] != "rest"
        or contract["service_root"] != "https://www.geoboundaries.org"
        or contract["status"] != "probe_ready"
        or contract["authentication"]["mode"] != "none"
        or contract["probe_contract"]["mode"] != "metadata_get"
        or contract["probe_contract"]["operation"] != "deu_adm1_metadata"
        or contract["probe_contract"]["requires_credentials"] is not False
        or contract["request_contract"]["allowed_operations"] != ["deu_adm1_metadata"]
        or contract["request_contract"]["path_templates"] != ["/api/current/gbOpen/DEU/ADM1/"]
        or contract["operational_constraints"]["timeout_seconds"] != TIMEOUT_SECONDS
        or contract["operational_constraints"]["max_probe_bytes"] != MAX_RESPONSE_BYTES
        or contract["rights_and_policy"]["dataset_rights_status"] != "verified"
        or contract["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or contract["rights_and_policy"]["commercial_automation_status"] != "allowed"
    ):
        raise GeoBoundariesProbeError("geoBoundaries contract drift; do not probe")
    return contract


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if type(value) is not str or not value.strip() or len(value) > 2048:
        raise GeoBoundariesProbeError(f"invalid required metadata field: {key}")
    return value


def inspect_metadata(raw: bytes) -> dict[str, Any]:
    """Return a safe fixed-origin metadata subset; never fetch provider asset URLs."""
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_RESPONSE_BYTES):
        raise GeoBoundariesProbeError("empty/oversize geoBoundaries metadata")
    try:
        obj = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GeoBoundariesProbeError("invalid UTF-8 JSON metadata") from exc
    if type(obj) is not dict:
        raise GeoBoundariesProbeError("a single boundary metadata object is required")
    frozen = {
        "boundaryID": EXPECTED_ID,
        "boundaryISO": "DEU",
        "boundaryType": "ADM1",
        "boundaryLicense": EXPECTED_LICENSE,
        "licenseSource": EXPECTED_LICENSE_SOURCE,
        "boundarySource": EXPECTED_SOURCE,
    }
    for key, expected in frozen.items():
        if _required_string(obj, key) != expected:
            raise GeoBoundariesProbeError(f"source identity/licence drift: {key}")

    if _required_string(obj, "boundaryYearRepresented") != "2021":
        raise GeoBoundariesProbeError("boundary represented-year drift")
    if _required_string(obj, "admUnitCount") != "16":
        raise GeoBoundariesProbeError("ADM1 unit-count drift")
    source_update = _required_string(obj, "sourceDataUpdateDate")
    build_date = _required_string(obj, "buildDate")

    urls: dict[str, str] = {}
    for key, filename in ASSET_NAMES.items():
        value = _required_string(obj, key)
        if value != EXPECTED_ASSET_PREFIX + filename:
            raise GeoBoundariesProbeError(f"unreviewed provider asset identity: {key}")
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https" or parsed.hostname != "github.com"
            or parsed.username is not None or parsed.password is not None
            or parsed.port not in (None, 443) or parsed.query or parsed.fragment
        ):
            raise GeoBoundariesProbeError(f"unsafe provider asset link: {key}")
        urls[key] = value

    return {
        "boundary_id": EXPECTED_ID,
        "boundary_iso": "DEU",
        "boundary_type": "ADM1",
        "year_represented": "2021",
        "admin_unit_count": 16,
        "boundary_source": EXPECTED_SOURCE,
        "boundary_license": EXPECTED_LICENSE,
        "license_source": EXPECTED_LICENSE_SOURCE,
        "source_update_date_provider_text": source_update,
        "build_date_provider_text": build_date,
        "asset_commit": EXPECTED_COMMIT,
        "asset_links_evidence_only": urls,
        "asset_bytes_acquired": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GeoBoundariesProbeError("provider redirect is not approved")


def _open(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)


def probe(
    *,
    open_request: Callable[[request.Request, int], Any] = _open,
    utc_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    contract_path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    verify_frozen_contract(contract_path)
    req = request.Request(PROBE_URL, headers={"Accept": "application/json"}, method="GET")
    try:
        with open_request(req, TIMEOUT_SECONDS) as response:
            if response.geturl() != PROBE_URL:
                raise GeoBoundariesProbeError("unexpected provider response URL")
            if type(response.status) is not int or response.status != 200:
                raise GeoBoundariesProbeError("unexpected HTTP response status")
            media_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media_type != "application/json":
                raise GeoBoundariesProbeError("unexpected metadata content type")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except GeoBoundariesProbeError:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise GeoBoundariesProbeError("geoBoundaries exact metadata request failed") from exc

    # Inspect and hash the *same* response bytes, never make a second request
    # that might point at a different mutable /current/ source identity.
    metadata = inspect_metadata(raw)
    checked_at = utc_clock()
    if checked_at.tzinfo is None or checked_at.utcoffset() is None:
        raise GeoBoundariesProbeError("UTC receipt clock must be timezone-aware")
    return {
        "profile": PROFILE,
        "source_id": "geoboundaries.gbopen",
        "access_contract": "access/geoboundaries.gbopen.json",
        "retrieved_at_utc": checked_at.astimezone(timezone.utc).isoformat(),
        "request_url": PROBE_URL,
        "response_media_type": "application/json",
        "response_bytes": len(raw),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "execution_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **metadata,
        "provider_metadata_persisted": False,
        "geometry_imported": False,
        "model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="opt into exactly one reviewed anonymous metadata GET")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("no network request by default: use --live for the fixed metadata canary")
    try:
        print(json.dumps(probe(), sort_keys=True, indent=2, allow_nan=False))
    except (GeoBoundariesProbeError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
