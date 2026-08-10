# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Build a deterministic first-pass access inventory for every source-landscape entry.

The inventory is deliberately conservative. It translates the already reviewed
``access_class_hint`` and source note into machine-access and rights work queues;
it does not invent provider API facts or upgrade source rights. Concrete live
interfaces belong in reviewed ``access/*.json`` source-access contracts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LANDSCAPE_DIR = ROOT / "landscape"
DEFAULT_OUTPUT = ROOT / "access" / "source-access-inventory.json"


class InventoryError(ValueError):
    """Raised when canonical source discovery cannot be inventoried safely."""


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


def classify_access(hint: str, categories: list[str], note: str) -> dict[str, Any]:
    evidence = " ".join([hint, *categories, note]).casefold()

    api_like = _contains(hint, "api") or "api" in {value.casefold() for value in categories}
    geospatial = _contains(hint, "stac", "wms", "wfs", "wcs", "arcgis", "web_services", "geospatial_service")
    federated = _contains(hint, "mqtt", "federated", "data_exchange")
    downloadable = _contains(hint, "download", "object", "cloud", "geoparquet", "repository", "ftp", "file", "bulk")
    service = _contains(hint, "service", "portal", "catalog")
    provider_gate = _contains(hint, "registration", "registered", "account", "token", "eu_login")
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
        "registration_or_account_gate": ("registration", "registered", "account", "token", "eu login", "eu_login"),
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
        next_action = "Verify exact service protocol/endpoints and terms; model it as a non-generic provider contract rather than forcing REST semantics."
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


def source_files() -> list[Path]:
    paths = sorted(LANDSCAPE_DIR.glob("sources*.json"))
    if not paths:
        raise InventoryError("no canonical landscape/sources*.json files found")
    return paths


def build_inventory() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    files: list[str] = []
    review_dates: list[str] = []

    for path in source_files():
        payload = load_json(path)
        if type(payload) is not dict or type(payload.get("entries")) is not list:
            raise InventoryError(f"{path.relative_to(ROOT)} is not a source-landscape object")
        review_date = payload.get("review_date")
        if type(review_date) is not str:
            raise InventoryError(f"{path.relative_to(ROOT)} lacks review_date")
        review_dates.append(review_date)
        relative = path.relative_to(ROOT).as_posix()
        files.append(relative)
        for index, source in enumerate(payload["entries"]):
            if type(source) is not dict:
                raise InventoryError(f"{relative}: entries[{index}] must be an object")
            source_id = source.get("candidate_id")
            if type(source_id) is not str or not source_id:
                raise InventoryError(f"{relative}: entries[{index}] lacks candidate_id")
            if source_id in seen:
                raise InventoryError(f"duplicate source candidate_id across landscapes: {source_id}")
            seen.add(source_id)
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
            classification = classify_access(hint, categories, note)
            if rights_review != "not_reviewed":
                raise InventoryError(
                    f"{relative}: {source_id} rights state {rights_review!r} requires an explicit inventory policy update"
                )
            entries.append({
                "source_id": source_id,
                "source_registry_path": relative,
                "provider": provider,
                "authoritative_url": authoritative_url,
                "access_class_hint": hint,
                **classification,
            })

    entries.sort(key=lambda item: item["source_id"])
    return {
        "schema_version": "1.0.0",
        "purpose": "Deterministic fail-closed first-pass machine-access and licensing work queue for every current source-landscape candidate. This inventory is not an API verification, rights approval, scientific approval or data admission.",
        "source_review_date_max": max(review_dates),
        "source_files": files,
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
        expected = canonical_bytes(build_inventory())
        if args.write:
            DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            DEFAULT_OUTPUT.write_bytes(expected)
            print(f"WROTE {DEFAULT_OUTPUT.relative_to(ROOT)}")
            return 0
        if args.check:
            actual = DEFAULT_OUTPUT.read_bytes()
            if actual != expected:
                print(
                    "FAIL: source-access inventory is stale; run python scripts/build_source_access_inventory.py --write",
                    file=sys.stderr,
                )
                return 1
            print(f"PASS: {DEFAULT_OUTPUT.relative_to(ROOT)} covers {build_inventory()['entry_count']} source candidates")
            return 0
        sys.stdout.buffer.write(expected)
        return 0
    except (OSError, InventoryError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
