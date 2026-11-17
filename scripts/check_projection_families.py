# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail closed when canonical JSON escapes a registered projection family."""

from __future__ import annotations

import json
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
        if self.name == "research_receipts":
            return (
                len(parts) == 3
                and parts[0] == "docs"
                and parts[1] == "research"
                and relative.name == "insurer-directory-original-page-receipt-20261101.json"
            )
        raise RuntimeError(f"unknown projection-family implementation: {self.name}")


# Explicitly scoped non-canonical research snapshots already on main.
# These are NOT generated source projections; unknown research JSON stays rejected.
RESEARCH_ONLY_STANDALONE_JSON_SCHEMAS = {
    PurePosixPath("research/observations/knmi_historical_downloads.json"):
        "KNMI_HISTORICAL_ACQUISITION_V1",
    PurePosixPath("research/observations/knmi_wind_metadata_review.json"):
        "KNMI_WIND_METADATA_REVIEW_V1",
    PurePosixPath("research/source_screening/windstorm_whole_chain.json"):
        "WINDSTORM_WHOLE_CHAIN_SCREEN_V1",
    PurePosixPath("research/observations/climk_gunter_date_resolution_reference.json"):
        "CLIMK_GUNTER_DATE_RESOLUTION_REFERENCE_V1",
    PurePosixPath("research/observations/wind_sources_downloads_20261115.json"):
        "__SOURCE_DOWNLOAD_RECEIPT_ROWS__",
    PurePosixPath("research/observations/xws_downloads_20261115.json"):
        "__SOURCE_DOWNLOAD_RECEIPT_ROWS__",
}


FAMILIES = (
    ProjectionFamily("access", ("scripts/render_public_views.py", "--check")),
    ProjectionFamily("manifests", ("scripts/render_public_views.py", "--check")),
    ProjectionFamily("landscape", ("scripts/render_public_views.py", "--check")),
    ProjectionFamily("schemas", ("scripts/schema_reference.py", "--check")),
    ProjectionFamily("research_receipts", ("scripts/insurer_directory_receipt_projection.py", "--check")),
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
        required_research_schema = RESEARCH_ONLY_STANDALONE_JSON_SCHEMAS.get(relative)
        if required_research_schema is not None:
            try:
                research_record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                errors.append(f"invalid standalone research JSON: {relative}")
                continue
            if required_research_schema == "__SOURCE_DOWNLOAD_RECEIPT_ROWS__":
                # These two older receipts are JSON arrays, not canonical JSON/MD
                # projection families. Demand exact nonempty receipt row shape.
                if not (
                    isinstance(research_record, list)
                    and research_record
                    and all(
                        isinstance(row, dict)
                        and isinstance(row.get("file"), str)
                        and bool(row["file"])
                        and isinstance(row.get("url"), str)
                        and row["url"].startswith("https://")
                        and isinstance(row.get("sha256"), str)
                        and len(row["sha256"]) == 64
                        and all(c in "0123456789abcdef" for c in row["sha256"])
                        and type(row.get("bytes")) is int
                        and row["bytes"] > 0
                        and row.get("status") == "downloaded"
                        for row in research_record
                    )
                ):
                    errors.append(f"standalone research download receipt mismatch: {relative}")
                continue
            if (
                not isinstance(research_record, dict)
                or research_record.get("schema") != required_research_schema
            ):
                errors.append(f"standalone research JSON schema mismatch: {relative}")
            continue
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
