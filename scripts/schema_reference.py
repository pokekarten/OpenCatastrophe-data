# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Render and verify one deterministic human-readable reference for public JSON Schemas."""

from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__:
    from .structured_public_views import ProjectionError, load_structured_json
else:
    from structured_public_views import ProjectionError, load_structured_json

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
OUTPUT_PATH = ROOT / "docs" / "SCHEMA_REFERENCE.md"
GENERATED_MARKER = "GENERATED FILE — DO NOT EDIT DIRECTLY"
GENERATED_SPDX_LICENSE_LINE = "SPDX-" + "License-Identifier: Apache-2.0"
MARKDOWN_ESCAPE_RE = re.compile(r"([\\`*\[\]{}#!|])")

_METADATA_KEYS = {
    "$schema",
    "$id",
    "$anchor",
    "$comment",
    "title",
    "description",
    "examples",
    "default",
}
_STRUCTURAL_KEYS = {
    "type",
    "required",
    "properties",
    "patternProperties",
    "additionalProperties",
    "$defs",
    "definitions",
    "items",
    "prefixItems",
    "allOf",
    "anyOf",
    "oneOf",
    "if",
    "then",
    "else",
    "not",
}
_CONSTRAINT_KEYS = (
    "$ref",
    "const",
    "enum",
    "format",
    "pattern",
    "minimum",
    "exclusiveMinimum",
    "maximum",
    "exclusiveMaximum",
    "multipleOf",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "uniqueItems",
    "minProperties",
    "maxProperties",
)


def _markdown_text(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    escaped = MARKDOWN_ESCAPE_RE.sub(r"\\\1", html.escape(normalized, quote=False))
    return escaped.replace("\n", "<br>")


def _code(value: str) -> str:
    return f"`{html.escape(value, quote=False).replace('`', '&#96;')}`"


def _compact(value: Any) -> str:
    if isinstance(value, str):
        return _code(value)
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _code(encoded)


def _heading(level: int, text: str) -> str:
    return f"{'#' * min(level, 6)} {text}"


def _type_text(node: dict[str, Any]) -> str | None:
    raw = node.get("type")
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list) and raw and all(isinstance(item, str) for item in raw):
        return " | ".join(raw)
    if "properties" in node or "$defs" in node or "definitions" in node:
        return "object (implicit)"
    return None


def _constraint_fragments(node: dict[str, Any]) -> list[str]:
    fragments: list[str] = []
    type_text = _type_text(node)
    if type_text is not None:
        fragments.append(f"type={_code(type_text)}")
    for key in _CONSTRAINT_KEYS:
        if key in node:
            fragments.append(f"{_code(key)}={_compact(node[key])}")
    if "additionalProperties" in node:
        value = node["additionalProperties"]
        if isinstance(value, bool):
            fragments.append(f"{_code('additionalProperties')}={_code(str(value).lower())}")
        elif isinstance(value, dict):
            fragments.append(f"{_code('additionalProperties')}=schema")
    return fragments


def _required_names(node: dict[str, Any]) -> tuple[str, ...]:
    raw = node.get("required")
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(item, str) and item for item in raw):
        raise ProjectionError("schema required must be an array of non-empty strings")
    return tuple(raw)


def _render_unhandled_keywords(lines: list[str], node: dict[str, Any]) -> None:
    handled = _METADATA_KEYS | _STRUCTURAL_KEYS | set(_CONSTRAINT_KEYS)
    leftovers = [key for key in sorted(node) if key not in handled]
    if not leftovers:
        return
    lines.extend(["**Other schema keywords:**", ""])
    for key in leftovers:
        lines.append(f"- {_code(key)}: {_compact(node[key])}")
    lines.append("")


