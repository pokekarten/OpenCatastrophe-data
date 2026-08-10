# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail closed when a pull request changes files claimed by another open PR.

This checker is intentionally narrow. It proves exact changed-file non-overlap
(including the old path of renamed files); it does not replace the repository's
manual shared/single-writer semantic-contract review in ``AGENTS.md``.

The check is a claim-time guard, not a distributed lock: a competing PR opened
later must run the same check, and maintainers still re-check current ``main``
and active claims immediately before merge.

The script uses only the Python standard library and GitHub's REST API. It is
safe to run with a read-only ``GITHUB_TOKEN``. A later workflow change can wire
it into pull-request CI once the CI-policy surface is not owned by another PR.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

API_VERSION = "2026-03-10"
PER_PAGE = 100
MAX_OPEN_PR_PAGES = 100
MAX_PR_FILE_PAGES = 30  # GitHub documents a hard maximum of 3,000 PR files.
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class CollisionCheckError(ValueError):
    """Raised when non-overlap cannot be established safely."""


def _positive_int(value: Any, where: str) -> int:
    if type(value) is not int or value <= 0:
        raise CollisionCheckError(f"{where} must be a positive integer")
    return value


def require_repository(value: Any) -> str:
    """Validate an ``owner/repository`` identity without accepting URL syntax."""

    if type(value) is not str or value != value.strip() or not REPOSITORY_RE.fullmatch(value):
        raise CollisionCheckError("repository must be a canonical owner/name identity")
    return value


def require_api_url(value: Any) -> str:
    """Require an HTTPS GitHub API base URL and remove a trailing slash."""

    if type(value) is not str or value != value.strip() or not value:
        raise CollisionCheckError("GitHub API URL must be a non-empty trimmed string")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
        raise CollisionCheckError("GitHub API URL must be an HTTPS base URL without query/fragment")
    return value.rstrip("/")


