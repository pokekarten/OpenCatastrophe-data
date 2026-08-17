# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded metadata-only history profile for the ESRM20 Exposure-to-Site tool.

The profile is deliberately narrower than a source acquisition. It queries only
GitLab commit-list metadata for the fixed public EFEHR project and a fixed
historical UTC window around the ESRM20 v1.0 release cut. It never requests
repository file contents, archives, raw URLs, or arbitrary projects/refs/dates.

Candidate commit identity is provenance evidence only. Temporal inclusion in the
window does not identify the exact commit or invocation that generated the
frozen Kosovo site model and does not establish CRS or missing-value semantics.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Any

from scripts import acquire_efehr_gitlab_receipt as transport
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT

SCHEMA_VERSION = "oc-esrm20-sitemodel-history-profile-v1"
SOURCE_ISSUE = 291
PROJECT_ID = 278
PROJECT_PATH = "efehr/esrm20_sitemodel"
REF_NAME = "main"
SINCE_UTC = "2021-12-06T00:00:00Z"
UNTIL_UTC = "2021-12-16T23:59:59Z"
PER_PAGE = 100
MAX_PAGES = 10
MAX_PAGE_BYTES = 1_048_576
MAX_COMMITS = PER_PAGE * MAX_PAGES
MAX_PARENT_IDS = 32
TOTAL_DEADLINE_SECONDS = 180.0

_OPEN_FIXED = transport._open_fixed
_READ_BOUNDED = transport._read_bounded
_VALIDATE_RESPONSE = transport._validate_exact_response
_REMAINING = transport._remaining
_MONOTONIC = time.monotonic
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


class SiteModelHistoryProfileError(RuntimeError):
    """Raised when fixed site-tool history metadata cannot be proven safely."""


def _strict_json(raw: bytes) -> Any:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise SiteModelHistoryProfileError("site-tool metadata response is not UTF-8") from exc

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise SiteModelHistoryProfileError(
                    f"duplicate site-tool metadata JSON key: {key}"
                )
            result[key] = value
        return result

    def reject_nonfinite(token: str) -> Any:
        raise SiteModelHistoryProfileError(
            f"non-finite site-tool metadata JSON value: {token}"
        )

    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_nonfinite,
        )
    except SiteModelHistoryProfileError:
        raise
    except json.JSONDecodeError as exc:
        raise SiteModelHistoryProfileError(
            "site-tool metadata response is not valid JSON"
        ) from exc


