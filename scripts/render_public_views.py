# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Render and verify deterministic human-readable views of canonical public data contracts."""

from __future__ import annotations

import argparse
import difflib
import html
import json
import sys
from pathlib import Path
from typing import Any

if __package__:
    from .source_landscape_contract import (
        LandscapeContractError,
        load_landscape_shard,
        load_landscape_shards,
    )
else:
    from source_landscape_contract import (
        LandscapeContractError,
        load_landscape_shard,
        load_landscape_shards,
    )

ROOT = Path(__file__).resolve().parents[1]
LANDSCAPE_DIR = ROOT / "landscape"
ACCESS_DIR = ROOT / "access"
MANIFESTS_DIR = ROOT / "manifests"
GENERATED_MARKER = "GENERATED FILE — DO NOT EDIT DIRECTLY"
# Keep the generated SPDX line split in this source so REUSE does not parse it as
# a second licence declaration belonging to this Python file.
GENERATED_SPDX_LICENSE_LINE = "SPDX-" + "License-Identifier: Apache-2.0"


class ProjectionError(ValueError):
    """Raised when a canonical object cannot be projected deterministically."""


def load_canonical_json(path: Path) -> dict[str, Any]:
    """Load a canonical landscape shard through the authoritative contract."""

    try:
        return load_landscape_shard(path)
    except LandscapeContractError as exc:
        raise ProjectionError(str(exc)) from exc