def _render_node_details(lines: list[str], node: Any, *, level: int) -> None:
    if isinstance(node, bool):
        lines.extend([f"**Boolean schema:** {_code(str(node).lower())}", ""])
        return
    if not isinstance(node, dict):
        raise ProjectionError(f"schema node must be an object or boolean, got {type(node).__name__}")

    description = node.get("description")
    if description is not None:
        if not isinstance(description, str):
            raise ProjectionError("schema description must be a string when present")
        lines.extend([_markdown_text(description), ""])

    fragments = _constraint_fragments(node)
    if fragments:
        lines.extend(["**Constraints:** " + "; ".join(fragments), ""])

    required = _required_names(node)
    if required:
        lines.extend(["**Required here:** " + ", ".join(_code(name) for name in required), ""])

    properties = node.get("properties")
    if properties is not None:
        if not isinstance(properties, dict):
            raise ProjectionError("schema properties must be an object")
        lines.extend([_heading(level, "Properties"), ""])
        required_set = set(required)
        for name in sorted(properties):
            child = properties[name]
            suffix = " — **required**" if name in required_set else ""
            lines.extend([_heading(level + 1, f"{_code(name)}{suffix}"), ""])
            _render_node_details(lines, child, level=level + 2)

    pattern_properties = node.get("patternProperties")
    if pattern_properties is not None:
        if not isinstance(pattern_properties, dict):
            raise ProjectionError("schema patternProperties must be an object")
        lines.extend([_heading(level, "Pattern properties"), ""])
        for pattern in sorted(pattern_properties):
            lines.extend([_heading(level + 1, _code(pattern)), ""])
            _render_node_details(lines, pattern_properties[pattern], level=level + 2)

    for defs_key, label in (("$defs", "$defs"), ("definitions", "Definitions")):
        defs = node.get(defs_key)
        if defs is None:
            continue
        if not isinstance(defs, dict):
            raise ProjectionError(f"schema {defs_key} must be an object")
        lines.extend([_heading(level, label), ""])
        for name in sorted(defs):
            lines.extend([_heading(level + 1, _code(name)), ""])
            _render_node_details(lines, defs[name], level=level + 2)

    if "items" in node:
        lines.extend([_heading(level, "Array items"), ""])
        _render_node_details(lines, node["items"], level=level + 1)

    prefix_items = node.get("prefixItems")
    if prefix_items is not None:
        if not isinstance(prefix_items, list):
            raise ProjectionError("schema prefixItems must be an array")
        lines.extend([_heading(level, "Prefix items"), ""])
        for index, child in enumerate(prefix_items, start=1):
            lines.extend([_heading(level + 1, f"Item {index}"), ""])
            _render_node_details(lines, child, level=level + 2)

    for keyword in ("allOf", "anyOf", "oneOf"):
        value = node.get(keyword)
        if value is None:
            continue
        if not isinstance(value, list):
            raise ProjectionError(f"schema {keyword} must be an array")
        lines.extend([_heading(level, keyword), ""])
        for index, child in enumerate(value, start=1):
            lines.extend([_heading(level + 1, f"Branch {index}"), ""])
            _render_node_details(lines, child, level=level + 2)

    for keyword in ("if", "then", "else", "not"):
        if keyword not in node:
            continue
        lines.extend([_heading(level, keyword), ""])
        _render_node_details(lines, node[keyword], level=level + 1)

    _render_unhandled_keywords(lines, node)


def _schema_paths(schema_dir: Path) -> tuple[Path, ...]:
    paths = tuple(sorted(schema_dir.glob("*.schema.json"), key=lambda path: path.name))
    if not paths:
        raise ProjectionError(f"{schema_dir}: no *.schema.json files found")
    return paths


