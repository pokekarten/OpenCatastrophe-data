# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline AST evidence for the frozen ESRM20 project-278 writer paths.

No provider access occurs here. The production entry point accepts only the two
Python objects already byte-grounded by #291 and re-verifies byte count,
SHA-256, and Git blob SHA-1 before parsing. Output is bounded structural
evidence, never source text and never historical/CRS/missingness authority.

Important semantic boundary: the ESRM20 methodology uses ``Unknown`` as a
modelled geology category. This profiler therefore reports it as a *category*
marker and never conflates it with missing/null/sentinel candidates.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Iterator

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
MAX_FUNCTIONS = 96
MAX_STATEMENTS = 256
MAX_CALLS = 32
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]{0,127}$")
_SCOPE_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
_SITE_ALIASES = {
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
# Deliberately exclude generic ``transform``: without receiver/type evidence it
# is too broad to classify as a CRS operation. Exact CRS APIs/markers remain.
_CRS_TAILS = {"to_crs", "reproject", "from_crs", "from_epsg"}
_CRS_MARKERS = {"epsg_3035", "epsg_4326", "wgs84"}
_MISSING_MARKERS = {"negative_999", "negative_9999", "nan", "nodata", "none"}
_CATEGORY_MARKERS = {"unknown"}


class Project278DataflowProfileError(RuntimeError):
    """Fail-closed fixed-source profile error."""


def _git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _safe_name(value: str) -> str:
    if type(value) is not str or _IDENTIFIER_RE.fullmatch(value) is None:
        raise Project278DataflowProfileError("identifier outside profile policy")
    return value


def _bounded_walk(root: ast.AST) -> Iterator[ast.AST]:
    """Walk one lexical scope and prune nested functions/classes/lambdas."""
    stack = [root]
    while stack:
        node = stack.pop()
        if node is not root and isinstance(node, _SCOPE_TYPES):
            continue
        yield node
        stack.extend(reversed(list(ast.iter_child_nodes(node))))


def _call_name(func: ast.expr) -> str | None:
    parts: list[str] = []
    node: ast.expr | None = func
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return _safe_name(".".join(reversed(parts)))


def _call_sets(nodes: Iterable[ast.AST]) -> tuple[set[str], set[str]]:
    writers: set[str] = set()
    crs: set[str] = set()
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        if name is None:
            continue
        tail = name.rsplit(".", 1)[-1].casefold()
        if tail in _WRITER_TAILS or tail.startswith("write_") or tail.endswith("_writer"):
            writers.add(name)
        if tail in _CRS_TAILS or "reproject" in tail or tail.endswith("_crs"):
            crs.add(name)
    if len(writers) > MAX_CALLS or len(crs) > MAX_CALLS:
        raise Project278DataflowProfileError("call set exceeds profile policy")
    return writers, crs


def _is_none_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _is_explicit_none_comparison(node: ast.AST) -> bool:
    """Recognize bounded explicit null checks, not generic Python ``None`` use."""
    if not isinstance(node, ast.Compare):
        return False
    operands = (node.left, *node.comparators)
    if not any(_is_none_literal(operand) for operand in operands):
        return False
    return any(
        isinstance(operator, (ast.Is, ast.IsNot, ast.Eq, ast.NotEq))
        for operator in node.ops
    )


def _markers(nodes: Iterable[ast.AST]) -> set[str]:
    result: set[str] = set()
    for node in nodes:
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, str):
                lower = value.casefold()
                compact = lower.replace(" ", "").replace("-", "")
                if "epsg:4326" in lower or "epsg=4326" in lower or compact == "epsg4326":
                    result.add("epsg_4326")
                if "epsg:3035" in lower or "epsg=3035" in lower or compact == "epsg3035":
                    result.add("epsg_3035")
                if "wgs84" in compact:
                    result.add("wgs84")
                if "nodata" in compact or "no_data" in lower:
                    result.add("nodata")
                if "unknown" in lower:
                    result.add("unknown")
                if lower.strip() == "nan":
                    result.add("nan")
        elif _is_explicit_none_comparison(node):
            result.add("none")
        elif isinstance(node, (ast.Name, ast.Attribute)):
            token = (node.id if isinstance(node, ast.Name) else node.attr).casefold()
            if token in {"nan", "isnan"}:
                result.add("nan")
            elif token in {"nodata", "no_data"}:
                result.add("nodata")
            elif token == "unknown":
                result.add("unknown")
        if (
            isinstance(node, ast.UnaryOp)
            and isinstance(node.op, ast.USub)
            and isinstance(node.operand, ast.Constant)
            and type(node.operand.value) in (int, float)
        ):
            if node.operand.value == 999:
                result.add("negative_999")
            elif node.operand.value == 9999:
                result.add("negative_9999")
    return result


