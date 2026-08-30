# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded offline AST profile for the frozen ESRM20 project-278 source.

This module does not fetch provider content. A caller must supply the two exact
Python source objects already frozen by #291. Production entry points verify
their byte count, SHA-256 and Git blob SHA-1 before AST parsing.

The emitted profile contains bounded structural facts only: candidate function
names, line spans, standardized CRS/sentinel markers, relevant call names and
function-local co-occurrence relations. It never returns raw source text and it
does not prove the historical Kosovo generator invocation, output CRS/datum,
missingness semantics, site-model compatibility, publication rights or model use.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

PROFILE_SCHEMA_VERSION = "oc-esrm20-project278-dataflow-profile-v1"
PROJECT_ID = 278
PROJECT_PATH = "efehr/esrm20_sitemodel"
SOURCE_REF = "038c91d2bf5a07f6b54ff51639aad874d6837ea9"

SOURCE_TARGETS = {
    "exposure2site/exposure_to_site_tools.py": {
        "byte_count": 79_824,
        "sha256": "d215f41510c2572ab6bda92bb7061261855a32a2fb6b54a1d74e9c362a3d8730",
        "git_blob_sha1": "e00104344b608ba528a46d84f61269f8000b385a",
    },
    "exposure2site/node_handler.py": {
        "byte_count": 25_394,
        "sha256": "8152525369ba6dabd9cf665d84ee69ba10c5a11fd07d2e5bd41cc009dbf89acb",
        "git_blob_sha1": "14ee7c80d8b69a89fc669a6fc265e3e40c0358a7",
    },
}

MAX_SOURCE_BYTES = 1_048_576
MAX_CANDIDATE_FUNCTIONS = 96
MAX_STATEMENT_RECORDS = 192
MAX_CALL_NAMES = 32
MAX_SITE_FIELDS = 16
MAX_MARKERS = 16
MAX_IDENTIFIER_CHARS = 128

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]{0,127}$")
_SITE_FIELD_ALIASES = {
    "lon": "longitude",
    "longitude": "longitude",
    "lat": "latitude",
    "latitude": "latitude",
    "vs30": "vs30",
    "xvf": "xvf",
    "geology": "geology",
    "region": "region",
    "slope": "slope",
}
_WRITER_TAILS = {
    "write",
    "write_xml",
    "to_xml",
    "to_file",
    "tostring",
    "dump",
    "dumps",
    "save",
    "serialize",
    "export",
}
_CRS_TAILS = {
    "to_crs",
    "reproject",
    "transform",
    "from_crs",
    "from_epsg",
}
_RELATION_ORDER = (
    "coordinates_and_writer_same_function",
    "crs_and_coordinates_same_function",
    "crs_and_writer_same_function",
    "sentinel_and_site_fields_same_function",
    "sentinel_and_writer_same_function",
)


class Project278DataflowProfileError(RuntimeError):
    """Fail-closed error for the bounded fixed-source AST profile."""


def _git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _safe_identifier(value: str) -> str:
    if (
        type(value) is not str
        or len(value) > MAX_IDENTIFIER_CHARS
        or _IDENTIFIER_RE.fullmatch(value) is None
    ):
        raise Project278DataflowProfileError("source identifier is outside profile policy")
    return value


def _call_name(func: ast.expr) -> str | None:
    parts: list[str] = []
    node: ast.expr | None = func
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    else:
        return None
    name = ".".join(reversed(parts))
    return _safe_identifier(name)


def _call_tail(name: str) -> str:
    return name.rsplit(".", 1)[-1].casefold()


def _is_writer_call(name: str) -> bool:
    tail = _call_tail(name)
    return tail in _WRITER_TAILS or tail.startswith("write_") or tail.endswith("_writer")


def _is_crs_call(name: str) -> bool:
    tail = _call_tail(name)
    return tail in _CRS_TAILS or "reproject" in tail or tail.endswith("_crs")


def _string_marker(value: str) -> set[str]:
    lower = value.casefold()
    compact = lower.replace(" ", "").replace("-", "")
    markers: set[str] = set()
    if "epsg:4326" in lower or "epsg=4326" in lower or compact == "epsg4326":
        markers.add("epsg_4326")
    if "epsg:3035" in lower or "epsg=3035" in lower or compact == "epsg3035":
        markers.add("epsg_3035")
    if "wgs84" in compact:
        markers.add("wgs84")
    if "nodata" in compact or "no_data" in lower:
        markers.add("nodata")
    if "unknown" in lower:
        markers.add("unknown")
    if lower.strip() == "nan":
        markers.add("nan")
    return markers


