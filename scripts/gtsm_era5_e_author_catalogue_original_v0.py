# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Ephemeral, two-pinned-original GTSM author catalogue identity probe.

Zenodo NetCDF and the author GitHub catalogue remain ephemeral. Output only
aggregate overlap counts, never original IDs, station names or positions.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from gtsm_era5_e_author_catalogue_overlap_v0 import (
    AuthorCatalogueAuditBlocked, compare_original_to_author_catalogue,
    parse_author_catalogue, audit_hypothetical_100_id_batches,
)
from gtsm_era5_e_author_family_return_qa_v0 import (
    audit_return_levels_by_author_name_family,
    read_pinned_original_return_matrices,
    GtsmFamilyReturnAuditBlocked, COUNTER_FIELDS,
    require_verified_author_station_join,
)
from gtsm_era5_e_original_receipt_v0 import (
    GtsmReceiptError, PINNED_SHA256, SOURCE_BYTES, SOURCE_DOWNLOAD_URL,
    SOURCE_NAME, _ZenodoOnlyRedirect, verify_original,
)

AUTHOR_GITHUB_COMMIT = "30580a729be88fea8bf5b4e813b39e381ad9e2f4"
AUTHOR_CATALOGUE_GIT_BLOB_SHA1 = "07c784f401a1296bea15e7bfbd10332065dc3732"
AUTHOR_CATALOGUE_URL = (
    "https://raw.githubusercontent.com/VU-IVM/gtsm3-era5-nrt/"
    + AUTHOR_GITHUB_COMMIT + "/04_supplementary_data/GTSM_output_locations_list.csv"
)
AUTHOR_BYTES_MAX = 25_000_000
CHUNK = 256 * 1024


