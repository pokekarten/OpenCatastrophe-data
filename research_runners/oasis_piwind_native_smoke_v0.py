# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Run one pinned, fictional OasisPiWind model and attest native GUL/IL/RI outputs.

This research runner is for an isolated CI runner only. It intentionally
rejects missing/ambiguous outputs and does not promote any real insurer model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

MODEL_COMMIT = "94820c59f169b222d4c1a72256ff0a8f86a9e5bf"
OASIS_VERSION = "2.5.8"
OUTPUT_KINDS = ("palt", "psept")
LOSS_STREAMS = ("gul", "il", "ri")
EXPECTED_FILES = tuple(f"{stage}_S1_{kind}.csv" for stage in LOSS_STREAMS for kind in OUTPUT_KINDS)
MAX_OUTPUT_BYTES = 20_000_000


class PiWindNativeSmokeError(ValueError):
    """The engine proof is not complete or fails an explicit trust boundary."""


def blob_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def attest_output_csv(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise PiWindNativeSmokeError("required ORD output is absent or a symbolic link")
    size = path.stat().st_size
    if not 1 <= size <= MAX_OUTPUT_BYTES:
        raise PiWindNativeSmokeError("required ORD output has invalid size")
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        rows = list(csv.reader(text.splitlines(), strict=True))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise PiWindNativeSmokeError("required ORD output is malformed") from exc
    if len(rows) < 2 or not rows[0] or any(not col.strip() for col in rows[0]):
        raise PiWindNativeSmokeError("required ORD output is empty or has no valid header")
    fields = len(rows[0])
    if fields < 3 or any(len(row) != fields for row in rows[1:]):
        raise PiWindNativeSmokeError("required ORD output has inconsistent row fields")
    return {"bytes": len(raw), "sha256": blob_sha256(raw), "data_rows": len(rows) - 1}


def inspect_piwind_outputs(run_root: Path) -> dict[str, dict[str, object]]:
    if not run_root.is_dir() or run_root.is_symlink():
        raise PiWindNativeSmokeError("native run output root is missing")
    matching: list[Path] = []
    for output in run_root.rglob("output"):
        if output.is_dir() and not output.is_symlink() and all((output / file).is_file() for file in EXPECTED_FILES):
            matching.append(output)
    if len(matching) != 1:
        raise PiWindNativeSmokeError("expected exactly one complete native GUL/IL/RI output directory")
    result: dict[str, dict[str, object]] = {}
    for filename in EXPECTED_FILES:
        result[filename] = attest_output_csv(matching[0] / filename)
    return result


def verify_model_checkout(model_dir: Path) -> str:
    if not model_dir.is_dir() or model_dir.is_symlink():
        raise PiWindNativeSmokeError("model checkout must be a real directory")
    try:
        response = subprocess.run(
            ["git", "-C", str(model_dir), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise PiWindNativeSmokeError("could not independently verify model git commit") from exc
    if response.stdout.strip() != MODEL_COMMIT:
        raise PiWindNativeSmokeError("model checkout does not match pinned public Git commit")
    if not (model_dir / "oasislmf.json").is_file():
        raise PiWindNativeSmokeError("pinned model lacks the expected Oasis config")
    return response.stdout.strip()


def native_run(model_dir: Path, *, timeout_seconds: int) -> dict[str, object]:
    if not 30 <= timeout_seconds <= 1200:
        raise PiWindNativeSmokeError("runtime limit must be between 30 and 1200 seconds")
    commit = verify_model_checkout(model_dir)
    try:
        installed_version = metadata.version("oasislmf")
    except metadata.PackageNotFoundError as exc:
        raise PiWindNativeSmokeError("oasislmf Python distribution is not installed") from exc
    if installed_version != OASIS_VERSION:
        raise PiWindNativeSmokeError("installed OasisLMF version differs from pinned version")
    cli = shutil.which("oasislmf")
    if not cli:
        raise PiWindNativeSmokeError("oasislmf executable not on PATH")
    output_root = model_dir / "runs"
    if output_root.exists():
        raise PiWindNativeSmokeError("model checkout already contains run outputs; use a fresh clone")

    env = os.environ.copy()
    env.update({"NUMBA_NUM_THREADS": "2", "OMP_NUM_THREADS": "2"})
    log_path = model_dir.parent / "native-piwind-output.log"
    started = time.monotonic()
    try:
        with log_path.open("wb") as log:
            process = subprocess.run(
                [cli, "model", "run", "-C", "oasislmf.json"],
                cwd=model_dir, stdout=log, stderr=subprocess.STDOUT,
                timeout=timeout_seconds, env=env, check=False,
            )
    except subprocess.TimeoutExpired as exc:
        raise PiWindNativeSmokeError("native Oasis PiWind model run timed out") from exc
    except OSError as exc:
        raise PiWindNativeSmokeError("native Oasis PiWind model run could not start") from exc
    elapsed = round(time.monotonic() - started, 3)
    if process.returncode != 0:
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-5000:]
        raise PiWindNativeSmokeError(f"native Oasis process exited with {process.returncode}; log tail:\n{tail}")
    outputs = inspect_piwind_outputs(output_root)
    return {
        "receipt_kind": "piwind_pinned_native_engine_research_v0",
        "status": "native_engine_demo_outputs_verified",
        "model_repository": "OasisLMF/OasisPiWind",
        "model_commit": commit,
        "oasislmf_version": installed_version,
        "duration_seconds": elapsed,
        "source_demo_inputs_only": True,
        "native_oasis_run_verified": True,
        "result_loss_streams": list(LOSS_STREAMS),
        "ord_csv": outputs,
        "original_insurer_exposure_verified": False,
        "hazard_calibration_verified": False,
        "physical_event_independence_verified": False,
        "insurer_gross_net_oep_aep_verified": False,
        "real_treaty_and_retro_verified": False,
        "external_model_or_result_bytes_committed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_dir", type=Path, help="fresh checkout of the pinned public PiWind source")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--receipt", type=Path, help="output research JSON outside the repository")
    args = parser.parse_args(argv)
    try:
        result = native_run(args.model_dir.resolve(), timeout_seconds=args.timeout_seconds)
        payload = json.dumps(result, sort_keys=True, indent=2) + "\n"
        if args.receipt is not None:
            if args.receipt.exists():
                raise PiWindNativeSmokeError("refuse to overwrite an existing output receipt")
            if not args.receipt.parent.is_dir():
                raise PiWindNativeSmokeError("receipt parent must exist")
            args.receipt.write_text(payload, encoding="utf-8")
        print(payload, end="")
        return 0
    except PiWindNativeSmokeError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