def _numeric_value(node: ast.AST) -> int | float | None:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and type(node.operand.value) in (int, float)
    ):
        return -node.operand.value
    return None


def _markers(node: ast.AST) -> set[str]:
    markers: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Constant):
            if isinstance(child.value, str):
                markers.update(_string_marker(child.value))
            elif child.value is None:
                markers.add("none")
        elif isinstance(child, ast.Name):
            lower = child.id.casefold()
            if lower in {"nan", "isnan"}:
                markers.add("nan")
            elif lower in {"nodata", "no_data"}:
                markers.add("nodata")
            elif lower == "unknown":
                markers.add("unknown")
        elif isinstance(child, ast.Attribute):
            lower = child.attr.casefold()
            if lower in {"nan", "isnan"}:
                markers.add("nan")
            elif lower in {"nodata", "no_data"}:
                markers.add("nodata")
            elif lower == "unknown":
                markers.add("unknown")
        value = _numeric_value(child)
        if value == -999:
            markers.add("negative_999")
        elif value == -9999:
            markers.add("negative_9999")
    if len(markers) > MAX_MARKERS:
        raise Project278DataflowProfileError("marker set exceeds profile policy")
    return markers


def _site_fields(node: ast.AST) -> set[str]:
    fields: set[str] = set()
    for child in ast.walk(node):
        values: list[str] = []
        if isinstance(child, ast.Name):
            values.append(child.id)
        elif isinstance(child, ast.Attribute):
            values.append(child.attr)
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            values.append(child.value)
        elif isinstance(child, ast.keyword) and child.arg is not None:
            values.append(child.arg)
        for value in values:
            normalized = value.casefold().replace("-", "_").strip()
            for alias, canonical in _SITE_FIELD_ALIASES.items():
                if normalized == alias or normalized.endswith("_" + alias):
                    fields.add(canonical)
    if len(fields) > MAX_SITE_FIELDS:
        raise Project278DataflowProfileError("site-field set exceeds profile policy")
    return fields


def _relevant_calls(node: ast.AST) -> tuple[list[str], list[str]]:
    writer: set[str] = set()
    crs: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        name = _call_name(child.func)
        if name is None:
            continue
        if _is_writer_call(name):
            writer.add(name)
        if _is_crs_call(name):
            crs.add(name)
    if len(writer) > MAX_CALL_NAMES or len(crs) > MAX_CALL_NAMES:
        raise Project278DataflowProfileError("relevant call set exceeds profile policy")
    return sorted(writer), sorted(crs)


