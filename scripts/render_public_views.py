# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Render and verify deterministic human-readable views of canonical public data contracts."""

from __future__ import annotations

import argparse
import difflib
import html
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


def _generated_orphan_paths(directory: Path, expected: set[Path]) -> tuple[Path, ...]:
    orphans: list[Path] = []
    for path in sorted(directory.glob("sources*.md")):
        if path in expected:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if GENERATED_MARKER in text:
            orphans.append(path)
    return tuple(orphans)


def write_landscape_projections(directory: Path = LANDSCAPE_DIR) -> tuple[Path, ...]:
    outputs = expected_landscape_projections(directory)
    written: list[Path] = []
    for path, expected in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != expected:
            path.write_text(expected, encoding="utf-8", newline="\n")
            written.append(path)
    for orphan in _generated_orphan_paths(directory, set(outputs)):
        orphan.unlink()
        written.append(orphan)
    return tuple(written)


def check_landscape_projections(directory: Path = LANDSCAPE_DIR, *, stream: Any = sys.stdout) -> bool:
    outputs = expected_landscape_projections(directory)
    ok = True
    for path, expected in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current == expected:
            continue
        ok = False
        label = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()
        print(f"DRIFT: {label} does not match its canonical JSON source", file=stream)
        diff = difflib.unified_diff(
            current.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile=label,
            tofile=f"expected:{label}",
        )
        for line in diff:
            print(line, end="", file=stream)

    for orphan in _generated_orphan_paths(directory, set(outputs)):
        ok = False
        label = orphan.relative_to(ROOT).as_posix() if orphan.is_relative_to(ROOT) else orphan.as_posix()
        print(f"DRIFT: orphan generated projection has no canonical JSON source: {label}", file=stream)

    if ok:
        print(f"PASS: {len(outputs)} landscape Markdown projections match canonical JSON", file=stream)
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Regenerate committed human-readable projections")
    mode.add_argument("--check", action="store_true", help="Fail if committed projections differ from canonical JSON")
    args = parser.parse_args(argv)

    try:
        if args.write:
            changed = write_landscape_projections()
            if changed:
                for path in changed:
                    print(path.relative_to(ROOT).as_posix())
            else:
                print("PASS: public projections already current")
            return 0
        return 0 if check_landscape_projections() else 1
    except ProjectionError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
