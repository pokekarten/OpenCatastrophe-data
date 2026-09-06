# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire the two frozen CEMS Europe v3.1.1 companion masks as receipt-only evidence."""

from __future__ import annotations

import hashlib
import ssl
import time
import urllib.parse
import urllib.request
from typing import Any, Callable

try:
    from scripts import acquire_cems_europe_rp10_receipt as _base
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_cems_europe_rp10_receipt as _base

SCHEMA_VERSION = "oc-cems-europe-mask-receipts-v1"
RECEIPT_SCHEMA_VERSION = "oc-cems-europe-mask-receipt-v1"
SOURCE_ISSUE = 809
DATASET_ID = _base.DATASET_ID
RELEASE = _base.RELEASE
RELEASE_DATE = _base.RELEASE_DATE
DOI = _base.DOI
EXPECTED_HOST = _base.EXPECTED_HOST
BASE_URL = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/"
ASSETS = (
    ("permanent_water", "Europe_permanent_water_bodies.tif"),
    ("spurious_depth", "Europe_spurious_depth_areas.tif"),
)
ALLOWED_URLS = frozenset(BASE_URL + filename for _kind, filename in ASSETS)


class CemsMaskReceiptError(RuntimeError):
    """Raised when either frozen mask receipt cannot be produced fail-closed."""


def _safe_source_url(url: str) -> bool:
    if type(url) is not str or url not in ALLOWED_URLS:
        return False
    parsed = urllib.parse.urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname == EXPECTED_HOST
        and parsed.username is None
        and parsed.password is None
        and parsed.port in (None, 443)
        and parsed.query == ""
        and parsed.fragment == ""
    )


def _open_frozen_source(request: urllib.request.Request, timeout: float):
    """Open exactly one of the two frozen mask GETs on the reviewed CEMS transport."""
    if (
        request.get_method() != "GET"
        or request.data is not None
        or not _safe_source_url(request.full_url)
        or timeout <= 0
    ):
        raise CemsMaskReceiptError("frozen CEMS mask source identity is invalid")

    parsed = urllib.parse.urlsplit(request.full_url)
    connection = _base.PublicOnlyHTTPSConnection(
        EXPECTED_HOST,
        443,
        timeout=timeout,
        context=ssl.create_default_context(),
    )
    response = None
    try:
        connection.request(
            "GET",
            parsed.path,
            headers={
                "Accept": "image/tiff, application/octet-stream",
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
        )
        response_socket = connection.sock
        if response_socket is None:
            raise CemsMaskReceiptError("trusted CEMS mask connection failed")
        response = connection.response_class(response_socket, method="GET")
        response.begin()
        if response._oc_response_socket is not response_socket:
            raise CemsMaskReceiptError("CEMS mask response cannot enforce the total deadline")
        connection.sock = None
        response.url = request.full_url
        return response
    except Exception:
        if response is not None:
            response.close()
        connection.close()
        raise


def _acquire_one(
    kind: str,
    filename: str,
    *,
    opener: Callable[[urllib.request.Request, float], Any],
    clock: Callable[[], str],
    monotonic: Callable[[], float],
) -> dict[str, Any]:
    source_url = BASE_URL + filename
    if not _safe_source_url(source_url):
        raise CemsMaskReceiptError("frozen CEMS mask source identity is invalid")

    deadline = monotonic() + _base.TOTAL_DEADLINE_SECONDS
    request = urllib.request.Request(
        source_url,
        method="GET",
        headers={"Accept": "image/tiff, application/octet-stream", "Accept-Encoding": "identity"},
    )
    try:
        response_cm = opener(request, _base._remaining(deadline, monotonic))
        with response_cm as response:
            if type(response.status) is not int or response.status != 200:
                raise CemsMaskReceiptError("CEMS mask response status is not exact HTTP 200")
            final_url = response.geturl()
            if type(final_url) is not str or final_url != source_url:
                raise CemsMaskReceiptError("CEMS mask final URL drifted from frozen source identity")
            encoding = response.headers.get("Content-Encoding")
            if encoding not in (None, "", "identity"):
                raise CemsMaskReceiptError("CEMS mask response used unexpected content encoding")
            media_raw = response.headers.get("Content-Type")
            if type(media_raw) is not str:
                raise CemsMaskReceiptError("CEMS mask response media type is missing")
            media_type = media_raw.split(";", 1)[0].strip().lower()
            if media_type not in _base.ALLOWED_MEDIA_TYPES:
                raise CemsMaskReceiptError("CEMS mask response media type is outside the fixed contract")
            declared_length = _base._parse_content_length(response.headers.get("Content-Length"))

            digest = hashlib.sha256()
            byte_count = 0
            prefix = bytearray()
            while True:
                remaining = _base._remaining(deadline, monotonic)
                _base._set_response_timeout(response, remaining)
                chunk = response.read(_base.CHUNK_SIZE)
                _base._remaining(deadline, monotonic)
                if not chunk:
                    break
                if type(chunk) is not bytes:
                    raise CemsMaskReceiptError("CEMS mask stream returned non-byte content")
                byte_count += len(chunk)
                if byte_count > _base.MAX_BYTES:
                    raise CemsMaskReceiptError("CEMS mask asset exceeded bounded byte size")
                if len(prefix) < 4:
                    prefix.extend(chunk[: 4 - len(prefix)])
                digest.update(chunk)

            if byte_count == 0:
                raise CemsMaskReceiptError("CEMS mask asset was empty")
            if declared_length is not None and byte_count != declared_length:
                raise CemsMaskReceiptError("CEMS mask byte count disagrees with Content-Length")
            if bytes(prefix) not in _base._TIFF_SIGNATURES:
                raise CemsMaskReceiptError("CEMS mask payload lacks a TIFF/BigTIFF signature")
    except CemsMaskReceiptError:
        raise
    except Exception as exc:
        raise CemsMaskReceiptError("CEMS mask acquisition failed") from exc

    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "source_issue": SOURCE_ISSUE,
        "release": RELEASE,
        "release_date": RELEASE_DATE,
        "doi": DOI,
        "mask_kind": kind,
        "filename": filename,
        "requested_url": source_url,
        "final_url": source_url,
        "retrieved_at": clock(),
        "http_status": 200,
        "media_type": media_type,
        "content_length_header": declared_length,
        "byte_count": byte_count,
        "sha256": digest.hexdigest(),
        "external_bytes_persisted": False,
        "geotiff_semantics_verified": False,
        "mask_values_inspected": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def acquire_cems_mask_receipts(
    *,
    opener: Callable[[urllib.request.Request, float], Any] = _open_frozen_source,
    clock: Callable[[], str] = _base.utc_now,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Acquire both frozen companion masks in fixed order and retain receipt metadata only."""
    receipts = [
        _acquire_one(kind, filename, opener=opener, clock=clock, monotonic=monotonic)
        for kind, filename in ASSETS
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "source_issue": SOURCE_ISSUE,
        "release": RELEASE,
        "receipts": receipts,
        "external_bytes_persisted": False,
        "geotiff_semantics_verified": False,
        "mask_values_inspected": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
