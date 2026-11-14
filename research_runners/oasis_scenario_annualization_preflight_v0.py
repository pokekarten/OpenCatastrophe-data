# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed, offline preflight for deterministic Oasis scenario metadata.

This tool reads user-provided public CSV/JSON source bytes from local paths.
It does not download data or run Oasis, and a successful result must never be
interpreted as annualized losses, an approved source or a model calibration.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import re
import sys

MAX_BYTES = 1_000_000
MAX_ROWS = 50_000
EVENT_FIELDS = ("event_id",)
OCCURRENCE_FIELDS = ("event_id", "period_no", "occ_year", "occ_month", "occ_day")
BLOB_RE = re.compile(r"^[0-9a-f]{40}$")
INTEGER_RE = re.compile(r"^[1-9][0-9]*$")


class ScenarioPreflightError(ValueError):
    """Untrusted local source data is malformed or cannot be authenticated."""


def git_blob_sha1(data: bytes) -> str:
    """Reproduce Git's blob identity from exact original bytes."""
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def read_source(path: Path, expected_git_blob: str | None = None) -> tuple[str, str]:
    if expected_git_blob is not None and not BLOB_RE.fullmatch(expected_git_blob):
        raise ScenarioPreflightError("expected Git blob must be a lower-case 40-character SHA-1")
    if not path.is_file():
        raise ScenarioPreflightError("source path must be an existing regular file")
    if path.stat().st_size > MAX_BYTES:
        raise ScenarioPreflightError("source exceeds bounded preflight size limit")
    try:
        raw = path.read_bytes()
        if not raw or len(raw) > MAX_BYTES or b"\0" in raw:
            raise ScenarioPreflightError("empty, oversized or binary source")
        digest = git_blob_sha1(raw)
        if expected_git_blob is not None and digest != expected_git_blob:
            raise ScenarioPreflightError("original source Git blob differs from pinned identity")
        return raw.decode("utf-8"), digest
    except (OSError, UnicodeError) as exc:
        raise ScenarioPreflightError("unable to read strict UTF-8 original source") from exc


def read_csv(source: str, expected: tuple[str, ...]) -> list[tuple[str, ...]]:
    try:
        reader = csv.reader(io.StringIO(source, newline=""), strict=True)
        header = next(reader, None)
        if header != list(expected):
            raise ScenarioPreflightError("CSV fields differ from exact supported scenario format")
        rows: list[tuple[str, ...]] = []
        for row in reader:
            if len(rows) >= MAX_ROWS:
                raise ScenarioPreflightError("CSV row budget exceeded")
            if len(row) != len(expected) or not all(row):
                raise ScenarioPreflightError("missing or unexpected scenario CSV field")
            rows.append(tuple(row))
    except (csv.Error, UnicodeError) as exc:
        raise ScenarioPreflightError("malformed scenario CSV") from exc
    if not rows:
        raise ScenarioPreflightError("scenario CSV must have at least one data row")
    return rows


def positive_int(value: str, *, maximum: int = 2_147_483_647) -> int:
    if not INTEGER_RE.fullmatch(value) or len(value) > 10:
        raise ScenarioPreflightError("scenario identifiers and dates must be positive decimal integers")
    number = int(value)
    if number > maximum:
        raise ScenarioPreflightError("scenario integer exceeds its allowed bound")
    return number


def audit_occurrences(
    events_text: str,
    occurrences_text: str,
    *,
    events_blob: str,
    occurrences_blob: str,
) -> dict[str, object]:
    event_rows = read_csv(events_text, EVENT_FIELDS)
    occurrence_rows = read_csv(occurrences_text, OCCURRENCE_FIELDS)
    events = [positive_int(row[0]) for row in event_rows]
    if len(set(events)) != len(events):
        raise ScenarioPreflightError("duplicate event identifier in events.csv")
    event_ids = set(events)
    seen_occurrences: set[tuple[int, int, int, int, int]] = set()
    observed_event_ids: set[int] = set()
    periods: dict[int, int] = {}
    for event_id_s, period_s, year_s, month_s, day_s in occurrence_rows:
        event_id = positive_int(event_id_s)
        period = positive_int(period_s)
        year = positive_int(year_s, maximum=9999)
        month = positive_int(month_s, maximum=12)
        day = positive_int(day_s, maximum=31)
        try:
            date(year, month, day)
        except ValueError as exc:
            raise ScenarioPreflightError("invalid occurrence calendar date") from exc
        if event_id not in event_ids:
            raise ScenarioPreflightError("occurrence uses an event missing from events.csv")
        row_identity = (event_id, period, year, month, day)
        if row_identity in seen_occurrences:
            raise ScenarioPreflightError("identical occurrence row repeated")
        seen_occurrences.add(row_identity)
        observed_event_ids.add(event_id)
        periods[period] = periods.get(period, 0) + 1
    if observed_event_ids != event_ids:
        raise ScenarioPreflightError("event in events.csv has no matching occurrence row")
    # These CSVs alone do not supply a complete probability measure, reliable
    # physical-event equivalence or economic loss/policy/treaty semantics.
    return {
        "kind": "oasis_deterministic_occurrence_preflight_v0",
        "status": "parsed_but_not_annualized",
        "event_ids_count": len(events),
        "occurrence_rows_count": len(occurrence_rows),
        "represented_periods_count": len(periods),
        "max_occurrence_rows_in_one_period": max(periods.values()),
        "all_rows_same_period": len(periods) == 1,
        "events_git_blob_sha1": events_blob,
        "occurrences_git_blob_sha1": occurrences_blob,
        "annual_period_universe_complete": False,
        "annual_period_weights_verified": False,
        "physical_occurrence_identity_verified": False,
        "vulnerability_and_hazard_validated": False,
        "oasis_model_run_verified": False,
        "insured_or_reinsured_loss_established": False,
        "annual_oep_aep_authorized": False,
        "reason": "Event IDs and occurrence rows alone are not a calibrated annual stochastic catalogue. Even when the analysis config requests AEP/OEP, it cannot establish occurrence probabilities or insured/net loss.",
    }


