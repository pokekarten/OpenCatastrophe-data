#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bind ESRM20 v1.0 Group1 minimum loss to the reconstructed Kosovo config.

The official Group1 INI is pinned by Project 269, immutable Git commit, byte
count and SHA-256. The Kosovo reconstruction is compared byte-for-byte with
the existing deterministic bounded transform, and both runtime scalar
projections must declare a 2000 EUR structural minimum loss.

This is SOURCE-CONFIG equivalence only. Neither the historical Group1
assignment for all Kosovo published losses nor the settings actually used to
produce the ESRM20 country viewer are established by a matching template.
The latter's threshold/reference compatibility remains UNKNOWN.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts import build_esrm20_kosovo_residential_ebrisk_config as config
from scripts import project_esrm20_group1_risk_runtime_scalars as runtime

SCHEMA_VERSION = "oc-eq1-esrm20-group1-kosovo-threshold-link-v1"
EXPECTED_MODE = "ebrisk"
EXPECTED_MINIMUM_LOSS = "2000"
MAX_SOURCE_BYTES = 8192
MAX_DERIVED_BYTES = 8192


class SourceThresholdLinkError(ValueError):
    """Exact frozen Group1 vs reconstructed source setting cannot be proven."""


def compare_profiles(
    *,
    source_profile: dict[str, Any],
    derived_runtime: dict[str, Any],
    reconstructed_bytes_identical: bool,
) -> dict[str, Any]:
    """Compare independently parsed settings without deriving missing defaults."""

    if type(source_profile) is not dict or type(derived_runtime) is not dict:
        raise SourceThresholdLinkError("runtime profile missing")
    expected_source = {
        "schema_version": runtime.SCHEMA_VERSION,
        "project_id": config.PROJECT_ID,
        "project_path": config.PROJECT_PATH,
        "commit_sha": config.COMMIT_SHA,
        "candidate_key": config.GROUP1_KEY,
        "repository_path": config.GROUP1_PATH,
        "byte_count": config.GROUP1_BYTE_COUNT,
        "sha256": config.GROUP1_SHA256,
        "raw_config_returned": False,
        "external_bytes_persisted": False,
        "historical_group_assignment_verified": False,
        "runtime_compatibility_verified": False,
        "numerical_loss_reproduction_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for key, expected in expected_source.items():
        if type(source_profile.get(key)) is not type(expected) or source_profile[key] != expected:
            raise SourceThresholdLinkError("Group1 source identity or authority drifted")
    if reconstructed_bytes_identical is not True:
        raise SourceThresholdLinkError("derived Kosovo config is not exact deterministic projection")
    for label, settings in (
        ("source", source_profile.get("runtime_scalars")),
        ("derived", derived_runtime),
    ):
        if type(settings) is not dict:
            raise SourceThresholdLinkError(f"{label} runtime setting profile missing")
        if (
            settings.get("calculation_mode_present") is not True
            or settings.get("calculation_mode") != EXPECTED_MODE
            or settings.get("minimum_asset_loss_structural_present") is not True
            or settings.get("minimum_asset_loss_structural") != EXPECTED_MINIMUM_LOSS
            or settings.get("defaults_inferred") is not False
        ):
            raise SourceThresholdLinkError(f"{label} explicit ebrisk/minimum-loss source drifted")
    if (
        source_profile["runtime_scalars"]["minimum_asset_loss_structural"]
        != derived_runtime["minimum_asset_loss_structural"]
    ):
        raise SourceThresholdLinkError("Group1 to Kosovo threshold differs")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "GROUP1_SOURCE_TO_RECONSTRUCTED_THRESHOLD_EQUIVALENT",
        "frozen_provider": {
            "project_id": config.PROJECT_ID,
            "commit_sha": config.COMMIT_SHA,
            "repository_path": config.GROUP1_PATH,
            "byte_count": config.GROUP1_BYTE_COUNT,
            "sha256": config.GROUP1_SHA256,
        },
        "source_group1_declares_ebrisk": True,
        "reconstructed_kosovo_declares_ebrisk": True,
        "source_group1_minimum_asset_loss_structural_eur": 2000,
        "reconstructed_minimum_asset_loss_structural_eur": 2000,
        "byte_identical_to_canonical_kosovo_transform": True,
        "source_config_threshold_match_verified": True,
        "historical_group_assignment_verified": False,
        "published_esrm20_same_group_config_verified": False,
        "published_esrm20_same_threshold_verified": False,
        "threshold_compatibility_verified": False,
        "denominator_semantics_verified": False,
        "annualization_semantics_verified": False,
        "reference_loss_agreement_verified": False,
        "external_bytes_persisted": False,
        "provider_values_returned": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _read_bounded_file(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise SourceThresholdLinkError("staged source config is not an ordinary file")
    with path.open("rb") as stream:
        payload = stream.read(limit + 1)
    if not payload or len(payload) > limit:
        raise SourceThresholdLinkError("staged config violates bounded byte limit")
    return payload


def run(group1_path: Path, reconstructed_path: Path) -> dict[str, Any]:
    group1 = _read_bounded_file(group1_path, MAX_SOURCE_BYTES)
    reconstructed = _read_bounded_file(reconstructed_path, MAX_DERIVED_BYTES)
    canonical_derived, _ = config.build_kosovo_residential_ebrisk_config(group1)
    if reconstructed != canonical_derived:
        raise SourceThresholdLinkError("staged reconstruction differs from canonical transform")
    group1_profile = runtime.project_group1_risk_runtime_scalars(group1)
    try:
        derived_text = reconstructed.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceThresholdLinkError("reconstructed config is not UTF-8") from exc
    derived_profile = runtime.project_runtime_scalars_from_verified_text(derived_text)
    return compare_profiles(
        source_profile=group1_profile,
        derived_runtime=derived_profile,
        reconstructed_bytes_identical=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-group1-config", type=Path, required=True)
    parser.add_argument("--reconstructed-kosovo-config", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.source_group1_config, args.reconstructed_kosovo_config)
    except (SourceThresholdLinkError, OSError, config.KosovoResidentialEbriskConfigError,
            runtime.RiskRuntimeScalarError, ValueError):
        print(json.dumps({
            "schema_version": SCHEMA_VERSION,
            "status": "BLOCKED",
            "source_config_threshold_match_verified": False,
            "published_esrm20_same_threshold_verified": False,
            "threshold_compatibility_verified": False,
            "reference_loss_agreement_verified": False,
            "model_use_authorized": False,
        }, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