def render_schema_reference(schema_dir: Path = SCHEMA_DIR) -> str:
    paths = _schema_paths(schema_dir)
    loaded: list[tuple[Path, dict[str, Any]]] = [(path, load_structured_json(path)) for path in paths]

    lines = [
        "<!--",
        "SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors",
        GENERATED_SPDX_LICENSE_LINE,
        "",
        GENERATED_MARKER,
        "Canonical source set: schemas/*.schema.json",
        "Renderer: scripts/schema_reference.py",
        "Change canonical schemas and run `python scripts/schema_reference.py --write`.",
        "-->",
        "",
        "# OpenCatastrophe JSON Schema Reference",
        "",
        "> This file is a deterministic navigation and human-readable reference for the canonical JSON Schemas in `schemas/`. "
        "The JSON Schema files and repository executable validators remain authoritative; this document does not change validation, security, rights, admission or scientific semantics.",
        "",
        f"**Schemas represented:** {len(loaded)}",
        "",
        "## Schema index",
        "",
    ]

    for path, payload in loaded:
        title = payload.get("title")
        title_text = title if isinstance(title, str) and title else path.name
        lines.append(f"- [`schemas/{path.name}`](../schemas/{path.name}) — {_markdown_text(title_text)}")
    lines.append("")

    for path, payload in loaded:
        title = payload.get("title")
        title_text = title if isinstance(title, str) and title else path.name
        lines.extend(
            [
                f"## {_code(path.name)}",
                "",
                f"**Canonical schema:** [`schemas/{path.name}`](../schemas/{path.name})  ",
                f"**Title:** {_markdown_text(title_text)}  ",
            ]
        )

        schema_uri = payload.get("$schema")
        if schema_uri is not None:
            if not isinstance(schema_uri, str):
                raise ProjectionError(f"{path}: $schema must be a string when present")
            lines.append(f"**JSON Schema dialect:** <{html.escape(schema_uri, quote=False)}>  ")
        schema_id = payload.get("$id")
        if schema_id is not None:
            if not isinstance(schema_id, str):
                raise ProjectionError(f"{path}: $id must be a string when present")
            lines.append(f"**$id:** {_code(schema_id)}  ")
        description = payload.get("description")
        if description is not None:
            if not isinstance(description, str):
                raise ProjectionError(f"{path}: description must be a string when present")
            lines.extend(["", _markdown_text(description), ""])
        else:
            lines.append("")

        comment = payload.get("$comment")
        if comment is not None:
            if not isinstance(comment, str):
                raise ProjectionError(f"{path}: $comment must be a string when present")
            lines.extend(["**Executable authority note:** " + _markdown_text(comment), ""])
        else:
            lines.extend(
                [
                    "**Authority note:** The canonical schema governs portable structure; repository Python validators may impose additional fail-closed semantic or security checks where documented.",
                    "",
                ]
            )

        lines.extend(["### Contract structure", ""])
        _render_node_details(lines, payload, level=4)

    return "\n".join(lines).rstrip() + "\n"


def write_schema_reference(
    schema_dir: Path = SCHEMA_DIR,
    output_path: Path = OUTPUT_PATH,
) -> tuple[Path, ...]:
    expected = render_schema_reference(schema_dir)
    current = output_path.read_text(encoding="utf-8") if output_path.exists() else None
    if current == expected:
        return ()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(expected, encoding="utf-8", newline="\n")
    return (output_path,)


def check_schema_reference(
    schema_dir: Path = SCHEMA_DIR,
    output_path: Path = OUTPUT_PATH,
    *,
    stream: Any = sys.stdout,
) -> bool:
    expected = render_schema_reference(schema_dir)
    current = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    if current == expected:
        label = output_path.relative_to(ROOT).as_posix() if output_path.is_relative_to(ROOT) else output_path.as_posix()
        print(f"PASS: {label} represents {len(_schema_paths(schema_dir))} canonical schemas", file=stream)
        return True

    label = output_path.relative_to(ROOT).as_posix() if output_path.is_relative_to(ROOT) else output_path.as_posix()
    print(f"DRIFT: {label} does not match canonical schemas/*.schema.json", file=stream)
    for line in difflib.unified_diff(
        current.splitlines(keepends=True),
        expected.splitlines(keepends=True),
        fromfile=label,
        tofile=f"expected:{label}",
    ):
        print(line, end="", file=stream)
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Regenerate docs/SCHEMA_REFERENCE.md")
    mode.add_argument("--check", action="store_true", help="Fail if docs/SCHEMA_REFERENCE.md is stale or missing")
    args = parser.parse_args(argv)

    try:
        if args.write:
            changed = write_schema_reference()
            if changed:
                for path in changed:
                    print(path.relative_to(ROOT).as_posix())
            else:
                print("PASS: schema reference already current")
            return 0
        return 0 if check_schema_reference() else 1
    except ProjectionError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