def strict_json(source: str) -> dict[str, object]:
    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise ScenarioPreflightError("duplicate key in model settings JSON")
            value[key] = item
        return value

    def reject_constant(value: str) -> None:
        raise ScenarioPreflightError("non-finite model settings JSON number")

    try:
        payload = json.loads(source, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except json.JSONDecodeError as exc:
        raise ScenarioPreflightError("invalid model settings JSON") from exc
    if not isinstance(payload, dict):
        raise ScenarioPreflightError("model settings JSON must contain a top-level object")
    return payload


def audit_event_set_options(source: str, *, settings_blob: str) -> dict[str, object]:
    payload = strict_json(source)
    model_settings = payload.get("model_settings")
    if not isinstance(model_settings, dict):
        raise ScenarioPreflightError("model_settings must be a JSON object")
    selector = model_settings.get("event_set")
    if not isinstance(selector, dict):
        raise ScenarioPreflightError("missing event_set selector")
    options = selector.get("options")
    if not isinstance(options, list) or not options or len(options) > 100:
        raise ScenarioPreflightError("event_set options must be a nonempty bounded array")
    identifiers: set[str] = set()
    total_option_rows = 0
    for option in options:
        if not isinstance(option, dict):
            raise ScenarioPreflightError("invalid event_set option")
        identifier = option.get("id")
        count = option.get("number_of_events")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9_-]{1,80}", identifier):
            raise ScenarioPreflightError("invalid event_set option identifier")
        if identifier in identifiers:
            raise ScenarioPreflightError("duplicate event_set option identifier")
        if type(count) is not int or not 1 <= count <= MAX_ROWS:
            raise ScenarioPreflightError("event_set number_of_events must be a positive integer")
        identifiers.add(identifier)
        total_option_rows += count
    default = selector.get("default")
    if not isinstance(default, str):
        raise ScenarioPreflightError("event_set default must be a string")
    return {
        "kind": "oasis_event_set_selector_preflight_v0",
        "status": "parsed_but_not_annualized",
        "option_count": len(options),
        "sum_declared_option_event_counts": total_option_rows,
        "default_matches_a_declared_option": default in identifiers,
        "model_settings_git_blob_sha1": settings_blob,
        "options_are_independent_physical_events": False,
        "alternative_footprints_are_independent_samples": False,
        "oasis_model_run_verified": False,
        "annual_oep_aep_authorized": False,
        "reason": "Event-set selection is not a joint annual catalogue or a probability model; declared per-option event counts cannot be summed as independently occurring physical storms.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    occurrences = sub.add_parser("occurrences", help="inspect events.csv and occurrence.csv")
    occurrences.add_argument("events", type=Path)
    occurrences.add_argument("occurrence", type=Path)
    occurrences.add_argument("--events-git-blob")
    occurrences.add_argument("--occurrence-git-blob")
    selector = sub.add_parser("event-sets", help="inspect model_settings.json event-set options")
    selector.add_argument("settings", type=Path)
    selector.add_argument("--settings-git-blob")
    args = parser.parse_args(argv)
    try:
        if args.action == "occurrences":
            event_text, event_blob = read_source(args.events, args.events_git_blob)
            occurrence_text, occurrence_blob = read_source(args.occurrence, args.occurrence_git_blob)
            result = audit_occurrences(event_text, occurrence_text, events_blob=event_blob, occurrences_blob=occurrence_blob)
        else:
            settings_text, settings_blob = read_source(args.settings, args.settings_git_blob)
            result = audit_event_set_options(settings_text, settings_blob=settings_blob)
    except ScenarioPreflightError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
