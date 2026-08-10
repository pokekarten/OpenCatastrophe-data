# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Run the repository definition-of-done checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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


def main() -> int:
    if not in_git_checkout():
        print("BLOCKED: check_all must run from a Git checkout")
        return 2

    commands = [
        [sys.executable, "-m", "compileall", "-q", "scripts", "tests"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test*.py", "-v"],
        [sys.executable, "scripts/check_repository_hygiene.py"],
        [sys.executable, "scripts/check_license_metadata.py"],
        ["git", "diff", "--check"],
        ["git", "diff", "--cached", "--check"],
    ]
    for command in commands:
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

    print(f"\nPASS: OpenCatastrophe-data checks succeeded ({len(manifests)} admitted manifests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
