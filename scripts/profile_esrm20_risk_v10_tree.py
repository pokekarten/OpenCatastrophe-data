# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile immutable ESRM20 v1.0 ``Risk`` tree metadata only.

The production entrypoint is fixed to EFEHR GitLab project 269, release v1.0,
the frozen immutable commit, and the ``Risk`` subtree. It requests repository
tag/tree metadata only; it never requests raw provider file contents or an
archive.

The exact country-risk CSV remains a candidate until this metadata profile
observes its exact path as a blob. Even then, this profile proves repository
tree identity only. It does not prove provider file bytes, CSV schema, Kosovo
rows, numeric values, scientific agreement, publication, or model-use authority.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import PurePosixPath
from typing import Any

from scripts import acquire_efehr_gitlab_receipt as transport
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT

SCHEMA_VERSION = "oc-esrm20-risk-v10-tree-profile-v1"
SOURCE_ISSUE = 778
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
RELEASE_TAG = "v1.0"
EXPECTED_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
SUBTREE_PATH = "Risk"
COUNTRY_RISK_PATH = "Risk/European_Risk_Country.csv"

TREE_PER_PAGE = 100
MAX_TREE_PAGES = 10
MAX_TREE_ENTRIES = 1_000
MAX_TAG_BYTES = 131_072
MAX_TREE_PAGE_BYTES = 1_048_576
MAX_TOTAL_METADATA_BYTES = 4_325_376
MAX_PATH_UTF8_BYTES = 2_048
TOTAL_DEADLINE_SECONDS = 180.0

_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_ENTRY_FIELDS = {"id", "name", "type", "path", "mode"}
_ALLOWED_MODES_BY_TYPE = {
    "blob": frozenset({"100644", "100755"}),
    "tree": frozenset({"040000"}),
}

_OPEN_FIXED = transport._open_fixed
_READ_BOUNDED = transport._read_bounded
_VALIDATE_RESPONSE = transport._validate_exact_response
_REMAINING = transport._remaining
_HEADER_VALUE = transport._header_value
_STRICT_JSON_OBJECT = transport._strict_json_object
_MONOTONIC = time.monotonic
_REQUEST = urllib.request.Request
_PROVIDER_ROOT = PROVIDER_ROOT

FAILURE_CLASSES = frozenset(
    {
        "tag_metadata_acquisition_failure",
        "tag_metadata_validation_failure",
        "tree_metadata_acquisition_failure",
        "tree_metadata_not_found",
        "tree_metadata_validation_failure",
    }
)


class RiskTreeProfileError(RuntimeError):
    """Fail-closed error for the fixed ESRM20 risk-tree metadata profile."""

    def __init__(self, message: str, *, failure_class: str | None = None) -> None:
        super().__init__(message)
        if failure_class is not None and failure_class not in FAILURE_CLASSES:
            raise ValueError("invalid risk-tree failure class")
        self.failure_class = failure_class


def _tag_url() -> str:
    tag = urllib.parse.quote(RELEASE_TAG, safe="")
    return f"{_PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tags/{tag}"


def _tree_url(commit_sha: str, page: int) -> str:
    if type(commit_sha) is not str or _GIT_SHA_RE.fullmatch(commit_sha) is None:
        raise RiskTreeProfileError("risk tree commit SHA is invalid")
    if type(page) is not int or isinstance(page, bool) or not (1 <= page <= MAX_TREE_PAGES):
        raise RiskTreeProfileError("risk tree page is outside policy")
    query = urllib.parse.urlencode(
        {
            "page": page,
            "path": SUBTREE_PATH,
            "per_page": TREE_PER_PAGE,
            "recursive": "true",
            "ref": commit_sha,
        }
    )
    return f"{_PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/tree?{query}"


