# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail closed when canonical JSON escapes a registered projection family."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ProjectionFamily:
    name: str
    checker: tuple[str, ...]

    def matches(self, relative: PurePosixPath) -> bool:
        parts = relative.parts
        if self.name == "access":
            return len(parts) == 2 and parts[0] == "access" and relative.suffix == ".json"
        if self.name == "manifests":
            return len(parts) == 2 and parts[0] == "manifests" and relative.suffix == ".json"
        if self.name == "landscape":
            return (
                len(parts) == 2
                and parts[0] == "landscape"
                and relative.name.startswith("sources")
                and relative.suffix == ".json"
            )
        if self.name == "schemas":
            return (
                len(parts) == 2
                and parts[0] == "schemas"
                and relative.name.endswith(".schema.json")
            )
        raise RuntimeError(f"unknown projection-family implementation: {self.name}")


FAMILIES = (
    ProjectionFamily("access", ("scripts/render_public_views.py", "--check")),
    ProjectionFamily("manifests", ("scripts/render_public_views.py", "--check")),
    ProjectionFamily("landscape", ("scripts/render_public_views.py", "--check")),
    ProjectionFamily("schemas", ("scripts/schema_reference.py", "--check")),
)


def _json_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.json")
        if ".git" not in path.relative_to(root).parts and path.is_file()
    )


def check_inventory(root: Path = ROOT) -> tuple[list[str], int]:
    errors: list[str] = []
    json_files = _json_files(root)

    for family in FAMILIES:
        checker_path = root / family.checker[0]
        if not checker_path.is_file():
            errors.append(
                f"registered projection family {family.name!r} has no checker: "
                f"{family.checker[0]}"
            )

    for path in json_files:
        relative = PurePosixPath(path.relative_to(root).as_posix())
        matches = [family for family in FAMILIES if family.matches(relative)]
        if len(matches) != 1:
            if not matches:
                errors.append(f"unregistered JSON projection family: {relative}")
            else:
                names = ", ".join(family.name for family in matches)
                errors.append(f"JSON belongs to multiple projection families ({names}): {relative}")
            continue

        markdown = path.with_suffix(".md")
        if not markdown.is_file():
            errors.append(
                f"registered canonical JSON lacks same-basename Markdown projection: {relative}"
            )

    return errors, len(json_files)


def checker_commands() -> tuple[tuple[str, ...], ...]:
    """Return each registered checker command once, preserving registry order."""
    commands: list[tuple[str, ...]] = []
    for family in FAMILIES:
        if family.checker not in commands:
            commands.append(family.checker)
    return tuple(commands)


def run_registered_checkers(root: Path = ROOT) -> bool:
    for command in checker_commands():
        full = [sys.executable, *command]
        print(f"==> {' '.join(full)}", flush=True)
        result = subprocess.run(full, cwd=root, check=False)
        if result.returncode:
            print(f"FAILED ({result.returncode}): {' '.join(full)}")
            return False
    return True


def main() -> int:
    errors, count = check_inventory(ROOT)
    if errors:
        print("BLOCKED: JSON projection registry check failed")
        for error in errors:
            print(f"- {error}")
        return 1

    if not run_registered_checkers(ROOT):
        return 1

    print(f"PASS: {count} canonical JSON files belong to registered projection families")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