class _ScopeVisitor(ast.NodeVisitor):
    """Visit one function body without descending into nested function scopes."""

    def __init__(self, root: ast.AST) -> None:
        self.root = root
        self.nodes: list[ast.AST] = []

    def generic_visit(self, node: ast.AST) -> None:
        self.nodes.append(node)
        super().generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        if node is self.root:
            self.nodes.append(node)
            for statement in node.body:
                self.visit(statement)
        else:
            self.nodes.append(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        if node is self.root:
            self.nodes.append(node)
            for statement in node.body:
                self.visit(statement)
        else:
            self.nodes.append(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: N802
        self.nodes.append(node)


def _scope_nodes(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.AST]:
    visitor = _ScopeVisitor(function)
    visitor.visit(function)
    return visitor.nodes


def _scope_summary(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    repository_path: str,
) -> dict[str, Any] | None:
    nodes = _scope_nodes(function)
    call_writer: set[str] = set()
    call_crs: set[str] = set()
    fields: set[str] = set()
    markers: set[str] = set()
    for node in nodes:
        writers, crs = _relevant_calls(node)
        call_writer.update(writers)
        call_crs.update(crs)
        fields.update(_site_fields(node))
        markers.update(_markers(node))

    coordinate_related = bool({"longitude", "latitude"} & fields)
    site_related = bool(fields)
    crs_related = bool(call_crs or {"epsg_4326", "epsg_3035", "wgs84"} & markers)
    sentinel_related = bool(
        {"negative_999", "negative_9999", "nan", "nodata", "unknown", "none"} & markers
    )
    writer_related = bool(call_writer)
    if not (coordinate_related or site_related or crs_related or sentinel_related or writer_related):
        return None

    relations: list[str] = []
    conditions = {
        "coordinates_and_writer_same_function": coordinate_related and writer_related,
        "crs_and_coordinates_same_function": crs_related and coordinate_related,
        "crs_and_writer_same_function": crs_related and writer_related,
        "sentinel_and_site_fields_same_function": sentinel_related and site_related,
        "sentinel_and_writer_same_function": sentinel_related and writer_related,
    }
    for relation in _RELATION_ORDER:
        if conditions[relation]:
            relations.append(relation)

    args = [
        arg.arg
        for arg in (
            list(function.args.posonlyargs)
            + list(function.args.args)
            + list(function.args.kwonlyargs)
        )
    ]
    if function.args.vararg is not None:
        args.append(function.args.vararg.arg)
    if function.args.kwarg is not None:
        args.append(function.args.kwarg.arg)

    return {
        "repository_path": repository_path,
        "function": _safe_identifier(function.name),
        "line_start": function.lineno,
        "line_end": getattr(function, "end_lineno", function.lineno),
        "argument_names": sorted({_safe_identifier(arg) for arg in args}),
        "site_fields": sorted(fields),
        "crs_markers": sorted(
            marker for marker in markers if marker in {"epsg_4326", "epsg_3035", "wgs84"}
        ),
        "sentinel_markers": sorted(
            marker
            for marker in markers
            if marker in {"negative_999", "negative_9999", "nan", "nodata", "unknown", "none"}
        ),
        "crs_calls": sorted(call_crs),
        "writer_calls": sorted(call_writer),
        "relations": relations,
    }


def _statement_kind(node: ast.AST) -> str | None:
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        return "assignment"
    if isinstance(node, ast.Call):
        return "call"
    if isinstance(node, ast.Return):
        return "return"
    if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.Assert, ast.Compare)):
        return "condition"
    return None


