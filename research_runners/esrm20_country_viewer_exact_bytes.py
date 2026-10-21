#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Compare the official ESRM20 viewer download against frozen v1.0 bytes.

This is a separate, bounded *byte-provenance* diagnostic for #778. Reuse the
existing source-bound Project 269 acquisition worker; do not replace its
canonical receipt or widen its admission. Fetch only the Country Viewer's
fixed legacy result URL, follow same-host redirects, and prove the received
octets equal the frozen v1.0 country-risk object. Neither payload is persisted
or returned; loss/reference semantics and model/publication authority remain
unverified even after byte equality.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from typing import Any

from research_runners import esrm20_country_viewer_provenance as provenance
from scripts import acquire_efehr_esrm20_country_risk_receipt as country

SCHEMA_VERSION = "oc-esrm20-country-viewer-exact-bytes-v1"
MAX_VIEWER_BYTES = 8192


class ViewerExactBytesError(RuntimeError):
    """The bounded viewer-to-frozen-byte identity could not be established."""


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(payload)).encode("ascii") + b"\x00" + payload
    ).hexdigest()


def compare_viewer_to_frozen(
    *,
    viewer_payload: bytes,
    viewer_final_url: str,
    frozen_payload: bytes,
    frozen_receipt: dict[str, Any],
) -> dict[str, Any]:
    """Compare two independently acquired octet streams without exposing rows."""

    if (
        type(viewer_payload) is not bytes
        or not viewer_payload
        or len(viewer_payload) > MAX_VIEWER_BYTES
        or type(frozen_payload) is not bytes
        or not frozen_payload
        or len(frozen_payload) > MAX_VIEWER_BYTES
    ):
        raise ViewerExactBytesError("source payloads exceed bounded byte policy")
    if not provenance._is_canonical_viewer_raw_url(viewer_final_url):
        raise ViewerExactBytesError("viewer body did not come from canonical main raw path")

    if (
        type(frozen_receipt) is not dict
        or frozen_receipt.get("project_id") != country.PROJECT_ID
        or frozen_receipt.get("project_path") != country.PROJECT_PATH
        or frozen_receipt.get("commit_sha") != provenance.FROZEN_V10_COMMIT
        or frozen_receipt.get("repository_path") != provenance.COUNTRY_RISK_PATH
        or frozen_receipt.get("byte_count") != provenance.FROZEN_V10_BYTE_COUNT
        or frozen_receipt.get("sha256") != provenance.FROZEN_V10_SHA256
        or frozen_receipt.get("external_bytes_persisted") is not False
    ):
        raise ViewerExactBytesError("frozen source receipt is not trusted v1.0 identity")

    frozen_sha = hashlib.sha256(frozen_payload).hexdigest()
    if (
        len(frozen_payload) != provenance.FROZEN_V10_BYTE_COUNT
        or frozen_sha != provenance.FROZEN_V10_SHA256
        or _git_blob_sha1(frozen_payload) != provenance.FROZEN_V10_BLOB_SHA1
    ):
        raise ViewerExactBytesError("frozen source payload differs from trusted receipt")

    viewer_sha = hashlib.sha256(viewer_payload).hexdigest()
    viewer_blob = _git_blob_sha1(viewer_payload)
    byte_equal = (
        viewer_payload == frozen_payload
        and len(viewer_payload) == provenance.FROZEN_V10_BYTE_COUNT
        and viewer_sha == provenance.FROZEN_V10_SHA256
        and viewer_blob == provenance.FROZEN_V10_BLOB_SHA1
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "VERIFIED" if byte_equal else "BLOCKED",
        "viewer_requested_url": provenance.LEGACY_VIEWER_RAW_URL,
        "viewer_final_url": viewer_final_url,
        "frozen_source_commit": provenance.FROZEN_V10_COMMIT,
        "frozen_source_path": provenance.COUNTRY_RISK_PATH,
        "viewer_byte_count": len(viewer_payload),
        "viewer_sha256": viewer_sha,
        "viewer_git_blob_sha1": viewer_blob,
        "viewer_bytes_match_frozen_v10": byte_equal,
        "provider_rows_returned": False,
        "provider_numeric_values_interpreted": False,
        "external_bytes_persisted": False,
        "denominator_semantics_verified": False,
        "threshold_compatibility_verified": False,
        "annualization_semantics_verified": False,
        "reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _acquire_viewer_body() -> tuple[bytes, str]:
    # The already-reviewed redirect handler rejects non-HTTPS, wrong host, ports,
    # credentials and URL fragments at every redirect step.
    redirects = provenance._RedirectRecorder()
    opener = urllib.request.build_opener(redirects)
    request = urllib.request.Request(
        provenance.LEGACY_VIEWER_RAW_URL,
        method="GET",
        headers={
            "User-Agent": "OpenCatastrophe-data ESRM20 viewer byte diagnostic",
            "Cache-Control": "no-cache",
            "Accept": "application/octet-stream,text/csv,text/plain",
        },
    )
    with opener.open(request, timeout=45) as response:
        if getattr(response, "status", 200) != 200:
            raise ViewerExactBytesError("viewer GET did not return HTTP 200")
        final_url = response.geturl()
        if not provenance._is_canonical_viewer_raw_url(final_url):
            raise ViewerExactBytesError("viewer GET did not resolve to canonical file")
        payload = response.read(MAX_VIEWER_BYTES + 1)
    if not payload or len(payload) > MAX_VIEWER_BYTES:
        raise ViewerExactBytesError("viewer GET body exceeds bounded byte policy")
    return payload, final_url


def run() -> dict[str, Any]:
    viewer_payload, viewer_final_url = _acquire_viewer_body()
    frozen_receipt, frozen_payload = country.acquire_country_risk_receipt_with_payload()
    return compare_viewer_to_frozen(
        viewer_payload=viewer_payload,
        viewer_final_url=viewer_final_url,
        frozen_payload=frozen_payload,
        frozen_receipt=frozen_receipt,
    )


def main() -> int:
    try:
        result = run()
    except (
        ViewerExactBytesError,
        provenance.ViewerProvenanceError,
        country.Esrm20CountryRiskReceiptError,
        OSError,
        urllib.error.URLError,
    ) as exc:
        # No provider bytes, row literals, network error text or redirects in
        # the durable error surface.
        print(json.dumps({
            "schema_version": SCHEMA_VERSION,
            "status": "BLOCKED",
            "failure_kind": type(exc).__name__,
            "external_bytes_persisted": False,
            "reference_loss_agreement_verified": False,
            "model_use_authorized": False,
        }, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
