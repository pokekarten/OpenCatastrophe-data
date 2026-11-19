# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Run the repository definition-of-done checks."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Keep this list small and centered on the repository-wide safety contracts.
# Fast preflight is not an alternative to full scientific/source-specific tests.
FAST_TEST_MODULES = (
    "tests.test_check_all_modes",
    "tests.test_agent_artifact_contracts",
    "tests.test_contract_consistency",
    "tests.test_source_access_failclosed_state",
    "tests.test_check_yaml_mapping_keys",
    "tests.test_repository_hygiene",
    "tests.test_check_projection_families",
    "tests.test_schema_reference",
)


def run(command: list[str]) -> bool:
    print(f"\n==> {' '.join(command)}", flush=True)
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode:
        print(f"FAILED ({result.returncode}): {' '.join(command)}")
        return False
    return True


def in_git_checkout() -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def commands_for_mode(*, fast: bool) -> list[list[str]]:
    """Share all structural/security gates; only the test breadth changes."""
    test_command = (
        [sys.executable, "-m", "unittest", *FAST_TEST_MODULES]
        if fast else
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test*.py", "-v"]
    )
    return [
        [sys.executable, "-m", "compileall", "-q", "scripts", "research_runners", "tests"],
        test_command,
        [sys.executable, "scripts/check_projection_families.py"],
        [sys.executable, "scripts/check_yaml_mapping_keys.py"],
        [sys.executable, "scripts/check_markdown_links.py"],
        [sys.executable, "scripts/check_repository_hygiene.py"],
        [sys.executable, "scripts/check_license_metadata.py"],
        ["git", "diff", "--check"],
        ["git", "diff", "--cached", "--check"],
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fast", action="store_true",
        help="Preflight: focused contract tests plus every structural/security gate; "
             "NOT the full test suite.",
    )
    options = parser.parse_args([] if argv is None else argv)
    if not in_git_checkout():
        print("BLOCKED: check_all must run from a Git checkout")
        return 2

    if options.fast:
        print("FAST PREFLIGHT ONLY: full/source-specific tests are NOT executed", flush=True)
    for command in commands_for_mode(fast=options.fast):
        if not run(command):
            return 1

    manifests = sorted((ROOT / "manifests").glob("*.json"))
    for path in manifests:
        if not run([
            sys.executable,
            "scripts/validate_manifest.py",
            str(path.relative_to(ROOT)),
            "--public-asset",
            "metadata",
        ]):
            return 1

    label = "fast preflight" if options.fast else "full definition-of-done"
    print(f"\nPASS: OpenCatastrophe-data {label} checks succeeded ({len(manifests)} admitted manifests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
