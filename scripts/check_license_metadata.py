# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Check lightweight file-level licensing invariants without external packages.

The official REUSE linter remains the release/tag packaging authority. This check
is intentionally lightweight so ordinary local/agent work fails early.
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LICENSE_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+-]*")
SPDX_OPERATORS = {"AND", "OR", "WITH"}
ROOT_LICENSE_NAMES = {"LICENSE", "LICENCE", "COPYING"}
SPDX_COPYRIGHT_MARKER = "SPDX-" + "FileCopyrightText:"
SPDX_LICENSE_MARKER = "SPDX-" + "License-Identifier:"


def tracked_paths() -> list[Path]:
    process = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [Path(item.decode("utf-8")) for item in process.stdout.split(b"\0") if item]


def reuse_annotations() -> list[dict[str, object]]:
    path = ROOT / "REUSE.toml"
    if not path.exists():
        return []
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("annotations", [])
    if not isinstance(entries, list):
        raise ValueError("REUSE.toml annotations must be an array")
    return [entry for entry in entries if isinstance(entry, dict)]


def covered_by_reuse(relative: Path, annotations: list[dict[str, object]]) -> bool:
    posix = relative.as_posix()
    for entry in annotations:
        patterns = entry.get("path")
        if isinstance(patterns, str):
            patterns = [patterns]
        if not isinstance(patterns, list):
            continue
        if not all(isinstance(pattern, str) for pattern in patterns):
            continue
        if any(fnmatch.fnmatch(posix, pattern) for pattern in patterns):
            copyright_text = entry.get("SPDX-FileCopyrightText")
            licence = entry.get("SPDX-License-Identifier")
            if copyright_text and licence:
                return True
    return False


def is_reuse_exempt(relative: Path) -> bool:
    if len(relative.parts) == 1:
        stem = relative.name.split(".", 1)[0].upper()
        if stem in ROOT_LICENSE_NAMES:
            return True
    return bool(relative.parts and relative.parts[0] == "LICENSES")


def read_spdx_lines(path: Path) -> tuple[bool, bool, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeError:
        return False, False, []
    head = "\n".join(text.splitlines()[:40])
    has_copyright = SPDX_COPYRIGHT_MARKER in head
    has_licence = SPDX_LICENSE_MARKER in head
    expressions = [
        line.split(SPDX_LICENSE_MARKER, 1)[1].strip().strip("-!>#;/* ")
        for line in head.splitlines()
        if SPDX_LICENSE_MARKER in line
    ]
    return has_copyright, has_licence, expressions


def referenced_licences(expressions: list[str]) -> set[str]:
    result: set[str] = set()
    for expression in expressions:
        for token in LICENSE_TOKEN_RE.findall(expression):
            if token in SPDX_OPERATORS:
                continue
            result.add(token)
    return result


def licence_file_exists(identifier: str) -> bool:
    directory = ROOT / "LICENSES"
    return any((directory / f"{identifier}{suffix}").is_file() for suffix in (".txt", ".md", ".html"))


def main() -> int:
    failures: list[str] = []
    try:
        paths = tracked_paths()
        annotations = reuse_annotations()
    except (OSError, UnicodeError, subprocess.CalledProcessError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"BLOCKED: unable to evaluate licensing metadata: {exc}")
        return 2

    all_expressions: list[str] = []
    for relative in paths:
        if is_reuse_exempt(relative) or covered_by_reuse(relative, annotations):
            continue
        absolute = ROOT / relative
        has_copyright, has_licence, expressions = read_spdx_lines(absolute)
        all_expressions.extend(expressions)
        if not has_copyright:
            failures.append(f"{relative}: missing SPDX-FileCopyrightText or REUSE annotation")
        if not has_licence:
            failures.append(f"{relative}: missing SPDX-License-Identifier or REUSE annotation")

    for entry in annotations:
        expression = entry.get("SPDX-License-Identifier")
        if isinstance(expression, str):
            all_expressions.append(expression)

    for identifier in sorted(referenced_licences(all_expressions)):
        if not licence_file_exists(identifier):
            failures.append(f"missing LICENSES file for SPDX identifier: {identifier}")

    if failures:
        print("BLOCKED: licence metadata violations found")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"PASS: licence metadata checked for {len(paths)} tracked files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
