# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Receipt-bound EQ1 Kosovo exposure↔site spatial interoperability profiler.

The bounded question is deliberately narrower than source-CRS identification:
can the exact Kosovo-residential exposure coordinates be passed unchanged to the
exact ESRM20 Kosovo site-model coordinate surface and associated under the
OpenQuake 3.14 geographic-distance contract?

Both exact external byte identities are verified before coordinate parsing.  The
result contains aggregate association diagnostics only; provider coordinates and
raw rows are never returned.  A positive result does not establish WGS84/EPSG,
reprojection authority, historical runtime identity, model validity, publication
or model-use authority.
"""

from __future__ import annotations

import csv
import io
import json
import math
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Iterable

try:
    from scripts import profile_efehr_kosovo_exposure_value_spatial as exposure
    from scripts import profile_efehr_kosovo_site_model as site_model
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from scripts.efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import profile_efehr_kosovo_exposure_value_spatial as exposure
    import profile_efehr_kosovo_site_model as site_model
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target


SCHEMA_VERSION = "oc-eq1-kosovo-spatial-interop-v0"
SOURCE_ISSUE = 287
OPENQUAKE_REFERENCE_TAG = "v3.14.0"
OPENQUAKE_REFERENCE_COMMIT = "9f044c93d72846421a8faa90ebf0a6afacdf3c20"
OPENQUAKE_EARTH_RADIUS_KM = 6371.0
OPENQUAKE_DEFAULT_ASSET_HAZARD_DISTANCE_KM = 15.0
DISTANCE_THRESHOLDS_KM = (1.0, 5.0, 10.0, 15.0, 20.0, 25.0, 50.0)
MAX_EXPOSURE_RECORDS = 100_000
MAX_SITE_RECORDS = 10_000

# Durable production authority is deliberately pinned rather than inferred from
# mutable imported module state at call time.  This mirrors the already-reviewed
# EFEHR trusted workers: test injection remains private, while the public entry
# point first rejects runtime rebinding/drift and then uses these canonical values.
_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic
_CANONICAL_EXPOSURE_PROFILER = exposure.profile_verified_exposure_value_spatial
_CANONICAL_SITE_PROFILER = site_model.profile_verified_xml_bytes
_CANONICAL_EXPOSURE_SOURCE_ISSUE = 282
_CANONICAL_EXPOSURE_DATASET_ID = "efehr.esrm20.european-exposure-model.v1.0"
_CANONICAL_EXPOSURE_PROJECT_ID = 186
_CANONICAL_EXPOSURE_PROJECT_PATH = "efehr/esrm20_exposure"
_CANONICAL_EXPOSURE_COMMIT_SHA = "900433ada80fbb424c0976c34d72eeef97bab1af"
_CANONICAL_EXPOSURE_REPOSITORY_PATH = "_exposure_models/Exposure_Model_Kosovo_Res.csv"
_CANONICAL_EXPOSURE_BYTE_COUNT = 316_789
_CANONICAL_EXPOSURE_SHA256 = "4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea"
_CANONICAL_SITE_SOURCE_SCIENCE_ISSUE = 284
_CANONICAL_SITE_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
_CANONICAL_SITE_PROJECT_ID = 269
_CANONICAL_SITE_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_SITE_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_SITE_REPOSITORY_PATH = "Vs30/Site_model_Kosovo.xml"
_CANONICAL_SITE_BYTE_COUNT = 5_891
_CANONICAL_SITE_SHA256 = "746cf75d91507da8b55a9476c61bb5d884eed42c6268a36b1179f432e8850edd"


class SpatialInteropProfileError(RuntimeError):
    """Raised when the bounded spatial interoperability profile fails closed."""


def _require_coordinate(value: str, *, role: str, minimum: float, maximum: float) -> float:
    if type(value) is not str or value == "" or value != value.strip():
        raise SpatialInteropProfileError(f"{role} coordinate is empty or padded")
    try:
        number = float(value)
    except ValueError as exc:
        raise SpatialInteropProfileError(f"{role} coordinate is not numeric") from exc
    if not math.isfinite(number) or number < minimum or number > maximum:
        raise SpatialInteropProfileError(f"{role} coordinate is outside geographic bounds")
    return number


def _cartesian(lon: float, lat: float) -> tuple[float, float, float]:
    """Match the zero-depth spherical Cartesian surface used by OQ hazardlib."""

    lon_radians = math.radians(lon)
    lat_radians = math.radians(lat)
    cos_lat = math.cos(lat_radians)
    return (
        OPENQUAKE_EARTH_RADIUS_KM * cos_lat * math.cos(lon_radians),
        OPENQUAKE_EARTH_RADIUS_KM * cos_lat * math.sin(lon_radians),
        OPENQUAKE_EARTH_RADIUS_KM * math.sin(lat_radians),
    )


def _chord_distance_km(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def _nearest_distance_km(
    point: tuple[float, float],
    site_cartesian: list[tuple[float, float, float]],
) -> float:
    if not site_cartesian:
        raise SpatialInteropProfileError("site coordinate set is empty")
    target = _cartesian(*point)
    return min(_chord_distance_km(target, candidate) for candidate in site_cartesian)


def _canonical_float(value: float) -> str:
    if not math.isfinite(value):
        raise SpatialInteropProfileError("distance diagnostic became non-finite")
    text = format(value, ".9f").rstrip("0").rstrip(".")
    return text or "0"


def _profile_verified_coordinate_sets(
    exposure_points: Iterable[tuple[float, float]],
    site_points: Iterable[tuple[float, float]],
) -> dict[str, Any]:
    """Return aggregate OQ3.14-compatible nearest-site diagnostics.

    This reproduces the OpenQuake 3.14 association geometry only for the
    configuration case where the supplied site-model mesh is the selected hazard
    mesh: no higher-precedence explicit ``sites``, ``sites`` input, hazard-curves
    mesh, or ``region_grid_spacing`` path may override it.  In that bounded case,
    exposure asset locations are associated to the hazard site collection using
    geographic nearest-neighbour distance and the configured
    ``asset_hazard_distance`` (15 km by default).  Hazardlib's geographic-object
    index compares zero-depth spherical Cartesian distances; this helper
    reproduces that distance geometry without importing an OpenQuake runtime into
    this dependency-free repository.
    """

    exposure_list = list(exposure_points)
    site_list = list(site_points)
    if not exposure_list or len(exposure_list) > MAX_EXPOSURE_RECORDS:
        raise SpatialInteropProfileError("exposure coordinate count is outside bounded policy")
    if not site_list or len(site_list) > MAX_SITE_RECORDS:
        raise SpatialInteropProfileError("site coordinate count is outside bounded policy")

    for lon, lat in exposure_list:
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise SpatialInteropProfileError("exposure coordinate is outside geographic bounds")
    for lon, lat in site_list:
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise SpatialInteropProfileError("site coordinate is outside geographic bounds")

    site_cartesian = [_cartesian(lon, lat) for lon, lat in site_list]
    nearest = [_nearest_distance_km(point, site_cartesian) for point in exposure_list]

    threshold_results = []
    for threshold in DISTANCE_THRESHOLDS_KM:
        associated = sum(distance <= threshold for distance in nearest)
        threshold_results.append(
            {
                "threshold_km": _canonical_float(threshold),
                "associated_exposure_record_count": associated,
                "discarded_exposure_record_count": len(nearest) - associated,
                "all_exposure_records_associated": associated == len(nearest),
            }
        )

    default = next(
        item
        for item in threshold_results
        if item["threshold_km"] == _canonical_float(OPENQUAKE_DEFAULT_ASSET_HAZARD_DISTANCE_KM)
    )
    return {
        "exposure_record_count": len(exposure_list),
        "distinct_exposure_location_count": len(set(exposure_list)),
        "site_record_count": len(site_list),
        "distinct_site_location_count": len(set(site_list)),
        "nearest_site_distance_km": {
            "minimum": _canonical_float(min(nearest)),
            "maximum": _canonical_float(max(nearest)),
        },
        "threshold_diagnostics": threshold_results,
        "openquake_default_asset_hazard_distance_km": _canonical_float(
            OPENQUAKE_DEFAULT_ASSET_HAZARD_DISTANCE_KM
        ),
        "default_distance_association": dict(default),
        "raw_coordinates_returned": False,
    }


def _parse_verified_exposure_coordinates(raw: bytes) -> list[tuple[float, float]]:
    try:
        verified = exposure.profile_verified_exposure_value_spatial(
            raw,
            expected_byte_count=exposure.EXPECTED_BYTE_COUNT,
            expected_sha256=exposure.EXPECTED_SHA256,
        )
    except exposure.ExposureValueSpatialProfileError as exc:
        raise SpatialInteropProfileError("exact exposure receipt/profile gate failed") from exc

    try:
        text = raw.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=",", strict=True)
        if reader.fieldnames is None or tuple(reader.fieldnames) != exposure.EXPECTED_HEADER:
            raise SpatialInteropProfileError("verified exposure header drifted")
        points = [
            (
                _require_coordinate(
                    row["LONGITUDE"], role="exposure longitude", minimum=-180, maximum=180
                ),
                _require_coordinate(
                    row["LATITUDE"], role="exposure latitude", minimum=-90, maximum=90
                ),
            )
            for row in reader
        ]
    except (UnicodeDecodeError, csv.Error, KeyError) as exc:
        raise SpatialInteropProfileError("verified exposure coordinate parse failed") from exc
    if len(points) != verified["record_count"]:
        raise SpatialInteropProfileError("exposure coordinate count drifted after receipt verification")
    return points


def _local_name(name: str) -> str:
    return name.rsplit("}", 1)[-1] if name.startswith("{") else name


def _parse_verified_site_coordinates(raw: bytes) -> list[tuple[float, float]]:
    try:
        site_model.profile_verified_xml_bytes(
            raw,
            expected_byte_count=site_model.EXPECTED_BYTE_COUNT,
            expected_sha256=site_model.EXPECTED_SHA256,
        )
    except site_model.KosovoSiteProfileError as exc:
        raise SpatialInteropProfileError("exact site-model receipt/profile gate failed") from exc

    codec = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
    try:
        root = ET.fromstring(raw.decode(codec, errors="strict"))
    except (UnicodeDecodeError, ET.ParseError) as exc:
        raise SpatialInteropProfileError("verified site coordinate parse failed") from exc

    points: list[tuple[float, float]] = []
    for element in root.iter():
        by_local = {_local_name(name): value for name, value in element.attrib.items()}
        has_lon = "lon" in by_local
        has_lat = "lat" in by_local
        if has_lon != has_lat:
            raise SpatialInteropProfileError("verified site element has only one coordinate axis")
        if has_lon:
            points.append(
                (
                    _require_coordinate(
                        by_local["lon"], role="site longitude", minimum=-180, maximum=180
                    ),
                    _require_coordinate(
                        by_local["lat"], role="site latitude", minimum=-90, maximum=90
                    ),
                )
            )
    if not points:
        raise SpatialInteropProfileError("verified site model contains no lon/lat site records")
    if len(points) != len(set(points)):
        raise SpatialInteropProfileError("verified site model contains duplicate coordinate pairs")
    return points


def profile_verified_kosovo_spatial_interop(
    exposure_raw: bytes,
    site_raw: bytes,
) -> dict[str, Any]:
    """Verify both frozen receipts, then measure aggregate coordinate interop."""

    exposure_points = _parse_verified_exposure_coordinates(exposure_raw)
    site_points = _parse_verified_site_coordinates(site_raw)
    profile = _profile_verified_coordinate_sets(exposure_points, site_points)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "reference_runtime": {
            "repository": "gem/oq-engine",
            "tag": OPENQUAKE_REFERENCE_TAG,
            "commit_sha": OPENQUAKE_REFERENCE_COMMIT,
            "association_contract": (
                "when the supplied site-model mesh is the selected hazard mesh, exposure "
                "asset locations are associated to nearest hazard sites by zero-depth "
                "spherical Cartesian distance"
            ),
            "hazard_mesh_precondition": (
                "no higher-precedence explicit sites, sites input, hazard-curves mesh, "
                "or region_grid_spacing path overrides the supplied site-model mesh"
            ),
        },
        "exposure_identity": {
            "dataset_id": exposure.DATASET_ID,
            "project_id": exposure.PROJECT_ID,
            "project_path": exposure.PROJECT_PATH,
            "commit_sha": exposure.COMMIT_SHA,
            "repository_path": exposure.REPOSITORY_PATH,
            "byte_count": exposure.EXPECTED_BYTE_COUNT,
            "sha256": exposure.EXPECTED_SHA256,
        },
        "site_identity": {
            "dataset_id": site_model.DATASET_ID,
            "project_id": site_model.PROJECT_ID,
            "project_path": site_model.PROJECT_PATH,
            "commit_sha": site_model.COMMIT_SHA,
            "repository_path": site_model.REPOSITORY_PATH,
            "byte_count": site_model.EXPECTED_BYTE_COUNT,
            "sha256": site_model.EXPECTED_SHA256,
        },
        "profile": profile,
        "reference_runtime_coordinate_role_verified": True,
        "source_crs_datum_epsg_verified": False,
        "reprojection_performed": False,
        "reprojection_authorized": False,
        "geographic_cross_source_equivalence_authorized": False,
        "raw_provider_coordinates_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


_CANONICAL_INTEROP_PROFILER = profile_verified_kosovo_spatial_interop


def _require_production_contract() -> None:
    """Reject runtime rebinding or frozen-identity drift before provider I/O."""

    if _open_fixed is not _CANONICAL_OPEN_FIXED:
        raise SpatialInteropProfileError("frozen spatial-interoperability production transport drifted")
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise SpatialInteropProfileError("frozen spatial-interoperability monotonic clock drifted")
    if exposure.profile_verified_exposure_value_spatial is not _CANONICAL_EXPOSURE_PROFILER:
        raise SpatialInteropProfileError("frozen exposure profiler identity drifted")
    if site_model.profile_verified_xml_bytes is not _CANONICAL_SITE_PROFILER:
        raise SpatialInteropProfileError("frozen site profiler identity drifted")
    if profile_verified_kosovo_spatial_interop is not _CANONICAL_INTEROP_PROFILER:
        raise SpatialInteropProfileError("frozen spatial-interoperability profiler identity drifted")

    exact = (
        (SCHEMA_VERSION, "oc-eq1-kosovo-spatial-interop-v0", "schema version"),
        (SOURCE_ISSUE, 287, "source issue"),
        (OPENQUAKE_REFERENCE_TAG, "v3.14.0", "OpenQuake reference tag"),
        (
            OPENQUAKE_REFERENCE_COMMIT,
            "9f044c93d72846421a8faa90ebf0a6afacdf3c20",
            "OpenQuake reference commit",
        ),
        (OPENQUAKE_EARTH_RADIUS_KM, 6371.0, "OpenQuake Earth radius"),
        (OPENQUAKE_DEFAULT_ASSET_HAZARD_DISTANCE_KM, 15.0, "default asset-hazard distance"),
        (
            DISTANCE_THRESHOLDS_KM,
            (1.0, 5.0, 10.0, 15.0, 20.0, 25.0, 50.0),
            "distance thresholds",
        ),
        (MAX_EXPOSURE_RECORDS, 100_000, "exposure record bound"),
        (MAX_SITE_RECORDS, 10_000, "site record bound"),
        (exposure.SOURCE_ISSUE, _CANONICAL_EXPOSURE_SOURCE_ISSUE, "exposure source issue"),
        (exposure.DATASET_ID, _CANONICAL_EXPOSURE_DATASET_ID, "exposure dataset"),
        (exposure.PROJECT_ID, _CANONICAL_EXPOSURE_PROJECT_ID, "exposure project id"),
        (exposure.PROJECT_PATH, _CANONICAL_EXPOSURE_PROJECT_PATH, "exposure project path"),
        (exposure.COMMIT_SHA, _CANONICAL_EXPOSURE_COMMIT_SHA, "exposure commit"),
        (
            exposure.REPOSITORY_PATH,
            _CANONICAL_EXPOSURE_REPOSITORY_PATH,
            "exposure repository path",
        ),
        (exposure.EXPECTED_BYTE_COUNT, _CANONICAL_EXPOSURE_BYTE_COUNT, "exposure byte count"),
        (exposure.EXPECTED_SHA256, _CANONICAL_EXPOSURE_SHA256, "exposure SHA-256"),
        (
            site_model.SOURCE_SCIENCE_ISSUE,
            _CANONICAL_SITE_SOURCE_SCIENCE_ISSUE,
            "site science issue",
        ),
        (site_model.DATASET_ID, _CANONICAL_SITE_DATASET_ID, "site dataset"),
        (site_model.PROJECT_ID, _CANONICAL_SITE_PROJECT_ID, "site project id"),
        (site_model.PROJECT_PATH, _CANONICAL_SITE_PROJECT_PATH, "site project path"),
        (site_model.COMMIT_SHA, _CANONICAL_SITE_COMMIT_SHA, "site commit"),
        (
            site_model.REPOSITORY_PATH,
            _CANONICAL_SITE_REPOSITORY_PATH,
            "site repository path",
        ),
        (site_model.EXPECTED_BYTE_COUNT, _CANONICAL_SITE_BYTE_COUNT, "site byte count"),
        (site_model.EXPECTED_SHA256, _CANONICAL_SITE_SHA256, "site SHA-256"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise SpatialInteropProfileError(f"frozen spatial-interoperability {label} drifted")


def _fixed_target(*, source_issue: int, dataset_id: str, project_id: int, commit: str, path: str):
    try:
        return validate_target(
            source_issue=source_issue,
            dataset_id=dataset_id,
            project_id=project_id,
            commit_sha=commit,
            repository_path=path,
        )
    except EfehrReceiptError as exc:
        raise SpatialInteropProfileError("trusted fixed EFEHR target is invalid") from exc


def _fetch_exact_bytes(
    *,
    source_issue: int,
    dataset_id: str,
    project_id: int,
    commit: str,
    path: str,
    expected_byte_count: int,
    opener: Any,
    deadline: float,
    monotonic: Any,
) -> bytes:
    target = _fixed_target(
        source_issue=source_issue,
        dataset_id=dataset_id,
        project_id=project_id,
        commit=commit,
        path=path,
    )
    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/plain,application/xml,text/xml,text/csv;q=0.9",
            "User-Agent": "OpenCatastrophe-EQ1-spatial-interop-v0",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            return _read_bounded(
                response,
                deadline=deadline,
                maximum=expected_byte_count,
                monotonic=monotonic,
            )
    except EfehrAcquisitionError as exc:
        raise SpatialInteropProfileError("fixed EFEHR spatial input retrieval failed closed") from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise SpatialInteropProfileError(
            f"fixed EFEHR spatial input retrieval failed: {type(exc).__name__}"
        ) from exc


def _acquire_and_profile_kosovo_spatial_interop(*, opener: Any, monotonic: Any) -> dict[str, Any]:
    """Private injectable helper for deterministic offline acquisition tests."""

    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    exposure_raw = _fetch_exact_bytes(
        source_issue=_CANONICAL_EXPOSURE_SOURCE_ISSUE,
        dataset_id=_CANONICAL_EXPOSURE_DATASET_ID,
        project_id=_CANONICAL_EXPOSURE_PROJECT_ID,
        commit=_CANONICAL_EXPOSURE_COMMIT_SHA,
        path=_CANONICAL_EXPOSURE_REPOSITORY_PATH,
        expected_byte_count=_CANONICAL_EXPOSURE_BYTE_COUNT,
        opener=opener,
        deadline=deadline,
        monotonic=monotonic,
    )
    site_raw = _fetch_exact_bytes(
        source_issue=_CANONICAL_SITE_SOURCE_SCIENCE_ISSUE,
        dataset_id=_CANONICAL_SITE_DATASET_ID,
        project_id=_CANONICAL_SITE_PROJECT_ID,
        commit=_CANONICAL_SITE_COMMIT_SHA,
        path=_CANONICAL_SITE_REPOSITORY_PATH,
        expected_byte_count=_CANONICAL_SITE_BYTE_COUNT,
        opener=opener,
        deadline=deadline,
        monotonic=monotonic,
    )
    return profile_verified_kosovo_spatial_interop(exposure_raw, site_raw)


def acquire_and_profile_kosovo_spatial_interop() -> dict[str, Any]:
    """Run fixed production authority and return bounded aggregate evidence."""

    _require_production_contract()
    return _acquire_and_profile_kosovo_spatial_interop(
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
    )


def main() -> int:
    print(json.dumps(acquire_and_profile_kosovo_spatial_interop(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover - trusted manual execution entry point
    raise SystemExit(main())
