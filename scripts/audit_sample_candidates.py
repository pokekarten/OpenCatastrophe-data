# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Audit admitted manifests for bounded raw-sample proposal eligibility.

This tool deliberately separates two questions:

1. Do the recorded source rights/privacy/access facts permit proposing a bounded
   raw sample for asset-specific review?
2. Does the current repository manifest already authorize publishing its exact
   raw artifact?

A positive answer to (1) never implies (2). Small size does not waive exact
artifact identity, attribution, privacy/confidentiality, or repository review.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from validate_manifest import (
    ManifestError,
    assert_public_asset_allowed,
    load_manifest,
    validate_structure,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_DIR = ROOT / "manifests"


@dataclass(frozen=True)
class SampleAuditResult:
    dataset_id: str
    access_class: str
    source_rights_eligible: bool
    existing_raw_publication_ready: bool
    status: str
    source_blockers: tuple[str, ...]
    repository_publication_blocker: str | None


def source_rights_blockers(manifest: dict[str, Any]) -> tuple[str, ...]:
    """Return fail-closed blockers for proposing a bounded raw sample.

    This is intentionally narrower than a legal conclusion. It only evaluates
    the structured facts already admitted in the manifest. Asset-specific
    acquisition identity and repository review remain separate gates.
    """

    validate_structure(manifest)
    licensing = manifest["licensing"]
    redistribution = manifest["redistribution"]
    privacy = manifest["privacy"]

    blockers: list[str] = []
    if manifest["access_class"] in {"unknown", "restricted"}:
        blockers.append("source_access_not_publicly_acquirable")
    if licensing["status"] != "verified":
        blockers.append("licensing_not_verified")
    if licensing["commercial_use_status"] != "allowed":
        blockers.append("commercial_use_not_allowed")
    if redistribution["status"] != "allowed":
        blockers.append("redistribution_not_allowed")
    if redistribution["scope"] != "raw":
        blockers.append("raw_redistribution_not_in_scope")
    if privacy["personal_data_status"] != "none":
        blockers.append("personal_data_not_clear")
    if privacy["confidential_or_proprietary_status"] != "none":
        blockers.append("confidentiality_not_clear")
    return tuple(blockers)


def audit_manifest(manifest: dict[str, Any]) -> SampleAuditResult:
    blockers = source_rights_blockers(manifest)
    source_eligible = not blockers

    repository_blocker: str | None = None
    repository_raw_allowed = False
    try:
        assert_public_asset_allowed(manifest, "raw")
    except ManifestError as exc:
        repository_blocker = str(exc)
    else:
        repository_raw_allowed = True

    existing_raw_ready = source_eligible and repository_raw_allowed
    if repository_raw_allowed and not source_eligible:
        repository_blocker = "sample source contract blocks raw publication"

    if existing_raw_ready:
        status = "existing_raw_publication_ready"
    elif source_eligible:
        status = "eligible_for_asset_specific_sample_review"
    else:
        status = "blocked_by_source_contract"

    return SampleAuditResult(
        dataset_id=manifest["dataset_id"],
        access_class=manifest["access_class"],
        source_rights_eligible=source_eligible,
        existing_raw_publication_ready=existing_raw_ready,
        status=status,
        source_blockers=blockers,
        repository_publication_blocker=repository_blocker,
    )


def audit_manifest_directory(manifest_dir: Path = DEFAULT_MANIFEST_DIR) -> list[SampleAuditResult]:
    paths = sorted(manifest_dir.glob("*.json"))
    if not paths:
        raise ManifestError(f"no manifests found in {manifest_dir}")
    return [audit_manifest(load_manifest(path)) for path in paths]


def _json_payload(results: list[SampleAuditResult]) -> str:
    return json.dumps(
        [asdict(result) for result in results],
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )


def _text_payload(results: list[SampleAuditResult]) -> str:
    lines = []
    for result in results:
        if result.source_blockers:
            detail = ",".join(result.source_blockers)
        elif result.repository_publication_blocker:
            detail = result.repository_publication_blocker
        else:
            detail = "none"
        lines.append(
            "\t".join(
                (
                    result.status,
                    result.dataset_id,
                    f"access={result.access_class}",
                    f"detail={detail}",
                )
            )
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Classify admitted manifests for bounded raw-sample proposal eligibility "
            "without weakening the existing raw publication gate."
        )
    )
    parser.add_argument("--manifest-dir", type=Path, default=DEFAULT_MANIFEST_DIR)
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    args = parser.parse_args()

    try:
        results = audit_manifest_directory(args.manifest_dir)
    except ManifestError as exc:
        print(f"BLOCKED: {exc}")
        return 1

    print(_json_payload(results) if args.json else _text_payload(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