def _site_fields(nodes: Iterable[ast.AST]) -> set[str]:
    result: set[str] = set()
    for node in nodes:
        values: list[str] = []
        if isinstance(node, ast.Name):
            values.append(node.id)
        elif isinstance(node, ast.Attribute):
            values.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append(node.value)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            values.append(node.arg)
        for value in values:
            normalized = value.casefold().replace("-", "_").strip()
            for alias, canonical in _SITE_ALIASES.items():
                if normalized == alias or normalized.endswith("_" + alias):
                    result.add(canonical)
    return result


def _scope_profile(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    repository_path: str,
) -> dict[str, Any] | None:
    nodes = list(_bounded_walk(function))
    writers, crs_calls = _call_sets(nodes)
    markers = _markers(nodes)
    fields = _site_fields(nodes)
    coordinate_related = bool({"longitude", "latitude"} & fields)
    crs_related = bool(crs_calls or markers & _CRS_MARKERS)
    missing_related = bool(markers & _MISSING_MARKERS)
    category_related = bool(markers & _CATEGORY_MARKERS)
    if not (writers or crs_related or missing_related or category_related or fields):
        return None

    relations = []
    for name, matched in (
        ("coordinates_and_writer_same_function", coordinate_related and bool(writers)),
        ("crs_and_coordinates_same_function", crs_related and coordinate_related),
        ("crs_and_writer_same_function", crs_related and bool(writers)),
        ("missing_and_site_fields_same_function", missing_related and bool(fields)),
        ("missing_and_writer_same_function", missing_related and bool(writers)),
        ("category_and_site_fields_same_function", category_related and bool(fields)),
    ):
        if matched:
            relations.append(name)

    return {
        "repository_path": repository_path,
        "function": _safe_name(function.name),
        "line_start": function.lineno,
        "line_end": getattr(function, "end_lineno", function.lineno),
        "site_fields": sorted(fields),
        "crs_markers": sorted(markers & _CRS_MARKERS),
        "missing_candidate_markers": sorted(markers & _MISSING_MARKERS),
        "category_markers": sorted(markers & _CATEGORY_MARKERS),
        "crs_calls": sorted(crs_calls),
        "writer_calls": sorted(writers),
        "relations": relations,
    }


def _statement_profile(
    statement: ast.stmt,
    *,
    function: str,
    repository_path: str,
) -> dict[str, Any] | None:
    nodes = list(_bounded_walk(statement))
    writers, crs_calls = _call_sets(nodes)
    markers = _markers(nodes)
    fields = _site_fields(nodes)
    crs_markers = markers & _CRS_MARKERS
    missing_markers = markers & _MISSING_MARKERS
    category_markers = markers & _CATEGORY_MARKERS
    if not (writers or crs_calls or crs_markers or missing_markers or category_markers or fields):
        return None
    return {
        "repository_path": repository_path,
        "function": _safe_name(function),
        "statement_type": type(statement).__name__,
        "line_start": statement.lineno,
        "line_end": getattr(statement, "end_lineno", statement.lineno),
        "site_fields": sorted(fields),
        "crs_markers": sorted(crs_markers),
        "missing_candidate_markers": sorted(missing_markers),
        "category_markers": sorted(category_markers),
        "crs_calls": sorted(crs_calls),
        "writer_calls": sorted(writers),
    }