class AuthorCatalogueRedirect(HTTPRedirectHandler):
    """Avoid silently reading another host's file in a source-verifying job."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        result = urlsplit(newurl)
        if (result.scheme != "https" or result.hostname != "raw.githubusercontent.com"
                or result.port not in (None, 443)):
            raise AuthorCatalogueAuditBlocked("author catalogue HTTPS host redirect changed")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def get_author_original_csv() -> tuple[str, int]:
    """Download fixed author commit; reject changes against GitHub's blob hash."""
    req = Request(AUTHOR_CATALOGUE_URL, headers={
        "User-Agent": "OpenCatastrophe-Author-GTSM-Research/1.0",
    })
    with build_opener(AuthorCatalogueRedirect()).open(req, timeout=90) as response:
        final = urlsplit(response.geturl())
        if (response.status != 200 or final.scheme != "https"
                or final.hostname != "raw.githubusercontent.com"):
            raise AuthorCatalogueAuditBlocked("original author catalogue unavailable at fixed host")
        raw_size = response.headers.get("Content-Length")
        if raw_size is not None and (
            not raw_size.isdecimal() or int(raw_size) > AUTHOR_BYTES_MAX
        ):
            raise AuthorCatalogueAuditBlocked("original author catalogue is larger than fixed budget")
        payload = bytearray()
        while True:
            chunk = response.read(min(CHUNK, AUTHOR_BYTES_MAX + 1 - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
            if len(payload) > AUTHOR_BYTES_MAX:
                raise AuthorCatalogueAuditBlocked("fixed author catalogue download exceeds size cap")

    blob_prefix = ("blob " + str(len(payload)) + "\0").encode("ascii")
    git_blob_sha1 = hashlib.sha1(blob_prefix + payload).hexdigest()  # nosec B324: Git blob identity
    if not hmac.compare_digest(git_blob_sha1, AUTHOR_CATALOGUE_GIT_BLOB_SHA1):
        raise AuthorCatalogueAuditBlocked("original author catalogue differs from fixed Git blob")
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AuthorCatalogueAuditBlocked("author catalogue is not UTF-8 text") from exc
    return text, len(payload)


def fetch_verified_statistical_original(destination: Path) -> None:
    """One fixed 9,652,424-byte Zenodo file, with source-host restrictions."""
    req = Request(SOURCE_DOWNLOAD_URL, headers={
        "User-Agent": "OpenCatastrophe-Author-GTSM-Research/1.0",
    })
    with build_opener(_ZenodoOnlyRedirect()).open(req, timeout=90) as response:
        final = urlsplit(response.geturl())
        if (response.status != 200 or final.scheme != "https"
                or final.hostname != "zenodo.org"):
            raise GtsmReceiptError("pinned GTSM original source-host check failed")
        size = response.headers.get("Content-Length")
        if size is not None and (not size.isdecimal() or int(size) != SOURCE_BYTES):
            raise GtsmReceiptError("source Zenodo NetCDF size not pinned")
        total = 0
        with destination.open("xb") as output:
            while True:
                data = response.read(min(CHUNK, SOURCE_BYTES + 1 - total))
                if not data:
                    break
                total += len(data)
                if total > SOURCE_BYTES:
                    raise GtsmReceiptError("source original NetCDF exceeds fixed cap")
                output.write(data)
        if total != SOURCE_BYTES:
            raise GtsmReceiptError("source original NetCDF has unexpected file length")


def read_original_native_id_coordinates(path: Path) -> tuple[list[int], list[int], list[int]]:
    """Called only after the fixed original digest and native-header checks."""
    try:
        from netCDF4 import Dataset
        with Dataset(path.as_posix(), "r") as dataset:
            source = []
            for name, native in (
                ("stations", "uint16"), ("lon", "int32"), ("lat", "int32"),
            ):
                var = dataset.variables[name]
                if var.dimensions != ("stations",) or str(var.dtype) != native:
                    raise AuthorCatalogueAuditBlocked("native source-ID or coordinate schema drift")
                var.set_auto_maskandscale(False)
                values = var[:]
                if values.ndim != 1 or values.size != 38_957:
                    raise AuthorCatalogueAuditBlocked("native source axis changed")
                source.append(values.tolist())
            return source[0], source[1], source[2]
    except AuthorCatalogueAuditBlocked:
        raise
    except Exception as exc:
        raise AuthorCatalogueAuditBlocked(
            "original source station read failed: " + type(exc).__name__
        ) from exc


def original_author_identity_receipt() -> dict[str, object]:
    """No station data or author CSV bytes returned or persisted."""
    with tempfile.TemporaryDirectory(prefix="gtsm-two-originals-") as temp:
        source_path = Path(temp) / SOURCE_NAME
        fetch_verified_statistical_original(source_path)
        verified_source = verify_original(
            source_path, inspect_header=True, audit_coordinates=True,
            inspect_labels=True, audit_return_levels=True, audit_station_ids=True,
        )
        author_csv, author_size = get_author_original_csv()
        catalogue = parse_author_catalogue(author_csv)
        station, lon, lat = read_original_native_id_coordinates(source_path)
        overlap = compare_original_to_author_catalogue(station, lon, lat, catalogue)
        require_verified_author_station_join(overlap)
        batch_check = audit_hypothetical_100_id_batches(station, catalogue)
        native_extremes = read_pinned_original_return_matrices(source_path)
        family_quality = audit_return_levels_by_author_name_family(
            station, native_extremes, catalogue
        )
        independently_verified_global = verified_source["return_level_quality"]
        for key in COUNTER_FIELDS:
            if family_quality["source_global_quality_counts"][key] != independently_verified_global[key]:
                raise GtsmFamilyReturnAuditBlocked(
                    "producer-family return QA disagrees with independently verified global original QA"
                )
        return {
            "schema_version": "gtsm-zenodo-v2-author-github-catalogue-receipt-v0",
            "zenodo_original_sha256": PINNED_SHA256,
            "zenodo_original_digest_verified": verified_source["independent_sha256_pinned"],
            "author_catalogue_github_commit": AUTHOR_GITHUB_COMMIT,
            "author_catalogue_git_blob_sha1_verified": AUTHOR_CATALOGUE_GIT_BLOB_SHA1,
            "author_catalogue_original_byte_length": author_size,
            "author_catalogue_derived_data_only": overlap,
            "hypothetical_100_id_batch_aggregate_quality": batch_check,
            "source_return_level_quality_by_author_name_family": family_quality,
            "original_provider_source_files_redistributed": False,
            "original_source_station_ids_or_coordinate_pairs_emitted": False,
            "original_source_files_persisted_after_probe": False,
            "source_release_identity_and_commercial_rights_approved": False,
            "cat_model_admitted": False,
        }


if __name__ == "__main__":
    try:
        print(json.dumps(original_author_identity_receipt(), sort_keys=True, allow_nan=False))
    except (GtsmReceiptError, AuthorCatalogueAuditBlocked,
            GtsmFamilyReturnAuditBlocked, HTTPError, URLError,
            TimeoutError, OSError, ValueError) as exc:
        # None of these sanitized exception messages contain individual
        # source rows, station IDs, coordinates or file bytes.
        raise SystemExit("BLOCKED: " + type(exc).__name__ + ": " + str(exc)) from None
