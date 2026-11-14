# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One *conditionally* authorized, fixed, 4096-byte JRC source TIFF prefix GET.

The reviewed source policy currently authorizes ZERO CloudFerro requests.
This module does not weaken that policy: no provider request is made unless
both the canonical source contract and the separate host-policy file have
been independently reviewed and explicitly changed to compatible active
states. Offline synthetic tests inject fake HTTP response objects.

Even after an authorized HTTP206, a prefix hash is NEVER a full-file SHA,
a post-2026-11-10 correction proof, a decoded pixel or CAT admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import sys
import tomllib
from urllib import error, request

from scripts.preflight_jrc_gsw_v15_occurrence_header_v0 import (
    JRCHeaderBlocked,
    PREFIX_BYTES,
    SOURCE_ID,
    SOURCE_URL,
    inspect_tiff_prefix,
)
from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "research_runners/policies/jrc_gsw_v15_cloudferro_host_scope_v0.toml"
CONTRACT = ROOT / "access/ec-jrc.global-surface-water.1984-2024.json"
PUBLISHER_URL = "https://global-surface-water.appspot.com/download"
TIMEOUT_SECONDS = 20
FIXED_HEADERS = {
    "Accept": "image/tiff, application/octet-stream",
    "Accept-Encoding": "identity",
    "Cache-Control": "no-cache",
    "Range": f"bytes=0-{PREFIX_BYTES-1}",
    "User-Agent": "OpenCatastrophe-JRC-Reviewed-OneShot/0.1",
}
# Max 18 decimal digits: reject unbounded attacker-supplied HTTP range totals.
CONTENT_RANGE = re.compile(r"bytes 0-4095/([1-9][0-9]{3,17})")


class OriginalPrefixBlocked(ValueError):
    """Source terms, transport bytes or original TIFF evidence not sufficient."""


def authorization_blockers(policy: dict[str, object], contract: dict[str, object]) -> list[str]:
    """Require ALL independent future reviews; never infer rights from a URL.

    The production contract must already have passed validate_path() before
    the provider call. This predicate is intentionally exact. Editing one
    flag never allows the fixed host request to execute.
    """
    blockers: list[str] = []

    def need(ok: bool, label: str) -> None:
        if not ok:
            blockers.append(label)

    need(policy.get("schema_version") == "1.0.0", "canonical policy version")
    need(policy.get("source_id") == SOURCE_ID
         and policy.get("access_id") == SOURCE_ID, "canonical source identity")
    need(policy.get("fixed_tile_url") == SOURCE_URL
         and policy.get("delivery_host") == "s3.waw4-1.cloudferro.com"
         and policy.get("delivery_protocol") == "https", "fixed original source host/path")
    need(policy.get("fixed_product") ==
         "GSW v1.5 1984-2024 corrected 2026-11-10 Occurrence",
         "fixed product identity")
    need(policy.get("public_anonymous_download_permission") == "reviewed_allowed",
         "independently reviewed public anonymous source-asset GET permission")
    rate = policy.get("anonymous_http_rate_cap")
    need(type(rate) is int and rate > 0, "reviewed host rate budget")
    need(type(policy.get("approved_network_requests")) is int
         and policy["approved_network_requests"] == 1, "exactly one approved request")
    need(type(policy.get("approved_original_download_bytes")) is int
         and policy["approved_original_download_bytes"] == PREFIX_BYTES,
         "exact 4096-byte original range budget")
    need(policy.get("live_provider_probe_approved") is True,
         "explicit one-shot live approval")

    need(contract.get("schema_version") == "1.0.0"
         and contract.get("access_id") == SOURCE_ID
         and contract.get("source_ids") == [SOURCE_ID],
         "validated contract/source identity")
    need(contract.get("service_root") == "https://s3.waw4-1.cloudferro.com"
         and contract.get("interface_type") == "object_store",
         "validated exact transport root")
    need(contract.get("status") == "probe_ready",
         "independently reviewed active probe contract")
    auth = contract.get("authentication") or {}
    need(auth.get("mode") == "none"
         and auth.get("credential_reference") is None,
         "explicit anonymous access mode")
    operation = "inspect_fixed_v15_occurrence_tiff"
    probe = contract.get("probe_contract") or {}
    req = contract.get("request_contract") or {}
    need(probe.get("mode") == "provider_specific"
         and probe.get("operation") == operation
         and probe.get("requires_credentials") is False
         and bool(probe.get("expected_evidence")),
         "fixed original TIFF one-shot operation")
    need(operation in req.get("allowed_operations", [])
         and "/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/"
             "occurrence/occurrence_10E_50N_v1_5_2024.tif" in req.get("path_templates", []),
         "fixed TIFF path allowlist")
    rights = contract.get("rights_and_policy") or {}
    need(rights.get("dataset_rights_status") == "verified"
         and rights.get("api_terms_status") == "separate_reviewed"
         and type(rights.get("terms_url")) is str
         and rights.get("terms_url", "").startswith("https://")
         and rights.get("commercial_automation_status") == "allowed",
         "separately reviewed anonymous API/commercial terms")
    limits = contract.get("operational_constraints") or {}
    need(limits.get("retry_policy") == "none"
         and type(limits.get("max_probe_bytes")) is int
         and limits["max_probe_bytes"] >= PREFIX_BYTES,
         "bounded no-retry probe contract")
    return blockers


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _open_fixed(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)