def _text(value: Any, *, field: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectionError(f"{path}: {field} must be a non-empty string")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    return html.escape(normalized, quote=False).replace("\n", "<br>")


def _string_list(value: Any, *, field: str, path: Path) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ProjectionError(f"{path}: {field} must be a non-empty array of strings")
    return tuple(value)


def _code(value: str) -> str:
    return f"`{html.escape(value, quote=False).replace('`', '&#96;')}`"


def _code_list(values: tuple[str, ...]) -> str:
    return ", ".join(_code(value) for value in values)


def render_landscape_markdown(path: Path, payload: dict[str, Any]) -> str:
    schema_version = _text(payload.get("schema_version"), field="schema_version", path=path)
    purpose = _text(payload.get("purpose"), field="purpose", path=path)
    review_date = _text(payload.get("review_date"), field="review_date", path=path)
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ProjectionError(f"{path}: entries must be a non-empty array")

    try:
        canonical_source = path.relative_to(ROOT).as_posix()
    except ValueError:
        canonical_source = path.as_posix()

    lines = [
        "<!--",
        "SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors",
        GENERATED_SPDX_LICENSE_LINE,
        "",
        GENERATED_MARKER,
        f"Canonical source: {canonical_source}",
        "Renderer: scripts/render_public_views.py",
        "Change the canonical JSON and run `python scripts/render_public_views.py --write`.",
        "-->",
        "",
        f"# Source landscape: `{path.name}`",
        "",
        "> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. "
        "It does not create a second source of truth or change admission, rights or scientific-review state.",
        "",
        f"**Schema version:** {_code(html.unescape(schema_version))}  ",
        f"**Review date:** {_code(html.unescape(review_date))}  ",
        f"**Purpose:** {purpose}",
        "",
        f"**Entries:** {len(entries)}",
        "",
    ]

    for index, raw_entry in enumerate(entries, start=1):
        if not isinstance(raw_entry, dict):
            raise ProjectionError(f"{path}: entry {index} must be an object")
        candidate_id = _text(raw_entry.get("candidate_id"), field="candidate_id", path=path)
        name = _text(raw_entry.get("name"), field="name", path=path)
        provider = _text(raw_entry.get("provider"), field="provider", path=path)
        categories = _string_list(raw_entry.get("categories"), field="categories", path=path)
        spatial_scope = _text(raw_entry.get("spatial_scope"), field="spatial_scope", path=path)
        temporal_scope = _text(raw_entry.get("temporal_scope"), field="temporal_scope", path=path)
        granularity = _text(
            raw_entry.get("resolution_or_granularity"),
            field="resolution_or_granularity",
            path=path,
        )
        roles = _string_list(raw_entry.get("potential_roles"), field="potential_roles", path=path)
        authoritative_url = _text(raw_entry.get("authoritative_url"), field="authoritative_url", path=path)
        access_class_hint = _text(raw_entry.get("access_class_hint"), field="access_class_hint", path=path)
        candidate_status = _text(raw_entry.get("candidate_status"), field="candidate_status", path=path)
        rights_status = _text(raw_entry.get("rights_review_status"), field="rights_review_status", path=path)
        scientific_status = _text(
            raw_entry.get("scientific_review_status"),
            field="scientific_review_status",
            path=path,
        )
        admission_status = _text(raw_entry.get("admission_status"), field="admission_status", path=path)
        note = _text(raw_entry.get("note"), field="note", path=path)

        lines.extend(
            [
                f"## {name}",
                "",
                f"**Candidate ID:** {_code(html.unescape(candidate_id))}  ",
                f"**Provider:** {provider}  ",
                f"**Categories:** {_code_list(categories)}  ",
                f"**Spatial scope:** {spatial_scope}  ",
                f"**Temporal scope:** {temporal_scope}  ",
                f"**Resolution / granularity:** {granularity}  ",
                f"**Potential roles:** {_code_list(roles)}  ",
                f"**Access hint:** {_code(html.unescape(access_class_hint))}  ",
                f"**Authoritative source:** <{html.unescape(authoritative_url)}>  ",
                "**Review state:** "
                f"candidate {_code(html.unescape(candidate_status))}; "
                f"rights {_code(html.unescape(rights_status))}; "
                f"scientific {_code(html.unescape(scientific_status))}; "
                f"admission {_code(html.unescape(admission_status))}.",
                "",
                f"**Note:** {note}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def expected_landscape_projections(directory: Path = LANDSCAPE_DIR) -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    try:
        shards = load_landscape_shards(directory)
    except LandscapeContractError as exc:
        raise ProjectionError(str(exc)) from exc
    for source_path, payload in shards:
        output_path = source_path.with_suffix(".md")
        outputs[output_path] = render_landscape_markdown(source_path, payload)
    return outputs


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProjectionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_finite(value: str) -> None:
    raise ProjectionError(f"non-finite JSON number is not allowed: {value}")


def load_structured_json(path: Path) -> tuple[dict[str, Any], str]:
    """Strictly load a public access/manifest object and return normalized JSON text."""

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ProjectionError(f"{path}: cannot read canonical JSON: {exc}") from exc
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    try:
        payload = json.loads(
            normalized,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite,
        )
    except ProjectionError:
        raise
    except json.JSONDecodeError as exc:
        raise ProjectionError(f"{path}: invalid JSON: {exc.msg}") from exc
    if type(payload) is not dict:
        raise ProjectionError(f"{path}: canonical public record must be a JSON object")
    return payload, normalized.rstrip("\n") + "\n"


def render_structured_markdown(path: Path, canonical_json: str, *, record_kind: str) -> str:
    """Render a lossless public record view without reinterpreting canonical semantics."""

    try:
        canonical_source = path.relative_to(ROOT).as_posix()
    except ValueError:
        canonical_source = path.as_posix()
    title = "Access contract" if record_kind == "access" else "Dataset manifest"
    lines = [
        "<!--",
        "SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors",
        GENERATED_SPDX_LICENSE_LINE,
        "",
        GENERATED_MARKER,
        f"Canonical source: {canonical_source}",
        "Renderer: scripts/render_public_views.py",
        "Change the canonical JSON and run `python scripts/render_public_views.py --write`.",
        "-->",
        "",
        f"# {title}: `{path.name}`",
        "",
        "> This Markdown file is a deterministic, lossless human-readable projection of the canonical JSON file named above. "
        "The JSON remains authoritative; this projection does not change rights, admission, publication or scientific-review state.",
        "",
        "```json",
        canonical_json.rstrip("\n"),
        "```",
        "",
    ]
    return "\n".join(lines)


def expected_structured_projections(directory: Path, *, record_kind: str) -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    for source_path in sorted(directory.glob("*.json")):
        _payload, canonical_json = load_structured_json(source_path)
        outputs[source_path.with_suffix(".md")] = render_structured_markdown(
            source_path,
            canonical_json,
            record_kind=record_kind,
        )
    return outputs


def _generated_orphan_paths(
    directory: Path,
    expected: set[Path],
    *,
    pattern: str = "sources*.md",
) -> tuple[Path, ...]:
    orphans: list[Path] = []
    for path in sorted(directory.glob(pattern)):
        if path in expected:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if GENERATED_MARKER in text:
            orphans.append(path)
    return tuple(orphans)


def _write_projection_set(
    directory: Path,
    outputs: dict[Path, str],
    *,
    orphan_pattern: str,
) -> tuple[Path, ...]:
    written: list[Path] = []
    for path, expected in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != expected:
            path.write_text(expected, encoding="utf-8", newline="\n")
            written.append(path)
    for orphan in _generated_orphan_paths(
        directory,
        set(outputs),
        pattern=orphan_pattern,
    ):
        orphan.unlink()
        written.append(orphan)
    return tuple(written)


def _check_projection_set(
    directory: Path,
    outputs: dict[Path, str],
    *,
    orphan_pattern: str,
    label: str,
    stream: Any,
) -> bool:
    ok = True
    for path, expected in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current == expected:
            continue
        ok = False
        path_label = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()
        print(f"DRIFT: {path_label} does not match its canonical JSON source", file=stream)
        diff = difflib.unified_diff(
            current.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile=path_label,
            tofile=f"expected:{path_label}",
        )
        for line in diff:
            print(line, end="", file=stream)

    for orphan in _generated_orphan_paths(
        directory,
        set(outputs),
        pattern=orphan_pattern,
    ):
        ok = False
        path_label = orphan.relative_to(ROOT).as_posix() if orphan.is_relative_to(ROOT) else orphan.as_posix()
        print(f"DRIFT: orphan generated projection has no canonical JSON source: {path_label}", file=stream)

    if ok:
        print(f"PASS: {len(outputs)} {label} Markdown projections match canonical JSON", file=stream)
    return ok


def write_landscape_projections(directory: Path = LANDSCAPE_DIR) -> tuple[Path, ...]:
    return _write_projection_set(
        directory,
        expected_landscape_projections(directory),
        orphan_pattern="sources*.md",
    )


def check_landscape_projections(directory: Path = LANDSCAPE_DIR, *, stream: Any = sys.stdout) -> bool:
    return _check_projection_set(
        directory,
        expected_landscape_projections(directory),
        orphan_pattern="sources*.md",
        label="landscape",
        stream=stream,
    )


def write_structured_projections(directory: Path, *, record_kind: str) -> tuple[Path, ...]:
    return _write_projection_set(
        directory,
        expected_structured_projections(directory, record_kind=record_kind),
        orphan_pattern="*.md",
    )


def check_structured_projections(
    directory: Path,
    *,
    record_kind: str,
    stream: Any = sys.stdout,
) -> bool:
    return _check_projection_set(
        directory,
        expected_structured_projections(directory, record_kind=record_kind),
        orphan_pattern="*.md",
        label=record_kind,
        stream=stream,
    )


def write_public_projections(scope: str = "all") -> tuple[Path, ...]:
    changed: list[Path] = []
    if scope in {"all", "landscape"}:
        changed.extend(write_landscape_projections())
    if scope in {"all", "access"}:
        changed.extend(write_structured_projections(ACCESS_DIR, record_kind="access"))
    if scope in {"all", "manifests"}:
        changed.extend(write_structured_projections(MANIFESTS_DIR, record_kind="manifests"))
    return tuple(changed)


def check_public_projections(scope: str = "all", *, stream: Any = sys.stdout) -> bool:
    checks: list[bool] = []
    if scope in {"all", "landscape"}:
        checks.append(check_landscape_projections(stream=stream))
    if scope in {"all", "access"}:
        checks.append(check_structured_projections(ACCESS_DIR, record_kind="access", stream=stream))
    if scope in {"all", "manifests"}:
        checks.append(check_structured_projections(MANIFESTS_DIR, record_kind="manifests", stream=stream))
    return all(checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Regenerate committed human-readable projections")
    mode.add_argument("--check", action="store_true", help="Fail if committed projections differ from canonical JSON")
    parser.add_argument(
        "--scope",
        choices=("all", "landscape", "access", "manifests"),
        default="all",
        help="Projection family to write/check; default: all",
    )
    args = parser.parse_args(argv)

    try:
        if args.write:
            changed = write_public_projections(args.scope)
            if changed:
                for path in changed:
                    print(path.relative_to(ROOT).as_posix())
            else:
                print("PASS: public projections already current")
            return 0
        return 0 if check_public_projections(args.scope) else 1
    except ProjectionError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