def _window_endpoint(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SiteModelHistoryProfileError("fixed site-tool history window is timezone-naive")
    return parsed.astimezone(timezone.utc)


_SINCE = _window_endpoint(SINCE_UTC)
_UNTIL = _window_endpoint(UNTIL_UTC)


def _commits_url(page: int) -> str:
    if type(page) is not int or isinstance(page, bool) or not (1 <= page <= MAX_PAGES):
        raise SiteModelHistoryProfileError("site-tool commit page is outside policy")
    query = urllib.parse.urlencode(
        {
            "ref_name": REF_NAME,
            "since": SINCE_UTC,
            "until": UNTIL_UTC,
            "order": "default",
            "with_stats": "false",
            "per_page": PER_PAGE,
            "page": page,
        }
    )
    return f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/commits?{query}"


def _parse_committed_at(value: object) -> tuple[str, datetime]:
    if type(value) is not str or not value or value != value.strip():
        raise SiteModelHistoryProfileError("site-tool committed_date is not bounded text")
    if len(value.encode("utf-8")) > 64:
        raise SiteModelHistoryProfileError("site-tool committed_date exceeds policy")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SiteModelHistoryProfileError("site-tool committed_date is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SiteModelHistoryProfileError("site-tool committed_date is timezone-naive")
    observed = parsed.astimezone(timezone.utc)
    if not (_SINCE <= observed <= _UNTIL):
        raise SiteModelHistoryProfileError("site-tool commit lies outside fixed history window")
    canonical = observed.isoformat(timespec="seconds").replace("+00:00", "Z")
    return canonical, observed


def _validate_commit(raw: object) -> tuple[dict[str, Any], datetime]:
    if type(raw) is not dict:
        raise SiteModelHistoryProfileError("site-tool commit entry is not an object")
    for field in ("id", "committed_date", "parent_ids"):
        if field not in raw:
            raise SiteModelHistoryProfileError(f"site-tool commit entry lacks {field}")

    commit_sha = raw["id"]
    if type(commit_sha) is not str or _SHA1_RE.fullmatch(commit_sha) is None:
        raise SiteModelHistoryProfileError("site-tool commit id is not a canonical Git SHA-1")

    committed_at, observed_time = _parse_committed_at(raw["committed_date"])
    parent_ids = raw["parent_ids"]
    if type(parent_ids) is not list or len(parent_ids) > MAX_PARENT_IDS:
        raise SiteModelHistoryProfileError("site-tool parent_ids exceed bounded policy")
    parents: list[str] = []
    for parent in parent_ids:
        if type(parent) is not str or _SHA1_RE.fullmatch(parent) is None:
            raise SiteModelHistoryProfileError("site-tool parent id is not a canonical Git SHA-1")
        parents.append(parent)
    if len(set(parents)) != len(parents):
        raise SiteModelHistoryProfileError("site-tool commit contains duplicate parent ids")

    return (
        {
            "commit_sha": commit_sha,
            "committed_at_utc": committed_at,
            "parent_shas": parents,
        },
        observed_time,
    )


def _pagination_next(headers: object, *, expected_page: int) -> int | None:
    getter = getattr(headers, "get", None)
    if not callable(getter):
        raise SiteModelHistoryProfileError("site-tool pagination headers are unavailable")
    observed_page = getter("X-Page")
    observed_per_page = getter("X-Per-Page")
    observed_next = getter("X-Next-Page")
    if not all(type(value) is str for value in (observed_page, observed_per_page, observed_next)):
        raise SiteModelHistoryProfileError("site-tool pagination headers are incomplete")
    if observed_page != str(expected_page):
        raise SiteModelHistoryProfileError("site-tool X-Page drifted")
    if observed_per_page != str(PER_PAGE):
        raise SiteModelHistoryProfileError("site-tool X-Per-Page drifted")
    if observed_next == "":
        return None
    expected_next = expected_page + 1
    if observed_next != str(expected_next):
        raise SiteModelHistoryProfileError("site-tool X-Next-Page is not contiguous")
    if expected_next > MAX_PAGES:
        raise SiteModelHistoryProfileError("site-tool pagination exceeds page policy")
    return expected_next


def _history_sha256(candidates: list[dict[str, Any]]) -> str:
    canonical = "".join(
        f"{item['commit_sha']}\t{item['committed_at_utc']}\t{','.join(item['parent_shas'])}\n"
        for item in candidates
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def profile_history(*, opener: Any | None = None, monotonic: Any | None = None) -> dict[str, Any]:
    """Return a deterministic receipt of candidate commits in the fixed window."""
    if (
        transport._open_fixed is not _OPEN_FIXED
        or transport._read_bounded is not _READ_BOUNDED
        or transport._validate_exact_response is not _VALIDATE_RESPONSE
        or transport._remaining is not _REMAINING
        or time.monotonic is not _MONOTONIC
    ):
        raise SiteModelHistoryProfileError("trusted EFEHR history transport authority drifted")
    if (
        PROJECT_ID != 278
        or PROJECT_PATH != "efehr/esrm20_sitemodel"
        or REF_NAME != "main"
        or SINCE_UTC != "2021-12-06T00:00:00Z"
        or UNTIL_UTC != "2021-12-16T23:59:59Z"
    ):
        raise SiteModelHistoryProfileError("fixed site-tool history authority drifted")

    clock = monotonic or _MONOTONIC
    open_response = opener or _OPEN_FIXED
    deadline = clock() + TOTAL_DEADLINE_SECONDS
    candidates_with_time: list[tuple[dict[str, Any], datetime]] = []
    seen_ids: set[str] = set()
    page = 1
    pages_read = 0

    while True:
        url = _commits_url(page)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "OpenCatastrophe-ESRM20-sitemodel-history-v1",
            },
            method="GET",
        )
        try:
            with open_response(request, timeout=_REMAINING(deadline, clock)) as response:
                _VALIDATE_RESPONSE(response, url)
                raw = _READ_BOUNDED(
                    response,
                    deadline=deadline,
                    maximum=MAX_PAGE_BYTES,
                    monotonic=clock,
                )
                page_value = _strict_json(raw)
                if type(page_value) is not list:
                    raise SiteModelHistoryProfileError(
                        "site-tool commit-list response is not an array"
                    )
                for raw_commit in page_value:
                    candidate, committed_at = _validate_commit(raw_commit)
                    commit_sha = candidate["commit_sha"]
                    if commit_sha in seen_ids:
                        raise SiteModelHistoryProfileError(
                            "site-tool history contains duplicate commit ids"
                        )
                    seen_ids.add(commit_sha)
                    candidates_with_time.append((candidate, committed_at))
                    if len(candidates_with_time) > MAX_COMMITS:
                        raise SiteModelHistoryProfileError(
                            "site-tool history exceeds commit policy"
                        )
                next_page = _pagination_next(response.headers, expected_page=page)
        except SiteModelHistoryProfileError:
            raise
        except (OSError, TimeoutError, transport.EfehrAcquisitionError) as exc:
            raise SiteModelHistoryProfileError(
                "site-tool history metadata acquisition failed closed"
            ) from exc
        pages_read += 1
        if next_page is None:
            break
        page = next_page

    if pages_read < 1 or not candidates_with_time:
        raise SiteModelHistoryProfileError("site-tool fixed history window is empty")

    candidates_with_time.sort(key=lambda item: (-item[1].timestamp(), item[0]["commit_sha"]))
    candidates = [candidate for candidate, _ in candidates_with_time]

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "ref_name": REF_NAME,
        "since_utc": SINCE_UTC,
        "until_utc": UNTIL_UTC,
        "pages_read": pages_read,
        "candidate_commit_count": len(candidates),
        "history_identity_sha256": _history_sha256(candidates),
        "candidate_commits": candidates,
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "exact_kosovo_generator_commit_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "site_model_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
