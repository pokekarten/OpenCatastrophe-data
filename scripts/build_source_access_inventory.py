# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Build a deterministic first-pass access inventory for every known source.

Coverage includes both non-admission ``landscape/sources*.json`` candidates and
all admitted ``manifests/*.json`` datasets. The inventory is deliberately
conservative: it translates already recorded access/rights evidence into a
machine-access work queue, never invents provider API facts, and never upgrades
rights. Concrete reviewed interfaces live in ``access/*.json`` contracts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.validate_source_access import SourceAccessError, validate_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from validate_source_access import SourceAccessError, validate_path

ROOT = Path(__file__).resolve().parents[1]
LANDSCAPE_DIR = ROOT / "landscape"
MANIFEST_DIR = ROOT / "manifests"
ACCESS_DIR = ROOT / "access"
DEFAULT_OUTPUT = ACCESS_DIR / "source-access-inventory.json"


class InventoryError(ValueError):
    """Raised when canonical source state cannot be inventoried safely."""


def _reject_constant(value: str) -> None:
    raise InventoryError(f"non-finite JSON number is forbidden: {value}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InventoryError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text, object_pairs_hook=_strict_object, parse_constant=_reject_constant)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InventoryError(f"cannot load {path}: {exc}") from exc


def _contains(text: str, *needles: str) -> bool:
    folded = text.casefold().replace("-", "_")
    return any(needle.casefold().replace("-", "_") in folded for needle in needles)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.casefold()))


def classify_access(hint: str, categories: list[str], note: str) -> dict[str, Any]:
    """Conservatively classify recorded discovery hints without inventing API facts."""

    evidence = " ".join([hint, *categories, note]).casefold()
    category_set = {value.casefold() for value in categories}

    # API is a semantic token, not a substring: e.g. "rapid" and "capital" must
    # not be promoted merely because their spelling happens to contain "api".
    api_like = "api" in _tokens(hint) or "api" in category_set
    geospatial = _contains(hint, "stac", "wms", "wfs", "wcs", "arcgis", "web_services", "geospatial_service")
    federated = _contains(hint, "mqtt", "federated", "data_exchange")
    downloadable = _contains(hint, "download", "object", "cloud", "geoparquet", "repository", "ftp", "file", "bulk")
    service = _contains(hint, "service", "portal", "catalog", "explorer")
    provider_gate = _contains(hint, "registration", "registered", "account", "authenticated", "token", "eu_login", "earthdata")
    provider_agreement = _contains(hint, "agreement", "request", "paid", "license_request", "licence_request")

    if geospatial:
        machine_access_class = "geospatial_service"
        api_status = "documented_candidate"
    elif federated:
        machine_access_class = "federated_service"
        api_status = "documented_candidate"
    elif api_like:
        machine_access_class = "api"
        api_status = "documented_candidate"
    elif downloadable:
        machine_access_class = "bulk_or_file"
        api_status = "non_api_machine_access"
    elif provider_agreement:
        machine_access_class = "restricted_provider_access"
        api_status = "research_required"
    elif service:
        machine_access_class = "portal_or_service"
        api_status = "research_required"
    else:
        machine_access_class = "research_required"
        api_status = "research_required"

    if provider_agreement:
        authentication_posture = "provider_agreement_or_request"
    elif provider_gate:
        authentication_posture = "registration_or_credentials_required"
    elif _contains(hint, "public", "open", "unrestricted"):
        authentication_posture = "anonymous_or_not_stated"
    else:
        authentication_posture = "unknown"

    flags: list[str] = []
    restriction_patterns = {
        "noncommercial_or_noncommercial_variant": ("noncommercial", "non_commercial", "non-commercial"),
        "commercial_use_restriction": ("commercial use not allowed", "commercial_use_restricted", "paid commercial", "commercial license", "commercial licence"),
        "separate_license_or_agreement": ("separate license", "separate licence", "by agreement", "license request", "licence request"),
        "redistribution_or_reuse_restriction": ("redistribution", "reuse restricted", "provider-specific access", "provider specific access"),
        "registration_or_account_gate": ("registration", "registered", "account", "authenticated", "token", "eu login", "eu_login", "earthdata"),
    }
    for flag, patterns in restriction_patterns.items():
        if any(pattern.casefold() in evidence for pattern in patterns):
            flags.append(flag)

    rights_posture = "known_restriction_requires_review" if flags else "license_review_required"

    if rights_posture == "known_restriction_requires_review" or provider_agreement:
        decision = "document_only"
    elif machine_access_class == "api" and authentication_posture == "anonymous_or_not_stated":
        decision = "build_adapter_now"
    elif machine_access_class in {"api", "geospatial_service", "federated_service", "bulk_or_file"}:
        decision = "build_later"
    else:
        decision = "document_only"

    if machine_access_class == "api":
        next_action = "Verify authoritative API docs, exact auth/version/rate limits and API-specific terms; then add a source-access contract."
    elif machine_access_class in {"geospatial_service", "federated_service"}:
        next_action = "Verify exact service protocol/endpoints and terms; model it as a provider contract rather than forcing REST semantics."
    elif machine_access_class == "bulk_or_file":
        next_action = "Freeze authoritative machine-download resolution, version/mutability rules and byte-provenance receipt requirements."
    elif machine_access_class == "restricted_provider_access":
        next_action = "Document provider registration/agreement and legal constraints; do not automate acquisition until explicitly cleared."
    else:
        next_action = "Research whether an authoritative API, service, SDK or deterministic machine-download route exists; remain documentation-only until resolved."

    return {
        "machine_access_class": machine_access_class,
        "api_status": api_status,
        "authentication_posture": authentication_posture,
        "rights_posture": rights_posture,
        "license_or_terms_flags": sorted(flags),
        "automation_decision": decision,
        "next_action": next_action,
    }


def landscape_files() -> list[Path]:
    paths = sorted(LANDSCAPE_DIR.glob("sources*.json"))
    if not paths:
        raise InventoryError("no canonical landscape/sources*.json files found")
    return paths


def manifest_files() -> list[Path]:
    paths = sorted(MANIFEST_DIR.glob("*.json"))
    if not paths:
        raise InventoryError("no admitted manifests/*.json files found")
    return paths


def contract_files() -> list[Path]:
    if not ACCESS_DIR.exists():
        return []
    return sorted(path for path in ACCESS_DIR.glob("*.json") if path.name != DEFAULT_OUTPUT.name)


def _contract_index() -> tuple[dict[str, list[dict[str, str]]], list[str]]:
    by_source: dict[str, list[dict[str, str]]] = {}
    files: list[str] = []
    seen_access_ids: set[str] = set()
    for path in contract_files():
        try:
            payload = validate_path(path)
        except (OSError, SourceAccessError) as exc:
            raise InventoryError(f"invalid source-access contract {path.relative_to(ROOT)}: {exc}") from exc
        access_id = payload["access_id"]
        if access_id in seen_access_ids:
            raise InventoryError(f"duplicate source-access access_id: {access_id}")
        seen_access_ids.add(access_id)
        source_ids = payload["source_ids"]
        interface_type = payload["interface_type"]
        implementation = payload["implementation_decision"]
        status = payload["status"]
        relative = path.relative_to(ROOT).as_posix()
        files.append(relative)
        for source_id in source_ids:
            by_source.setdefault(source_id, []).append({
                "access_id": access_id,
                "interface_type": interface_type,
                "status": status,
                "implementation_decision": implementation,
            })
    for contracts in by_source.values():
        contracts.sort(key=lambda item: item["access_id"])
    return by_source, files


def _interface_class(interface_type: str) -> str:
    if interface_type in {"rest", "fdsn", "ogc_api", "arcgis_rest"}:
        return "api"
    if interface_type in {"stac", "wms", "wfs", "wcs"}:
        return "geospatial_service"
    if interface_type == "mqtt_http":
        return "federated_service"
    if interface_type in {"object_store", "http_file", "ftp_or_ftps", "provider_sdk"}:
        return "bulk_or_file"
    return "portal_or_service"


def _more_restrictive_decision(left: str, right: str) -> str:
    order = {
        "build_adapter_now": 0,
        "build_later": 1,
        "document_only": 2,
        "do_not_automate": 3,
    }
    if left not in order or right not in order:
        raise InventoryError(f"unknown automation decision while aggregating contracts: {left!r}, {right!r}")
    return left if order[left] >= order[right] else right


def _apply_contracts(
    classification: dict[str, Any],
    contracts: list[dict[str, str]],
    *,
    allow_contract_promotion: bool = False,
) -> dict[str, Any]:
    if not contracts:
        return {**classification, "contract_ids": []}
    result = dict(classification)
    result["contract_ids"] = [item["access_id"] for item in contracts]

    if len(contracts) > 1:
        # A source can legitimately expose multiple interfaces with different
        # rights/scope/auth semantics. Source-level execution must not depend on
        # lexicographic access_id ordering; keep the aggregate documentation-only
        # and require the caller to choose/review an exact contract.
        result["api_status"] = "multiple_concrete_contracts_present"
        result["machine_access_class"] = "multiple_reviewed_interfaces"
        result["automation_decision"] = _more_restrictive_decision(
            result["automation_decision"], "document_only"
        )
        if any(item["implementation_decision"] == "do_not_automate" for item in contracts):
            result["automation_decision"] = "do_not_automate"
        result["next_action"] = (
            "Select and verify one exact reviewed source-access contract by scope; "
            "never derive a source-level execution decision from contract ordering."
        )
        return result

    contract = contracts[0]
    result["api_status"] = "concrete_contract_present"
    result["machine_access_class"] = _interface_class(contract["interface_type"])
    contract_decision = contract["implementation_decision"]
    if allow_contract_promotion:
        result["automation_decision"] = contract_decision
    else:
        result["automation_decision"] = _more_restrictive_decision(
            result["automation_decision"], contract_decision
        )
    result["next_action"] = "Execute the reviewed contract verification ladder; do not infer rights, scientific fitness or admission from connectivity."
    return result


def _manifest_rights(manifest: dict[str, Any], classification: dict[str, Any]) -> dict[str, Any]:
    result = dict(classification)
    licensing = manifest.get("licensing")
    redistribution = manifest.get("redistribution")
    if type(licensing) is not dict or type(redistribution) is not dict:
        raise InventoryError("manifest licensing/redistribution must be objects")
    status = licensing.get("status")
    commercial = licensing.get("commercial_use_status")
    redistribution_status = redistribution.get("status")
    if not all(type(value) is str and value for value in (status, commercial, redistribution_status)):
        raise InventoryError("manifest rights fields must be non-empty strings")

    flags = set(result["license_or_terms_flags"])
    if commercial in {"restricted", "prohibited"}:
        flags.add(f"commercial_use_{commercial}")
    if redistribution_status in {"restricted", "prohibited"}:
        flags.add(f"redistribution_{redistribution_status}")

    if status == "verified" and commercial == "allowed" and redistribution_status == "allowed":
        result["rights_posture"] = "source_rights_verified"
    elif status == "verified":
        result["rights_posture"] = "known_restriction_requires_review"
    else:
        result["rights_posture"] = "license_review_required"
    result["license_or_terms_flags"] = sorted(flags)
    if result["rights_posture"] != "source_rights_verified":
        result["automation_decision"] = "document_only"
    return result


def build_inventory() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    seen_landscape: set[str] = set()
    seen_manifests: set[str] = set()
    known_source_ids: set[str] = set()
    review_dates: list[str] = []
    contracts_by_source, contract_paths = _contract_index()
    landscape_paths: list[str] = []
    manifest_paths: list[str] = []

    for path in landscape_files():
        payload = load_json(path)
        if type(payload) is not dict or type(payload.get("entries")) is not list:
            raise InventoryError(f"{path.relative_to(ROOT)} is not a source-landscape object")
        review_date = payload.get("review_date")
        if type(review_date) is not str:
            raise InventoryError(f"{path.relative_to(ROOT)} lacks review_date")
        review_dates.append(review_date)
        relative = path.relative_to(ROOT).as_posix()
        landscape_paths.append(relative)
        for index, source in enumerate(payload["entries"]):
            if type(source) is not dict:
                raise InventoryError(f"{relative}: entries[{index}] must be an object")
            source_id = source.get("candidate_id")
            if type(source_id) is not str or not source_id:
                raise InventoryError(f"{relative}: entries[{index}] lacks candidate_id")
            if source_id in seen_landscape:
                raise InventoryError(f"duplicate source candidate_id across landscapes: {source_id}")
            seen_landscape.add(source_id)
            known_source_ids.add(source_id)
            provider = source.get("provider")
            authoritative_url = source.get("authoritative_url")
            hint = source.get("access_class_hint")
            categories = source.get("categories")
            note = source.get("note")
            rights_review = source.get("rights_review_status")
            if not all(type(value) is str and value for value in (provider, authoritative_url, hint, note, rights_review)):
                raise InventoryError(f"{relative}: {source_id} lacks required access inventory inputs")
            if type(categories) is not list or not all(type(value) is str and value for value in categories):
                raise InventoryError(f"{relative}: {source_id} categories must be non-empty strings")
            if rights_review != "not_reviewed":
                raise InventoryError(
                    f"{relative}: {source_id} rights state {rights_review!r} requires an explicit inventory policy update"
                )
            classification = classify_access(hint, categories, note)
            # Landscape discovery is explicitly non-admission and rights are not
            # reviewed. Preserve any known restriction signal discovered in the
            # canonical note/hint, but never let that row become executable.
            classification["automation_decision"] = "document_only"
            classification = _apply_contracts(
                classification,
                contracts_by_source.get(source_id, []),
                allow_contract_promotion=False,
            )
            entries.append({
                "record_type": "landscape_candidate",
                "source_id": source_id,
                "source_registry_path": relative,
                "provider": provider,
                "authoritative_url": authoritative_url,
                "access_class_hint": hint,
                **classification,
            })

    for path in manifest_files():
        manifest = load_json(path)
        if type(manifest) is not dict:
            raise InventoryError(f"{path.relative_to(ROOT)} must contain a manifest object")
        source_id = manifest.get("dataset_id")
        provider = manifest.get("provider")
        authoritative_url = manifest.get("canonical_source")
        access_class = manifest.get("access_class")
        modelling_layer = manifest.get("modelling_layer")
        intended_use = manifest.get("intended_use")
        if not all(type(value) is str and value for value in (source_id, provider, authoritative_url, access_class, modelling_layer, intended_use)):
            raise InventoryError(f"{path.relative_to(ROOT)} lacks required manifest inventory inputs")
        if source_id in seen_manifests:
            raise InventoryError(f"duplicate admitted manifest dataset_id: {source_id}")
        seen_manifests.add(source_id)
        known_source_ids.add(source_id)
        review = manifest.get("review")
        licensing = manifest.get("licensing")
        note_parts = [intended_use]
        if type(review) is dict and type(review.get("notes")) is str:
            note_parts.append(review["notes"])
        if type(licensing) is dict and type(licensing.get("notes")) is str:
            note_parts.append(licensing["notes"])
        classification = classify_access(access_class, [modelling_layer], " ".join(note_parts))
        classification = _manifest_rights(manifest, classification)
        contracts = contracts_by_source.get(source_id, [])
        # Dataset/source rights alone never clear a separate provider API/service
        # boundary. A heuristic API hint with no validated access contract may be
        # a build candidate, but cannot become an executable adapter-now decision.
        if not contracts and classification["automation_decision"] == "build_adapter_now":
            classification["automation_decision"] = "build_later"
            classification["next_action"] = (
                "Add and validate an exact source-access contract with reviewed API/service terms before adapter execution."
            )
        classification = _apply_contracts(
            classification,
            contracts,
            allow_contract_promotion=classification["rights_posture"] == "source_rights_verified",
        )
        relative = path.relative_to(ROOT).as_posix()
        manifest_paths.append(relative)
        entries.append({
            "record_type": "admitted_manifest",
            "source_id": source_id,
            "source_registry_path": relative,
            "provider": provider,
            "authoritative_url": authoritative_url,
            "access_class_hint": access_class,
            **classification,
        })

    dangling_sources = sorted(set(contracts_by_source) - known_source_ids)
    if dangling_sources:
        raise InventoryError(f"source-access contracts reference unknown source_ids: {dangling_sources}")

    entries.sort(key=lambda item: (item["source_id"], item["record_type"], item["source_registry_path"]))
    landscape_count = sum(1 for entry in entries if entry["record_type"] == "landscape_candidate")
    manifest_count = sum(1 for entry in entries if entry["record_type"] == "admitted_manifest")
    return {
        "schema_version": "1.0.0",
        "purpose": "Deterministic fail-closed first-pass machine-access and licensing work queue for every current source-landscape candidate and admitted dataset manifest. This inventory is not API verification, rights approval, scientific approval or data admission.",
        "source_review_date_max": max(review_dates),
        "landscape_files": landscape_paths,
        "manifest_files": manifest_paths,
        "access_contract_files": contract_paths,
        "landscape_entry_count": landscape_count,
        "manifest_entry_count": manifest_count,
        "entry_count": len(entries),
        "entries": entries,
    }


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic source-access inventory.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help=f"write {DEFAULT_OUTPUT.relative_to(ROOT)}")
    group.add_argument("--check", action="store_true", help="require checked-in inventory to equal deterministic output")
    args = parser.parse_args(argv)
    try:
        inventory = build_inventory()
        expected = canonical_bytes(inventory)
        if args.write:
            DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            DEFAULT_OUTPUT.write_bytes(expected)
            print(f"WROTE {DEFAULT_OUTPUT.relative_to(ROOT)} ({inventory['entry_count']} records)")
            return 0
        if args.check:
            actual = DEFAULT_OUTPUT.read_bytes()
            if actual != expected:
                print(
                    "FAIL: source-access inventory is stale; run python scripts/build_source_access_inventory.py --write",
                    file=sys.stderr,
                )
                return 1
            print(f"PASS: {DEFAULT_OUTPUT.relative_to(ROOT)} covers {inventory['entry_count']} records")
            return 0
        sys.stdout.buffer.write(expected)
        return 0
    except (OSError, InventoryError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
