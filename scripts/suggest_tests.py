# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Suggest focused offline unit tests for changed Python files without executing test code.

Agent entry point (from a Git checkout):

    python scripts/suggest_tests.py scripts/validate_manifest.py
    python scripts/suggest_tests.py --base main --json

Suggestions are static hints, NOT an impact-coverage proof. Run task-specific
checks and the full python scripts/check_all.py before completion.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
INPUT_AREAS = ("scripts", "research_runners")


def safe_path(raw: str) -> PurePosixPath:
    """Never resolve arbitrary paths or follow user-supplied paths outside the repo."""
    if not raw or "\\" in raw or "\x00" in raw:
        raise ValueError("paths must be non-empty repository-relative POSIX paths")
    path = PurePosixPath(raw)
    if not path.parts or path.is_absolute() or ".." in path.parts or raw.startswith("./"):
        raise ValueError("paths must be repository-relative and cannot traverse parents")
    return path


def _nul_fields(data: bytes) -> list[str]:
    """Parse complete Git -z output; never silently accept truncated records."""
    if not data:
        return []
    if not data.endswith(b"\x00"):
        raise ValueError("unterminated Git -z output")
    return data[:-1].decode("utf-8", errors="strict").split("\x00")


def _diff_name_status_paths(data: bytes) -> set[str]:
    """Keep both original and destination paths for Git renames/copies."""
    fields = _nul_fields(data)
    paths: set[str] = set()
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if not re.fullmatch(r"(?:[RC][0-9]{1,3}|[AMDTUXB])", status):
            raise ValueError(f"unknown Git diff status: {status!r}")
        count = 2 if status[0] in "RC" else 1
        if len(fields) - index < count:
            raise ValueError("incomplete Git diff name-status record")
        paths.update(safe_path(name).as_posix() for name in fields[index:index + count])
        index += count
    return paths


def git_changed_paths(root: Path, base: str) -> list[str]:
    """Include both sides of renames plus staged, unstaged and untracked paths."""
    if not base or base.startswith("-"):
        raise ValueError("--base must name a non-option Git ref")
    commands = (
        ["git", "diff", "--name-status", "--find-renames", "-z", f"{base}...HEAD", "--"],
        ["git", "diff", "--name-status", "--find-renames", "-z", "HEAD", "--"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
    )
    names: set[str] = set()
    for index, cmd in enumerate(commands):
        outcome = subprocess.run(cmd, cwd=root, capture_output=True, check=False)
        if outcome.returncode:
            raise ValueError(
                f"unable to read Git changes ({cmd[1]}): "
                "check that --base exists locally and the checkout is complete"
            )
        if index < 2:
            names.update(_diff_name_status_paths(outcome.stdout))
        else:
            names.update(safe_path(name).as_posix() for name in _nul_fields(outcome.stdout))
    return sorted(names)


def imported_module(tree: ast.AST, dotted: str) -> bool:
    """Exact import binding only; generic package imports do not imply coverage."""
    package, _, leaf = dotted.rpartition(".")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == dotted for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == dotted:
                return True
            if node.module == package and any(alias.name == leaf for alias in node.names):
                return True
    return False


def literal_path_reference(tree: ast.AST, source: PurePosixPath) -> bool:
    """Recognise explicit ROOT / "scripts/file.py" and split-root joins, not text."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
            continue
        # Only the path-building expression matters. A fixture asserting that
        # a filename string exists is not evidence of test impact.
        if not isinstance(node.right, ast.Constant) or not isinstance(node.right.value, str):
            continue
        # Real tests also use ROOT / "scripts/validate_manifest.py" when
        # invoking a script by path rather than importing its module.
        # Require an explicit repository-root join to avoid matching strings.
        if (node.right.value == source.as_posix()
                and isinstance(node.left, ast.Name) and node.left.id == "ROOT"):
            return True
        if node.right.value != source.name:
            continue
        parent = node.left
        if (isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Div)
                and isinstance(parent.right, ast.Constant)
                and parent.right.value == source.parts[0]):
            return True
    return False


def suggests_test(source: PurePosixPath, test: PurePosixPath, tree: ast.AST) -> bool:
    """Conservative name/import/literal matches; no claim of completeness."""
    if source.parts[0] not in INPUT_AREAS or source.suffix != ".py":
        return False
    stem = source.stem
    if test.stem == f"test_{stem}" or test.stem.startswith(f"test_{stem}_"):
        return True
    dotted = ".".join(source.with_suffix("").parts)
    return imported_module(tree, dotted) or literal_path_reference(tree, source)


def suggest(paths: list[str], *, root: Path = ROOT) -> dict[str, object]:
    """Parse tests only; a matching test is not proof the changed behavior is covered."""
    changed = sorted({safe_path(path).as_posix() for path in paths})
    tests_root = root / "tests"
    if not tests_root.is_dir():
        raise ValueError("tests/ does not exist")

    test_trees: dict[str, ast.AST] = {}
    for file in sorted(tests_root.glob("test*.py")):
        if file.is_symlink() or not file.is_file():
            raise ValueError(f"unsafe test file: {file.name}")
        try:
            test_trees[f"tests/{file.name}"] = ast.parse(
                file.read_text(encoding="utf-8"), filename=file.name
            )
        except (SyntaxError, UnicodeError) as exc:
            raise ValueError(f"unparseable test file: {file.name}") from exc

    found: set[str] = set()
    unmatched: list[str] = []
    matches: dict[str, list[str]] = {}
    for name in changed:
        path = PurePosixPath(name)
        if len(path.parts) == 2 and path.parts[0] == "tests" and name in test_trees:
            hits = [name]
        elif len(path.parts) == 2 and path.parts[0] in INPUT_AREAS:
            hits = [test for test, tree in test_trees.items()
                    if suggests_test(path, PurePosixPath(test), tree)]
        else:
            hits = []
        if hits:
            found.update(hits)
            matches[name] = hits
        else:
            unmatched.append(name)

    modules = [name.removesuffix(".py").replace("/", ".") for name in sorted(found)]
    return {
        "changed_paths": changed,
        "suggested_tests": sorted(found),
        "matched_paths": matches,
        "unmatched_paths": unmatched,
        "command": ["python", "-m", "unittest", *modules] if modules else [],
        "verification": "ADVISORY ONLY: not a proof of test coverage or source/model admission; run full check_all.py",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="repository-relative changed paths")
    parser.add_argument("--base", help="Git base ref; include committed, staged, unstaged, and untracked changes")
    parser.add_argument("--json", action="store_true", help="print machine-readable suggestions")
    options = parser.parse_args(argv)
    if bool(options.paths) == bool(options.base):
        parser.error("supply either changed paths or --base, not both")
    try:
        changed = git_changed_paths(ROOT, options.base) if options.base else options.paths
        report = suggest(changed, root=ROOT)
    except (OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    if options.json:
        print(json.dumps(report, sort_keys=True, indent=2))
    else:
        print(f"Changed paths: {len(report['changed_paths'])}; suggested test files: "
              f"{len(report['suggested_tests'])}")
        if report["command"]:
            print("SUGGESTED: " + shlex.join(report["command"]))
        else:
            print("NO STATIC TEST MATCH: identify affected tests manually")
        if report["unmatched_paths"]:
            print("Unmatched changes: " + ", ".join(report["unmatched_paths"]))
        print(report["verification"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
