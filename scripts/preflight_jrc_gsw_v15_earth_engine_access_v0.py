# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline JRC GSW1.5 Earth Engine route assessment, not a network adapter.

Publisher dataset reuse != Google Earth Engine commercial service rights.
An official asset identifier is NOT evidence of an authenticated entitlement,
post-2026-11-10 corrected pixels, raw-byte download or CAT model admission.
No credentials, environment access, network calls or provider bytes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tomllib

POLICY_FILE = (
    Path(__file__).resolve().parents[1]
    / "research_runners/policies/jrc_gsw_v15_earth_engine_access_v0.toml"
)
SOURCE_ID = "ec-jrc.global-surface-water.1984-2024"
ASSET_ID = "projects/global-surface-water/assets/GSW1_5/Occurrence"
PUBLISHER_DOCS = "https://global-surface-water.appspot.com/download"
EE_ACCESS = "https://developers.google.com/earth-engine/guides/access"
EE_COMMERCIAL = (
    "https://developers.google.com/earth-engine/guides/transition_to_commercial"
)
REVIEW_FLAGS = (
    "reviewed_registered_commercial_cloud_project",
    "reviewed_paid_earth_engine_subscription",
    "reviewed_enabled_api_and_project_iam",
    "reviewed_exact_asset_visibility",
)
NEVER_AUTOMATIC_FLAGS = (
    "reviewed_post_correction_native_pixels",
    "reviewed_raw_bytes_persistence_rights",
    "live_network_probe_approved",
    "cat_model_input_approved",
    "web_map_rgb_numeric_input_approved",
)
TEXT_EXPECTATIONS = {
    "schema_version": "1.0.0",
    "source_id": SOURCE_ID,
    "delivery_service": "Google Earth Engine",
    "publisher_asset_id": ASSET_ID,
    "source_period": "1984-2024",
    "source_product": "aggregated_occurrence",
    "publisher_correction_announcement_date": "2026-11-10",
    "publisher_asset_documentation_url": PUBLISHER_DOCS,
    "service_access_requirements_url": EE_ACCESS,
    "commercial_subscription_rules_url": EE_COMMERCIAL,
    "publisher_dataset_reuse": "allowed_with_attribution",
    "required_attribution": "Source: EC JRC/Google",
    "intended_use": "commercial_insurance_cat_research",
}
BOOL_FIELDS = REVIEW_FLAGS + NEVER_AUTOMATIC_FLAGS
REQUIRED_FIELDS = set(TEXT_EXPECTATIONS) | set(BOOL_FIELDS) | {
    "service_registration_state", "approved_network_requests", "access_note"
}


class EarthEngineRouteBlocked(ValueError):
    """Unsupported or unsafe published-source/service routing assertion."""


def inspect_policy(policy: dict[str, object]) -> dict[str, object]:
    """Emit a non-authorizing metadata receipt with explicit access blockers."""
    if type(policy) is not dict or set(policy) != REQUIRED_FIELDS:
        raise EarthEngineRouteBlocked("Earth Engine policy keys missing/extra")
    for key, value in TEXT_EXPECTATIONS.items():
        if policy.get(key) != value or type(policy.get(key)) is not str:
            raise EarthEngineRouteBlocked(f"wrong fixed JRC v1.5 route: {key}")
    if policy.get("service_registration_state") not in {
        "unconfigured", "under_manual_review", "reviewed_commercial"
    } or type(policy.get("service_registration_state")) is not str:
        raise EarthEngineRouteBlocked("unknown Earth Engine registration state")
    note = policy.get("access_note")
    if type(note) is not str or not note.strip():
        raise EarthEngineRouteBlocked("nonempty separate-host access note required")
    for name in BOOL_FIELDS:
        if type(policy.get(name)) is not bool:
            raise EarthEngineRouteBlocked(f"non-boolean Earth Engine flag: {name}")
    if type(policy.get("approved_network_requests")) is not int:
        raise EarthEngineRouteBlocked("network request budget must be an integer")
    if policy["approved_network_requests"] != 0:
        raise EarthEngineRouteBlocked("no live request authorization in offline policy")
    for name in NEVER_AUTOMATIC_FLAGS:
        if policy[name] is not False:
            raise EarthEngineRouteBlocked(f"unsupported scientific or network trust promotion: {name}")
    blockers = [name for name in REVIEW_FLAGS if not policy[name]]
    if policy["service_registration_state"] != "reviewed_commercial":
        blockers.append("reviewed_commercial_cloud_registration_status")
    # Completing the prerequisites still does NOT grant execution. The
    # future original-source probe needs a separately reviewed contract.
    return {
        "profile": "jrc_gsw_v15_earth_engine_alternative_offline_v0",
        "source_id": SOURCE_ID,
        "original_publisher_earth_engine_asset_id": ASSET_ID,
        "original_publisher_asset_id_documented": True,
        "publisher_data_commercial_reuse_allowed_with_attribution": True,
        "service_kind": "Google Earth Engine authenticated",
        "commercial_cloud_service_prerequisites_met_on_paper": not blockers,
        "missing_commercial_service_prerequisites": blockers,
        "google_project_or_credentials_read": False,
        "google_earth_engine_api_request_executed": False,
        "google_earth_engine_request_authorized_by_this_policy": False,
        "post_2026_11_10_corrected_original_values_verified": False,
        "raw_source_bytes_persisted": False,
        "rgb_wmts_accepted_as_numeric_source": False,
        "model_input_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy-file", type=Path, default=POLICY_FILE)
    args = parser.parse_args(argv)
    try:
        # Metadata policy only; user-provided file never supplies a URL
        # or overrides the fixed original source/asset checks.
        raw = args.policy_file.read_bytes()
        if len(raw) > 8192:
            raise EarthEngineRouteBlocked("policy exceeds 8 KiB")
        result = inspect_policy(tomllib.loads(raw.decode("utf-8")))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, EarthEngineRouteBlocked) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