def _strict_json_array(raw: bytes) -> list[Any]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RiskTreeProfileError("risk tree response is not UTF-8") from exc

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise RiskTreeProfileError(f"duplicate risk-tree JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(token: str) -> Any:
        raise RiskTreeProfileError(f"non-finite risk-tree JSON value: {token}")

    def finite_float(token: str) -> float:
        try:
            value = float(token)
        except ValueError as exc:
            raise RiskTreeProfileError(f"invalid risk-tree JSON float: {token}") from exc
        if not math.isfinite(value):
            raise RiskTreeProfileError(f"non-finite risk-tree JSON value: {token}")
        return value

    try:
        value = json.loads(
            text,
            object_pairs_hook=pairs,
            parse_constant=reject_constant,
            parse_float=finite_float,
        )
    except RiskTreeProfileError:
        raise
    except json.JSONDecodeError as exc:
        raise RiskTreeProfileError("risk tree response is not valid JSON") from exc
    if type(value) is not list:
        raise RiskTreeProfileError("risk tree response is not an array")
    return value


def _bounded_text(value: object, *, field: str) -> str:
    if type(value) is not str or not value:
        raise RiskTreeProfileError(f"risk {field} is not text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise RiskTreeProfileError(f"risk {field} is not UTF-8") from exc
    if len(encoded) > MAX_PATH_UTF8_BYTES:
        raise RiskTreeProfileError(f"risk {field} exceeds policy")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise RiskTreeProfileError(f"risk {field} contains control characters")
    return value


def _canonical_entry(raw: object) -> dict[str, str]:
    if type(raw) is not dict or set(raw) != _ALLOWED_ENTRY_FIELDS:
        raise RiskTreeProfileError("risk tree entry shape drifted")
    object_id = raw["id"]
    if type(object_id) is not str or _GIT_SHA_RE.fullmatch(object_id) is None:
        raise RiskTreeProfileError("risk tree object id is invalid")
    entry_type = raw["type"]
    if entry_type not in _ALLOWED_MODES_BY_TYPE:
        raise RiskTreeProfileError("risk tree object type is unsupported")
    mode = raw["mode"]
    if type(mode) is not str or mode not in _ALLOWED_MODES_BY_TYPE[entry_type]:
        raise RiskTreeProfileError("risk tree type/mode identity drifted")
    path = _bounded_text(raw["path"], field="tree path")
    name = _bounded_text(raw["name"], field="tree name")
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or str(pure) != path
        or any(part in ("", ".", "..") for part in pure.parts)
        or "\\" in path
    ):
        raise RiskTreeProfileError("risk tree path is not canonical relative POSIX")
    if pure.name != name:
        raise RiskTreeProfileError("risk tree path/name identity drifted")
    if not path.startswith(SUBTREE_PATH + "/"):
        raise RiskTreeProfileError("risk tree entry escaped fixed subtree")
    return {
        "id": object_id,
        "mode": mode,
        "name": name,
        "path": path,
        "type": entry_type,
    }


def _optional_bounded_header_int(
    response: object,
    name: str,
    *,
    minimum: int,
    maximum: int,
) -> int | None:
    try:
        raw = _HEADER_VALUE(response, name)
    except transport.EfehrAcquisitionError as exc:
        raise RiskTreeProfileError(f"risk tree {name} header is invalid") from exc
    if raw is None:
        return None
    if not raw or not raw.isascii() or not raw.isdigit():
        raise RiskTreeProfileError(f"risk tree {name} header is invalid")
    value = int(raw)
    if not (minimum <= value <= maximum):
        raise RiskTreeProfileError(f"risk tree {name} exceeds bounded policy")
    return value


def _pagination_state(
    response: object,
    *,
    page: int,
) -> tuple[int | None, int | None]:
    try:
        raw_page = _HEADER_VALUE(response, "X-Page")
        raw_per_page = _HEADER_VALUE(response, "X-Per-Page")
        raw_next = _HEADER_VALUE(response, "X-Next-Page")
    except transport.EfehrAcquisitionError as exc:
        raise RiskTreeProfileError("risk tree pagination header is invalid") from exc
    if not all(type(value) is str for value in (raw_page, raw_per_page, raw_next)):
        raise RiskTreeProfileError("risk tree pagination headers are incomplete")
    if raw_page != str(page) or raw_per_page != str(TREE_PER_PAGE):
        raise RiskTreeProfileError("risk tree pagination identity drifted")

    total_pages = _optional_bounded_header_int(
        response,
        "X-Total-Pages",
        minimum=1,
        maximum=MAX_TREE_PAGES,
    )
    total_entries = _optional_bounded_header_int(
        response,
        "X-Total",
        minimum=1,
        maximum=MAX_TREE_ENTRIES,
    )
    if total_pages is not None and total_pages < page:
        raise RiskTreeProfileError("risk tree total pages precede current page")
    if total_pages is not None and total_entries is not None:
        expected_total_pages = (total_entries + TREE_PER_PAGE - 1) // TREE_PER_PAGE
        if expected_total_pages != total_pages:
            raise RiskTreeProfileError("risk tree total pagination metadata disagrees")

    if raw_next == "":
        if total_pages is not None and total_pages != page:
            raise RiskTreeProfileError("risk tree terminal page disagrees with total pages")
        return None, total_entries
    if not raw_next.isascii() or not raw_next.isdigit():
        raise RiskTreeProfileError("risk tree next-page header is invalid")
    next_page = int(raw_next)
    if next_page != page + 1 or next_page > MAX_TREE_PAGES:
        raise RiskTreeProfileError("risk tree pagination is not contiguous")
    if total_pages is not None and next_page > total_pages:
        raise RiskTreeProfileError("risk tree next page exceeds total pages")
    return next_page, total_entries


def _resolve_tag_commit(
    *,
    opener: Any,
    monotonic: Any,
    deadline: float,
) -> tuple[str, int]:
    url = _tag_url()
    request = _REQUEST(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "OpenCatastrophe-ESRM20-risk-v10-tree-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_REMAINING(deadline, monotonic)) as response:
            _VALIDATE_RESPONSE(response, url)
            raw = _READ_BOUNDED(
                response,
                deadline=deadline,
                maximum=MAX_TAG_BYTES,
                monotonic=monotonic,
            )
    except (
        OSError,
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        transport.EfehrAcquisitionError,
    ) as exc:
        raise RiskTreeProfileError(
            "risk v1.0 tag acquisition failed closed",
            failure_class="tag_metadata_acquisition_failure",
        ) from exc

    try:
        value = _STRICT_JSON_OBJECT(raw)
        if value.get("name") != RELEASE_TAG:
            raise RiskTreeProfileError("risk release-tag identity drifted")
        commit = value.get("commit")
        commit_sha = commit.get("id") if type(commit) is dict else None
        if type(commit_sha) is not str or _GIT_SHA_RE.fullmatch(commit_sha) is None:
            raise RiskTreeProfileError("risk release tag lacks immutable commit")
        target = value.get("target")
        if type(target) is not str or _GIT_SHA_RE.fullmatch(target) is None:
            raise RiskTreeProfileError("risk tag target object id is invalid")
        if commit_sha != EXPECTED_COMMIT_SHA:
            raise RiskTreeProfileError("risk v1.0 tag moved from frozen commit")
        return commit_sha, len(raw)
    except RiskTreeProfileError as exc:
        if exc.failure_class is not None:
            raise
        raise RiskTreeProfileError(
            str(exc),
            failure_class="tag_metadata_validation_failure",
        ) from exc
    except transport.EfehrAcquisitionError as exc:
        raise RiskTreeProfileError(
            "risk v1.0 tag metadata failed validation",
            failure_class="tag_metadata_validation_failure",
        ) from exc


def _inventory_tree(
    commit_sha: str,
    *,
    opener: Any,
    monotonic: Any,
    deadline: float,
    tag_bytes: int,
) -> tuple[list[dict[str, str]], int]:
    entries: dict[str, dict[str, str]] = {}
    total_bytes = tag_bytes
    page = 1
    pages_read = 0
    reported_total_entries: int | None = None
    totals_present: bool | None = None
    try:
        while True:
            pages_read += 1
            if pages_read > MAX_TREE_PAGES:
                raise RiskTreeProfileError("risk tree page bound exceeded")
            url = _tree_url(commit_sha, page)
            request = _REQUEST(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "OpenCatastrophe-ESRM20-risk-v10-tree-v1",
                },
                method="GET",
            )
            try:
                with opener(request, timeout=_REMAINING(deadline, monotonic)) as response:
                    _VALIDATE_RESPONSE(response, url)
                    raw = _READ_BOUNDED(
                        response,
                        deadline=deadline,
                        maximum=MAX_TREE_PAGE_BYTES,
                        monotonic=monotonic,
                    )
                    values = _strict_json_array(raw)
                    next_page, page_total_entries = _pagination_state(
                        response,
                        page=page,
                    )
            except RiskTreeProfileError:
                raise
            except urllib.error.HTTPError as exc:
                failure_class = (
                    "tree_metadata_not_found"
                    if exc.code == 404
                    else "tree_metadata_acquisition_failure"
                )
                raise RiskTreeProfileError(
                    "risk subtree acquisition failed closed",
                    failure_class=failure_class,
                ) from exc
            except (
                OSError,
                urllib.error.URLError,
                TimeoutError,
                transport.EfehrAcquisitionError,
            ) as exc:
                raise RiskTreeProfileError(
                    "risk subtree acquisition failed closed",
                    failure_class="tree_metadata_acquisition_failure",
                ) from exc

            page_has_total = page_total_entries is not None
            if totals_present is None:
                totals_present = page_has_total
            elif totals_present != page_has_total:
                raise RiskTreeProfileError("risk tree total-entry header presence drifted")
            if page_total_entries is not None:
                if reported_total_entries is None:
                    reported_total_entries = page_total_entries
                elif reported_total_entries != page_total_entries:
                    raise RiskTreeProfileError("risk tree total-entry count drifted")

            total_bytes += len(raw)
            if total_bytes > MAX_TOTAL_METADATA_BYTES:
                raise RiskTreeProfileError("risk metadata byte bound exceeded")
            for value in values:
                entry = _canonical_entry(value)
                path = entry["path"]
                if path in entries:
                    raise RiskTreeProfileError("duplicate risk tree path")
                entries[path] = entry
                if len(entries) > MAX_TREE_ENTRIES:
                    raise RiskTreeProfileError("risk tree entry bound exceeded")
            if next_page is None:
                break
            page = next_page
    except RiskTreeProfileError as exc:
        if exc.failure_class is not None:
            raise
        raise RiskTreeProfileError(
            str(exc),
            failure_class="tree_metadata_validation_failure",
        ) from exc

    if not entries:
        raise RiskTreeProfileError(
            "fixed risk subtree is empty",
            failure_class="tree_metadata_validation_failure",
        )
    if reported_total_entries is not None and len(entries) != reported_total_entries:
        raise RiskTreeProfileError(
            "risk tree inventory count disagrees with provider total",
            failure_class="tree_metadata_validation_failure",
        )
    return [entries[path] for path in sorted(entries)], pages_read


def _tree_identity_sha256(entries: list[dict[str, str]]) -> str:
    canonical = "".join(
        f"{entry['type']}\t{entry['mode']}\t{entry['id']}\t{entry['path']}\n"
        for entry in entries
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _public_inventory(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "mode": entry["mode"],
            "object_sha1": entry["id"],
            "path": entry["path"],
            "type": entry["type"],
        }
        for entry in entries
    ]


def _country_risk_path_status(
    entries: list[dict[str, str]],
) -> tuple[str, dict[str, str] | None]:
    matches = [entry for entry in entries if entry["path"] == COUNTRY_RISK_PATH]
    if len(matches) > 1:
        raise RiskTreeProfileError("country-risk path appears more than once")
    if not matches:
        return "absent", None
    entry = matches[0]
    public = {
        "mode": entry["mode"],
        "object_sha1": entry["id"],
        "path": entry["path"],
        "type": entry["type"],
    }
    if entry["type"] == "blob":
        return "blob", public
    return "tree", public


def _profile_v10_tree_for_test(*, opener: Any, monotonic: Any) -> dict[str, Any]:
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    commit_sha, tag_bytes = _resolve_tag_commit(
        opener=opener,
        monotonic=monotonic,
        deadline=deadline,
    )
    entries, pages_read = _inventory_tree(
        commit_sha,
        opener=opener,
        monotonic=monotonic,
        deadline=deadline,
        tag_bytes=tag_bytes,
    )
    status, country_entry = _country_risk_path_status(entries)
    blob_count = sum(entry["type"] == "blob" for entry in entries)
    tree_count = sum(entry["type"] == "tree" for entry in entries)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": commit_sha,
        "subtree_path": SUBTREE_PATH,
        "pages_read": pages_read,
        "entry_count": len(entries),
        "blob_count": blob_count,
        "tree_count": tree_count,
        "tree_identity_sha256": _tree_identity_sha256(entries),
        "risk_inventory": _public_inventory(entries),
        "country_risk_path": COUNTRY_RISK_PATH,
        "country_risk_path_status": status,
        "country_risk_path_entry": country_entry,
        "country_risk_blob_candidate_present": status == "blob",
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "country_risk_bytes_verified": False,
        "country_risk_schema_verified": False,
        "reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


_TAG_URL = _tag_url
_TREE_URL = _tree_url
_STRICT_JSON_ARRAY_FN = _strict_json_array
_BOUNDED_TEXT = _bounded_text
_CANONICAL_ENTRY = _canonical_entry
_OPTIONAL_BOUNDED_HEADER_INT = _optional_bounded_header_int
_PAGINATION_STATE = _pagination_state
_RESOLVE_TAG_COMMIT = _resolve_tag_commit
_INVENTORY_TREE = _inventory_tree
_TREE_IDENTITY_SHA256 = _tree_identity_sha256
_PUBLIC_INVENTORY = _public_inventory
_COUNTRY_RISK_PATH_STATUS = _country_risk_path_status
_PROFILE_FOR_TEST = _profile_v10_tree_for_test
_JSON_LOADS = json.loads
_MATH_ISFINITE = math.isfinite
_URL_QUOTE = urllib.parse.quote
_URLENCODE = urllib.parse.urlencode
_PURE_POSIX_PATH = PurePosixPath
_SHA256 = hashlib.sha256
_GIT_SHA_RE_AUTHORITY = _GIT_SHA_RE


def _require_production_authority() -> None:
    exact = (
        (SCHEMA_VERSION, "oc-esrm20-risk-v10-tree-profile-v1"),
        (SOURCE_ISSUE, 778),
        (DATASET_ID, "efehr.esrm20.risk-inputs.v1.0"),
        (PROJECT_ID, 269),
        (PROJECT_PATH, "efehr/esrm20"),
        (RELEASE_TAG, "v1.0"),
        (EXPECTED_COMMIT_SHA, "05f83bbc9df81d02ee8ddb1801d9d781355ce783"),
        (SUBTREE_PATH, "Risk"),
        (COUNTRY_RISK_PATH, "Risk/European_Risk_Country.csv"),
        (TREE_PER_PAGE, 100),
        (MAX_TREE_PAGES, 10),
        (MAX_TREE_ENTRIES, 1_000),
        (MAX_TAG_BYTES, 131_072),
        (MAX_TREE_PAGE_BYTES, 1_048_576),
        (MAX_TOTAL_METADATA_BYTES, 4_325_376),
        (MAX_PATH_UTF8_BYTES, 2_048),
        (TOTAL_DEADLINE_SECONDS, 180.0),
        (PROVIDER_ROOT, _PROVIDER_ROOT),
    )
    for observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise RiskTreeProfileError("trusted risk-tree target authority drifted")

    expected_entry_fields = {"id", "name", "type", "path", "mode"}
    expected_modes_by_type = {
        "blob": frozenset({"100644", "100755"}),
        "tree": frozenset({"040000"}),
    }
    if (
        _GIT_SHA_RE is not _GIT_SHA_RE_AUTHORITY
        or type(_ALLOWED_ENTRY_FIELDS) is not set
        or _ALLOWED_ENTRY_FIELDS != expected_entry_fields
        or type(_ALLOWED_MODES_BY_TYPE) is not dict
        or _ALLOWED_MODES_BY_TYPE != expected_modes_by_type
    ):
        raise RiskTreeProfileError("trusted risk-tree policy authority drifted")

    authority = (
        (transport._open_fixed, _OPEN_FIXED),
        (transport._read_bounded, _READ_BOUNDED),
        (transport._validate_exact_response, _VALIDATE_RESPONSE),
        (transport._remaining, _REMAINING),
        (transport._header_value, _HEADER_VALUE),
        (transport._strict_json_object, _STRICT_JSON_OBJECT),
        (time.monotonic, _MONOTONIC),
        (urllib.request.Request, _REQUEST),
        (json.loads, _JSON_LOADS),
        (math.isfinite, _MATH_ISFINITE),
        (urllib.parse.quote, _URL_QUOTE),
        (urllib.parse.urlencode, _URLENCODE),
        (PurePosixPath, _PURE_POSIX_PATH),
        (hashlib.sha256, _SHA256),
        (_tag_url, _TAG_URL),
        (_tree_url, _TREE_URL),
        (_strict_json_array, _STRICT_JSON_ARRAY_FN),
        (_bounded_text, _BOUNDED_TEXT),
        (_canonical_entry, _CANONICAL_ENTRY),
        (_optional_bounded_header_int, _OPTIONAL_BOUNDED_HEADER_INT),
        (_pagination_state, _PAGINATION_STATE),
        (_resolve_tag_commit, _RESOLVE_TAG_COMMIT),
        (_inventory_tree, _INVENTORY_TREE),
        (_tree_identity_sha256, _TREE_IDENTITY_SHA256),
        (_public_inventory, _PUBLIC_INVENTORY),
        (_country_risk_path_status, _COUNTRY_RISK_PATH_STATUS),
        (_profile_v10_tree_for_test, _PROFILE_FOR_TEST),
    )
    if any(observed is not expected for observed, expected in authority):
        raise RiskTreeProfileError("trusted risk-tree execution authority drifted")


def profile_v10_tree() -> dict[str, Any]:
    """Run the zero-argument production profile against the fixed provider target."""
    _require_production_authority()
    return _PROFILE_FOR_TEST(opener=_OPEN_FIXED, monotonic=_MONOTONIC)