def _statement_records(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    repository_path: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for node in _scope_nodes(function):
        kind = _statement_kind(node)
        if kind is None:
            continue
        fields = _site_fields(node)
        markers = _markers(node)
        writer_calls, crs_calls = _relevant_calls(node)
        relevant_markers = markers & {
            "epsg_4326",
            "epsg_3035",
            "wgs84",
            "negative_999",
            "negative_9999",
            "nan",
            "nodata",
            "unknown",
            "none",
        }
        if not (fields or relevant_markers or writer_calls or crs_calls):
            continue
        records.append(
            {
                "repository_path": repository_path,
                "function": _safe_identifier(function.name),
                "kind": kind,
                "line_start": getattr(node, "lineno", function.lineno),
                "line_end": getattr(node, "end_lineno", getattr(node, "lineno", function.lineno)),
                "site_fields": sorted(fields),
                "markers": sorted(relevant_markers),
                "crs_calls": crs_calls,
                "writer_calls": writer_calls,
            }
        )
        if len(records) > MAX_STATEMENT_RECORDS:
            raise Project278DataflowProfileError("statement record set exceeds profile policy")
    return records


def _parse_source(
    repository_path: str,
    data: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
    expected_git_blob_sha1: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if type(data) is not bytes or not data or len(data) > MAX_SOURCE_BYTES:
        raise Project278DataflowProfileError("source bytes are outside profile policy")
    if len(data) != expected_byte_count:
        raise Project278DataflowProfileError("fixed source byte count drifted")
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise Project278DataflowProfileError("fixed source SHA-256 drifted")
    if _git_blob_sha1(data) != expected_git_blob_sha1:
        raise Project278DataflowProfileError("fixed source Git blob identity drifted")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Project278DataflowProfileError("fixed source is not UTF-8") from exc
    if "\x00" in text:
        raise Project278DataflowProfileError("fixed source contains NUL")
    try:
        tree = ast.parse(text, filename=repository_path)
    except SyntaxError as exc:
        raise Project278DataflowProfileError("fixed source does not parse as Python") from exc

    functions: list[dict[str, Any]] = []
    statements: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        summary = _scope_summary(node, repository_path=repository_path)
        if summary is not None:
            functions.append(summary)
        statements.extend(_statement_records(node, repository_path=repository_path))
        if len(functions) > MAX_CANDIDATE_FUNCTIONS:
            raise Project278DataflowProfileError("candidate function set exceeds profile policy")
        if len(statements) > MAX_STATEMENT_RECORDS:
            raise Project278DataflowProfileError("statement record set exceeds profile policy")

    functions.sort(key=lambda item: (item["repository_path"], item["line_start"], item["function"]))
    statements.sort(
        key=lambda item: (
            item["repository_path"],
            item["line_start"],
            item["line_end"],
            item["function"],
            item["kind"],
        )
    )
    return functions, statements


def _profile_sources_for_test(
    sources: dict[str, bytes],
    *,
    identities: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if set(sources) != set(identities):
        raise Project278DataflowProfileError("source set does not match identity set")
    functions: list[dict[str, Any]] = []
    statements: list[dict[str, Any]] = []
    source_identities: list[dict[str, Any]] = []
    for repository_path in sorted(sources):
        identity = identities[repository_path]
        data = sources[repository_path]
        file_functions, file_statements = _parse_source(
            repository_path,
            data,
            expected_byte_count=identity["byte_count"],
            expected_sha256=identity["sha256"],
            expected_git_blob_sha1=identity["git_blob_sha1"],
        )
        functions.extend(file_functions)
        statements.extend(file_statements)
        source_identities.append(
            {
                "repository_path": repository_path,
                "byte_count": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "git_blob_sha1": _git_blob_sha1(data),
            }
        )

    if len(functions) > MAX_CANDIDATE_FUNCTIONS:
        raise Project278DataflowProfileError("combined candidate function set exceeds profile policy")
    if len(statements) > MAX_STATEMENT_RECORDS:
        raise Project278DataflowProfileError("combined statement record set exceeds profile policy")

    functions.sort(key=lambda item: (item["repository_path"], item["line_start"], item["function"]))
    statements.sort(
        key=lambda item: (
            item["repository_path"],
            item["line_start"],
            item["line_end"],
            item["function"],
            item["kind"],
        )
    )

    writer_candidates = sorted(
        {
            f'{item["repository_path"]}:{item["function"]}'
            for item in functions
            if item["writer_calls"]
        }
    )
    crs_writer_candidates = sorted(
        {
            f'{item["repository_path"]}:{item["function"]}'
            for item in functions
            if "crs_and_writer_same_function" in item["relations"]
        }
    )
    sentinel_writer_candidates = sorted(
        {
            f'{item["repository_path"]}:{item["function"]}'
            for item in functions
            if "sentinel_and_writer_same_function" in item["relations"]
        }
    )

    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "source_ref": SOURCE_REF,
        "source_identities": source_identities,
        "analysis_basis": "bounded_python_ast_function_local_structure",
        "candidate_functions": functions,
        "statement_records": statements,
        "candidate_function_count": len(functions),
        "statement_record_count": len(statements),
        "writer_candidate_functions": writer_candidates,
        "crs_writer_candidate_functions": crs_writer_candidates,
        "sentinel_writer_candidate_functions": sentinel_writer_candidates,
        "raw_source_returned": False,
        "historical_kosovo_generator_invocation_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "site_model_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_verified_project278_sources(sources: dict[str, bytes]) -> dict[str, Any]:
    """Profile only the two frozen project-278 Python source objects."""
    if set(SOURCE_TARGETS) != {
        "exposure2site/exposure_to_site_tools.py",
        "exposure2site/node_handler.py",
    }:
        raise Project278DataflowProfileError("frozen project-278 source authority drifted")
    return _profile_sources_for_test(sources, identities=SOURCE_TARGETS)


def _read_fixed_sources(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        raise Project278DataflowProfileError("source root is not a directory")
    result: dict[str, bytes] = {}
    for repository_path in SOURCE_TARGETS:
        path = root / repository_path
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise Project278DataflowProfileError("fixed source file is unavailable") from exc
        result[repository_path] = data
    return result


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Profile bounded AST relations in the frozen project-278 Python sources."
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)

    profile = profile_verified_project278_sources(_read_fixed_sources(args.source_root))
    payload = json.dumps(profile, sort_keys=True, separators=(",", ":")) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