def _parse_verified(
    repository_path: str,
    data: bytes,
    identity: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if type(data) is not bytes or not data or len(data) > MAX_SOURCE_BYTES:
        raise Project278DataflowProfileError("source bytes outside profile policy")
    if len(data) != identity["byte_count"]:
        raise Project278DataflowProfileError("fixed source byte count drifted")
    if hashlib.sha256(data).hexdigest() != identity["sha256"]:
        raise Project278DataflowProfileError("fixed source SHA-256 drifted")
    if _git_blob_sha1(data) != identity["git_blob_sha1"]:
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
        raise Project278DataflowProfileError("fixed source does not parse") from exc

    functions: list[dict[str, Any]] = []
    statements: list[dict[str, Any]] = []
    for function in (
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ):
        profile = _scope_profile(function, repository_path)
        if profile is not None:
            functions.append(profile)
        for node in _bounded_walk(function):
            if not isinstance(node, ast.stmt) or node is function:
                continue
            record = _statement_profile(
                node, function=function.name, repository_path=repository_path
            )
            if record is not None:
                statements.append(record)
        if len(functions) > MAX_FUNCTIONS or len(statements) > MAX_STATEMENTS:
            raise Project278DataflowProfileError("AST profile exceeds result policy")

    functions.sort(
        key=lambda item: (item["repository_path"], item["line_start"], item["function"])
    )
    statements.sort(
        key=lambda item: (
            item["repository_path"],
            item["line_start"],
            item["line_end"],
            item["function"],
            item["statement_type"],
        )
    )
    return functions, statements


def _profile_sources(
    sources: dict[str, bytes],
    identities: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if set(sources) != set(identities):
        raise Project278DataflowProfileError("source set does not match identity set")
    functions: list[dict[str, Any]] = []
    statements: list[dict[str, Any]] = []
    source_identities = []
    for path in sorted(sources):
        file_functions, file_statements = _parse_verified(path, sources[path], identities[path])
        functions.extend(file_functions)
        statements.extend(file_statements)
        source_identities.append(
            {
                "repository_path": path,
                "byte_count": len(sources[path]),
                "sha256": hashlib.sha256(sources[path]).hexdigest(),
                "git_blob_sha1": _git_blob_sha1(sources[path]),
            }
        )
    if len(functions) > MAX_FUNCTIONS or len(statements) > MAX_STATEMENTS:
        raise Project278DataflowProfileError("combined AST profile exceeds result policy")

    def selected(relation: str) -> list[str]:
        return sorted(
            f'{item["repository_path"]}:{item["function"]}'
            for item in functions
            if relation in item["relations"]
        )

    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "source_ref": SOURCE_REF,
        "analysis_basis": "bounded_python_ast_function_local_structure",
        "source_identities": source_identities,
        "candidate_functions": functions,
        "statement_records": statements,
        "candidate_function_count": len(functions),
        "statement_record_count": len(statements),
        "crs_writer_candidate_functions": selected("crs_and_writer_same_function"),
        "missing_writer_candidate_functions": selected("missing_and_writer_same_function"),
        "category_site_candidate_functions": selected("category_and_site_fields_same_function"),
        "unknown_is_missing_marker": False,
        "raw_source_returned": False,
        "historical_kosovo_generator_invocation_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "site_model_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _profile_sources_for_test(
    sources: dict[str, bytes],
    *,
    identities: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return _profile_sources(sources, identities)


def profile_verified_project278_sources(sources: dict[str, bytes]) -> dict[str, Any]:
    """Profile only the two frozen project-278 Python objects."""
    return _profile_sources(sources, SOURCE_TARGETS)


def _read_fixed_sources(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        raise Project278DataflowProfileError("source root is not a directory")
    try:
        return {path: (root / path).read_bytes() for path in SOURCE_TARGETS}
    except OSError as exc:
        raise Project278DataflowProfileError("fixed source file unavailable") from exc


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Profile AST writer/CRS/missing/category relations in frozen project-278 source."
    )
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    payload = json.dumps(
        profile_verified_project278_sources(_read_fixed_sources(args.source_root)),
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