def read_event_pull_request_number(path: Path) -> int:
    """Read the current PR number from a GitHub ``pull_request`` event payload."""

    if not isinstance(path, Path):
        raise CollisionCheckError("event path must be a pathlib.Path")
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CollisionCheckError(f"cannot read GitHub event payload: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CollisionCheckError("GitHub event payload must be valid JSON") from exc
    if type(payload) is not dict or type(payload.get("pull_request")) is not dict:
        raise CollisionCheckError("GitHub event payload is not a pull_request event")
    return _positive_int(payload["pull_request"].get("number"), "pull_request.number")


def _api_get_json(url: str, *, token: str, timeout_seconds: int = 30) -> Any:
    """Fetch one GitHub REST response without exposing the authentication token."""

    if type(token) is not str or not token:
        raise CollisionCheckError("GITHUB_TOKEN is required for the collision check")
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "OpenCatastrophe-pr-file-collision-checker",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - URL is validated GitHub API input.
            body = response.read()
    except HTTPError as exc:
        raise CollisionCheckError(f"GitHub API request failed with HTTP {exc.code}") from exc
    except URLError as exc:
        raise CollisionCheckError(f"GitHub API request failed: {exc.reason}") from exc
    except OSError as exc:
        raise CollisionCheckError(f"GitHub API request failed: {exc}") from exc
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CollisionCheckError("GitHub API returned invalid UTF-8 JSON") from exc


def collect_paginated(
    fetch_page: Callable[[int], Any],
    *,
    max_pages: int,
    label: str,
) -> list[Any]:
    """Collect full 100-item pages and fail closed at a documented API ceiling."""

    _positive_int(max_pages, "max_pages")
    items: list[Any] = []
    for page in range(1, max_pages + 1):
        batch = fetch_page(page)
        if type(batch) is not list:
            raise CollisionCheckError(f"GitHub API {label} page {page} must be a JSON array")
        if len(batch) > PER_PAGE:
            raise CollisionCheckError(f"GitHub API {label} page {page} exceeds per_page={PER_PAGE}")
        items.extend(batch)
        if len(batch) < PER_PAGE:
            return items
    raise CollisionCheckError(
        f"GitHub API {label} reached the configured/documented completeness limit; "
        "non-overlap cannot be proven"
    )


def list_open_pull_request_numbers(
    repository: str,
    *,
    api_url: str,
    token: str,
    get_json: Callable[..., Any] = _api_get_json,
) -> tuple[int, ...]:
    """Return every currently open pull-request number for one repository."""

    owner, name = require_repository(repository).split("/", 1)
    api_url = require_api_url(api_url)
    base = f"{api_url}/repos/{quote(owner, safe='')}/{quote(name, safe='')}/pulls"

    def fetch_page(page: int) -> Any:
        return get_json(
            f"{base}?state=open&per_page={PER_PAGE}&page={page}",
            token=token,
        )

    records = collect_paginated(fetch_page, max_pages=MAX_OPEN_PR_PAGES, label="open pull requests")
    numbers: list[int] = []
    for index, record in enumerate(records):
        if type(record) is not dict:
            raise CollisionCheckError(f"open pull request record {index} must be an object")
        numbers.append(_positive_int(record.get("number"), f"open pull request record {index}.number"))
    if len(numbers) != len(set(numbers)):
        raise CollisionCheckError("GitHub API returned duplicate open pull-request numbers")
    return tuple(sorted(numbers))


def _file_record_surfaces(record: Any, where: str) -> tuple[str, ...]:
    """Return current and previous paths claimed by one changed-file record."""

    if type(record) is not dict:
        raise CollisionCheckError(f"{where} must be an object")
    filename = record.get("filename")
    if type(filename) is not str or not filename or filename != filename.strip() or "\x00" in filename:
        raise CollisionCheckError(f"{where}.filename must be a non-empty trimmed path")
    surfaces = [filename]
    previous = record.get("previous_filename")
    if previous is not None:
        if type(previous) is not str or not previous or previous != previous.strip() or "\x00" in previous:
            raise CollisionCheckError(f"{where}.previous_filename must be a non-empty trimmed path")
        surfaces.append(previous)
    return tuple(surfaces)


def list_pull_request_file_surfaces(
    repository: str,
    pull_request_number: int,
    *,
    api_url: str,
    token: str,
    get_json: Callable[..., Any] = _api_get_json,
) -> frozenset[str]:
    """Return all changed paths, including old paths for renamed files."""

    owner, name = require_repository(repository).split("/", 1)
    number = _positive_int(pull_request_number, "pull request number")
    api_url = require_api_url(api_url)
    base = (
        f"{api_url}/repos/{quote(owner, safe='')}/{quote(name, safe='')}"
        f"/pulls/{number}/files"
    )

    def fetch_page(page: int) -> Any:
        return get_json(f"{base}?per_page={PER_PAGE}&page={page}", token=token)

    records = collect_paginated(fetch_page, max_pages=MAX_PR_FILE_PAGES, label=f"PR #{number} files")
    surfaces: set[str] = set()
    for index, record in enumerate(records):
        surfaces.update(_file_record_surfaces(record, f"PR #{number} file record {index}"))
    return frozenset(surfaces)


def find_collisions(
    current_pull_request: int,
    open_pull_requests: Iterable[int],
    load_surfaces: Callable[[int], frozenset[str]],
) -> tuple[frozenset[str], dict[int, tuple[str, ...]]]:
    """Compare the current PR with every other open PR using exact paths."""

    current = _positive_int(current_pull_request, "current pull request")
    try:
        open_numbers = tuple(open_pull_requests)
    except TypeError as exc:
        raise CollisionCheckError("open_pull_requests must be iterable") from exc
    normalized: list[int] = []
    for index, number in enumerate(open_numbers):
        normalized.append(_positive_int(number, f"open_pull_requests[{index}]"))
    if len(normalized) != len(set(normalized)):
        raise CollisionCheckError("open_pull_requests must not contain duplicates")

    current_surfaces = load_surfaces(current)
    if not isinstance(current_surfaces, frozenset) or any(type(path) is not str for path in current_surfaces):
        raise CollisionCheckError("load_surfaces must return frozenset[str]")

    collisions: dict[int, tuple[str, ...]] = {}
    for number in sorted(normalized):
        if number == current:
            continue
        other_surfaces = load_surfaces(number)
        if not isinstance(other_surfaces, frozenset) or any(type(path) is not str for path in other_surfaces):
            raise CollisionCheckError("load_surfaces must return frozenset[str]")
        overlap = tuple(sorted(current_surfaces.intersection(other_surfaces)))
        if overlap:
            collisions[number] = overlap
    return current_surfaces, collisions


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", help="GitHub owner/name; defaults to GITHUB_REPOSITORY")
    parser.add_argument("--pull-request", type=int, help="current PR number; defaults to GITHUB_EVENT_PATH")
    parser.add_argument("--event-path", type=Path, help="pull_request event JSON; defaults to GITHUB_EVENT_PATH")
    parser.add_argument("--api-url", help="GitHub API base URL; defaults to GITHUB_API_URL")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        repository = require_repository(args.repository or os.environ.get("GITHUB_REPOSITORY"))
        api_url = require_api_url(args.api_url or os.environ.get("GITHUB_API_URL", "https://api.github.com"))
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            raise CollisionCheckError("GITHUB_TOKEN is required for the collision check")

        if args.pull_request is not None:
            current_pr = _positive_int(args.pull_request, "--pull-request")
        else:
            event_path_value = args.event_path or (
                Path(os.environ["GITHUB_EVENT_PATH"]) if os.environ.get("GITHUB_EVENT_PATH") else None
            )
            if event_path_value is None:
                raise CollisionCheckError("pull-request number requires --pull-request or GITHUB_EVENT_PATH")
            current_pr = read_event_pull_request_number(event_path_value)

        open_prs = list_open_pull_request_numbers(
            repository,
            api_url=api_url,
            token=token,
        )

        def load_surfaces(number: int) -> frozenset[str]:
            return list_pull_request_file_surfaces(
                repository,
                number,
                api_url=api_url,
                token=token,
            )

        current_surfaces, collisions = find_collisions(current_pr, open_prs, load_surfaces)
    except CollisionCheckError as exc:
        print(f"BLOCKED: PR file-collision check could not prove non-overlap: {exc}")
        return 2

    if collisions:
        print(f"BLOCKED: PR #{current_pr} changes files claimed by other open pull requests:")
        for number, paths in collisions.items():
            print(f"  PR #{number}:")
            for path in paths:
                print(f"    - {path}")
        print("Coordinate on the existing PR or choose an independent task before writing these surfaces.")
        return 1

    compared = sum(1 for number in open_prs if number != current_pr)
    print(
        f"PASS: PR #{current_pr} has no exact changed-file overlap with "
        f"{compared} other open PR(s); {len(current_surfaces)} claimed path(s) checked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