def probe_original_prefix(
    policy: dict[str, object],
    contract: dict[str, object],
    *,
    open_request=_open_fixed,
) -> dict[str, object]:
    """Only one fixed HTTPS range GET, with bounded read and offline TIFF check."""
    blocked = authorization_blockers(policy, contract)
    if blocked:
        raise OriginalPrefixBlocked("source request blocked: " + "; ".join(blocked))
    req = request.Request(SOURCE_URL, method="GET", headers=FIXED_HEADERS)
    try:
        with open_request(req, TIMEOUT_SECONDS) as response:
            if response.status != 206 or response.geturl() != SOURCE_URL:
                raise OriginalPrefixBlocked("requires exact original-host HTTP206, no redirect")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in ("image/tiff", "application/octet-stream"):
                raise OriginalPrefixBlocked("not a native TIFF/octet-stream response")
            if response.headers.get("Content-Encoding", "identity").strip().lower() != "identity":
                raise OriginalPrefixBlocked("encoded/compressed transport response forbidden")
            content_range = response.headers.get("Content-Range", "")
            match = CONTENT_RANGE.fullmatch(content_range.strip())
            if not match or int(match.group(1)) <= PREFIX_BYTES:
                raise OriginalPrefixBlocked("not an exact 4096-byte TIFF range response")
            announced = response.headers.get("Content-Length")
            if announced != str(PREFIX_BYTES):
                raise OriginalPrefixBlocked("missing/incorrect original-range Content-Length")
            # Read no more than the **exact** approved 4096 original bytes.
            # Content-Range and Content-Length already bound this reply.
            prefix = response.read(PREFIX_BYTES)
    except OriginalPrefixBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise OriginalPrefixBlocked("single fixed original CloudFerro range GET failed") from exc
    if type(prefix) is not bytes or len(prefix) != PREFIX_BYTES:
        raise OriginalPrefixBlocked("short/oversized original TIFF range")
    try:
        header = inspect_tiff_prefix(prefix)
    except JRCHeaderBlocked as exc:
        raise OriginalPrefixBlocked("original HTTP206 body not valid bounded TIFF prefix") from exc
    # Return metadata only. The in-memory 4096 bytes are never saved,
    # included in the receipt, or treated as post-correction pixels.
    return {
        **header,
        "profile": "jrc-gsw-v15-original-4096-prefix-reviewed-one-shot-v0",
        "source_id": SOURCE_ID,
        "original_source_range_url": SOURCE_URL,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "http_status": 206,
        "http_content_range": content_range,
        "original_range_bytes_received": PREFIX_BYTES,
        "original_range_sha256": hashlib.sha256(prefix).hexdigest(),
        "exact_source_network_get_count": 1,
        "range_response_verified": True,
        "original_prefix_sha_only_not_full_asset": True,
        "original_asset_whole_file_sha256": None,
        "original_provider_source_identity_verified": True,
        "whole_original_tiff_sha256_verified": False,
        "post_2026_11_10_correction_verified": False,
        "geospatial_crs_and_affine_verified": False,
        "decoded_original_pixels_verified": False,
        "source_downloaded_by_preflight": False,
        "external_source_bytes_persisted_by_preflight": False,
        "model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--one-shot", action="store_true",
                        help="execute only after canonical host policy and source contract review")
    args = parser.parse_args(argv)
    if not args.one_shot:
        parser.error("no source GET by default; explicit --one-shot required")
    try:
        policy = tomllib.loads(POLICY.read_text(encoding="utf-8"))
        contract = validate_path(CONTRACT)
        receipt = probe_original_prefix(policy, contract)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError,
            OriginalPrefixBlocked, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
