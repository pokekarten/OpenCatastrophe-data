# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Deterministic Markdown projections for structured repository JSON records."""

from __future__ import annotations

import difflib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ACCESS_DIR = ROOT / "access"
MANIFEST_DIR = ROOT / "manifests"
SCHEMA_DIR = ROOT / "schemas"
GENERATED_MARKER = "GENERATED FILE — DO NOT EDIT DIRECTLY"
GENERATED_SPDX_LICENSE_LINE = "SPDX-" + "License-Identifier: Apache-2.0"
MARKDOWN_ESCAPE_RE = re.compile(r"([\\`*\[\]{}#!|])")
FULL_HTTPS_URL_RE = re.compile(r"https://[^\s<>]+$")
CAMEL_CASE_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


class ProjectionError(ValueError):
    """Raised when a structured public record cannot be projected safely."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProjectionError(f"{key}: duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ProjectionError(f"non-finite JSON number is not allowed: {value}")


def load_structured_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except ProjectionError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProjectionError(f"{path}: unable to read strict JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ProjectionError(f"{path}: canonical public record must be a JSON object")
    return payload


def _label(key: str) -> str:
    if key.startswith("$"):
        return key
    normalized = key.replace("_", " ").replace("-", " ")
    normalized = CAMEL_CASE_BOUNDARY_RE.sub(" ", normalized)
    return normalized.strip().capitalize()


def _markdown_text(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    if FULL_HTTPS_URL_RE.fullmatch(normalized):
        return f"<{html.escape(normalized, quote=False)}>"
    escaped = MARKDOWN_ESCAPE_RE.sub(r"\\\1", html.escape(normalized, quote=False))
    return escaped.replace("\n", "<br>")


def _scalar(value: Any) -> str:
    if value is None:
        return "`null`"
    if isinstance(value, bool):
        return "`true`" if value else "`false`"
    if isinstance(value, (int, float)):
        return f"`{value}`"
    if isinstance(value, str):
        return _markdown_text(value)
    raise ProjectionError(f"unsupported JSON scalar type: {type(value).__name__}")


def _heading(level: int, text: str) -> str:
    return f"{'#' * min(level, 6)} {text}"


def _render_list(lines: list[str], values: list[Any], *, level: int) -> None:
    if not values:
        lines.extend(["_Empty array._", ""])
        return
    for index, item in enumerate(values, start=1):
        if isinstance(item, dict):
            lines.extend([_heading(level, f"Item {index}"), ""])
            if not item:
                lines.extend(["_Empty object._", ""])
            for key, value in item.items():
                _render_field(lines, key, value, level=level + 1)
        elif isinstance(item, list):
            lines.extend([_heading(level, f"Item {index}"), ""])
            _render_list(lines, item, level=level + 1)
        else:
            lines.append(f"- {_scalar(item)}")
    lines.append("")


def _render_field(lines: list[str], key: str, value: Any, *, level: int) -> None:
    label = _label(key)
    if isinstance(value, dict):
        lines.extend([_heading(level, label), ""])
        if not value:
            lines.extend(["_Empty object._", ""])
        for child_key, child_value in value.items():
            _render_field(lines, child_key, child_value, level=level + 1)
    elif isinstance(value, list):
        lines.extend([_heading(level, label), ""])
        _render_list(lines, value, level=level + 1)
    else:
        lines.extend([f"**{label}:** {_scalar(value)}", ""])


def render_structured_markdown(path: Path, payload: dict[str, Any], *, kind: str) -> str:
    titles = {
        "access": "Source access contract",
        "manifest": "Dataset manifest",
        "schema": "JSON Schema",
    }
    if kind not in titles:
        raise ProjectionError(f"unsupported public record kind: {kind}")
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
        f"# {titles[kind]}: `{path.name}`",
        "",
        "> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. "
        "The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.",
        "",
    ]
    for key, value in payload.items():
        _render_field(lines, key, value, level=2)
    return "\n".join(lines).rstrip() + "\n"


def expected_structured_projections(directory: Path, *, kind: str) -> dict[Path, str]:
    paths = tuple(sorted(directory.glob("*.json")))
    if not paths:
        raise ProjectionError(f"{directory}: no canonical JSON public records found")
    return {
        path.with_suffix(".md"): render_structured_markdown(path, load_structured_json(path), kind=kind)
        for path in paths
    }


def _generated_orphans(directory: Path, expected: set[Path]) -> tuple[Path, ...]:
    orphans: list[Path] = []
    for path in sorted(directory.glob("*.md")):
        if path in expected:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if GENERATED_MARKER in text:
            orphans.append(path)
    return tuple(orphans)


def write_structured_projections(directory: Path, *, kind: str) -> tuple[Path, ...]:
    outputs = expected_structured_projections(directory, kind=kind)
    changed: list[Path] = []
    for path, expected in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != expected:
            path.write_text(expected, encoding="utf-8", newline="\n")
            changed.append(path)
    for orphan in _generated_orphans(directory, set(outputs)):
        orphan.unlink()
        changed.append(orphan)
    return tuple(changed)


def check_structured_projections(directory: Path, *, kind: str, stream: Any = sys.stdout) -> bool:
    outputs = expected_structured_projections(directory, kind=kind)
    ok = True
    for path, expected in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current == expected:
            continue
        ok = False
        label = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()
        print(f"DRIFT: {label} does not match its canonical JSON source", file=stream)
        for line in difflib.unified_diff(
            current.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile=label,
            tofile=f"expected:{label}",
        ):
            print(line, end="", file=stream)

    for orphan in _generated_orphans(directory, set(outputs)):
        ok = False
        label = orphan.relative_to(ROOT).as_posix() if orphan.is_relative_to(ROOT) else orphan.as_posix()
        print(f"DRIFT: orphan generated projection has no canonical JSON source: {label}", file=stream)

    if ok:
        print(f"PASS: {len(outputs)} {kind} Markdown projections match canonical JSON", file=stream)
    return ok
