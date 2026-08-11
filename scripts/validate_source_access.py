# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed validation for OpenCatastrophe source-access contracts."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

try:
    from scripts.source_access_path import PercentDecodeError, stable_percent_decode
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from source_access_path import PercentDecodeError, stable_percent_decode

ROOT = Path(__file__).resolve().parents[1]

TOP_LEVEL_KEYS = {
    "schema_version",
    "access_id",
    "source_ids",
    "provider",
    "interface_type",
    "status",
    "documentation_url",
    "service_root",
    "api_version",
    "access_scope",
    "authentication",
    "request_contract",
    "response_contract",
    "operational_constraints",
    "rights_and_policy",
    "probe_contract",
    "implementation_decision",
    "reviewed_at",
    "evidence_urls",
    "notes",
}
INTERFACE_TYPES = {
    "rest", "fdsn", "ogc_api", "stac", "wms", "wfs", "wcs", "arcgis_rest",
    "mqtt_http", "object_store", "http_file", "ftp_or_ftps", "provider_sdk",
    "web_portal", "other_documented_machine_interface",
}
STATUSES = {
    "documented_only", "probe_ready", "verified_anonymous", "verified_authenticated",
    "blocked_registration", "blocked_credentials", "restricted_by_terms", "deprecated", "rejected",
}
NONEXECUTABLE_STATUSES = {
    "documented_only", "blocked_registration", "blocked_credentials",
    "restricted_by_terms", "deprecated", "rejected",
}
AUTH_MODES = {"none", "api_key", "bearer_token", "basic", "oauth2", "provider_account", "signed_request", "other"}
CREDENTIAL_AUTH_MODES = {"api_key", "bearer_token", "basic", "oauth2", "signed_request"}
ACCESS_SCOPES = {"metadata", "catalogue", "sample", "bulk", "realtime", "other"}
IMPLEMENTATION_DECISIONS = {"build_adapter_now", "document_only", "build_later", "do_not_automate"}
DATASET_RIGHTS = {"verified", "not_reviewed", "conflicting", "restricted", "prohibited", "unknown"}
API_TERMS = {"same_as_dataset", "separate_reviewed", "separate_unreviewed", "unknown"}
RIGHTS_DECISIONS = {"allowed", "restricted", "prohibited", "unknown"}
PROBE_MODES = {"none", "metadata_get", "head", "catalogue_query", "provider_specific"}
RETRY_POLICIES = {"none", "bounded_backoff"}
ID_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
OP_RE = re.compile(r"^[a-z][a-z0-9_]*$")
MEDIA_RE = re.compile(r"^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$")
NUMERIC_HOST_PART_RE = re.compile(r"^(?:0[xX][0-9A-Fa-f]+|[0-9]+)$")
SECRET_LIKE = re.compile(r"(?i)(bearer\s+[A-Za-z0-9._-]{12,}|api[_-]?key\s*[:=]\s*\S+|password\s*[:=]\s*\S+|secret\s*[:=]\s*\S+)")
SECRET_QUERY_KEY = re.compile(
    r"(?i)^(?:access[_-]?token|api[_-]?key|token|password|passwd|secret|signature|sig|credential|auth(?:orization)?)$"
)


class SourceAccessError(ValueError):
    """Raised when a source-access contract violates the fail-closed policy."""


def _reject_constant(value: str) -> None:
    raise SourceAccessError(f"non-finite JSON number is forbidden: {value}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SourceAccessError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_strict_json_bytes(raw: bytes) -> Any:
    if type(raw) is not bytes or not raw:
        raise SourceAccessError("contract must be non-empty bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceAccessError("contract must be valid UTF-8") from exc
    try:
        return json.loads(text, object_pairs_hook=_strict_object, parse_constant=_reject_constant)
    except SourceAccessError:
        raise
    except json.JSONDecodeError as exc:
        raise SourceAccessError(f"invalid JSON: {exc}") from exc


def _exact_keys(value: Any, expected: set[str], where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise SourceAccessError(f"{where} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise SourceAccessError(f"{where} keys mismatch; missing={missing}, unexpected={unexpected}")
    return value


def _text(value: Any, where: str) -> str:
    if type(value) is not str or not value.strip():
        raise SourceAccessError(f"{where} must be non-blank text")
    if SECRET_LIKE.search(value):
        raise SourceAccessError(f"{where} appears to contain secret material")
    return value


def _enum(value: Any, allowed: set[str], where: str) -> str:
    text = _text(value, where)
    if text not in allowed:
        raise SourceAccessError(f"{where} has unsupported value {text!r}")
    return text


def _ambiguous_numeric_host(host: str) -> bool:
    """Reject legacy numeric IPv4 spellings before socket resolution can reinterpret them."""

    if ":" in host:
        return False
    parts = host.split(".")
    if not parts or not all(NUMERIC_HOST_PART_RE.fullmatch(part) for part in parts):
        return False
    if len(parts) != 4:
        return True
    for part in parts:
        if part.lower().startswith("0x"):
            return True
        if len(part) > 1 and part.startswith("0"):
            return True
        try:
            value = int(part, 10)
        except ValueError:
            return True
        if not 0 <= value <= 255:
            return True
    return False


def _https_url(value: Any, where: str, *, nullable: bool = False, root: bool = False) -> str | None:
    if value is None and nullable:
        return None
    text = _text(value, where)
    if any(char.isspace() for char in text):
        raise SourceAccessError(f"{where} must not contain whitespace")
    parsed = urlsplit(text)
    try:
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError as exc:
        raise SourceAccessError(f"{where} has an invalid host or port") from exc
    if parsed.scheme != "https" or not parsed.netloc or not hostname or parsed.username or parsed.password:
        raise SourceAccessError(f"{where} must be a public https URL without embedded credentials")

    host = hostname.rstrip(".").casefold()
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise SourceAccessError(f"{where} must not target a local host")
    if _ambiguous_numeric_host(host):
        raise SourceAccessError(f"{where} must not use an ambiguous numeric host")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise SourceAccessError(f"{where} must not target a non-public IP address")

    for key, query_value in parse_qsl(parsed.query, keep_blank_values=True):
        folded = key.casefold()
        if SECRET_QUERY_KEY.fullmatch(key) or folded.startswith("x-amz-") or folded.startswith("x-goog-"):
            raise SourceAccessError(f"{where} must not contain token/signature query parameters")
        if SECRET_LIKE.search(query_value):
            raise SourceAccessError(f"{where} query appears to contain secret material")
    if root and (parsed.query or parsed.fragment):
        raise SourceAccessError(f"{where} service root must not contain query or fragment")
    return text


def _unique_text_list(value: Any, where: str, *, allowed: set[str] | None = None, pattern: re.Pattern[str] | None = None) -> list[str]:
    if type(value) is not list or not value:
        raise SourceAccessError(f"{where} must be a non-empty array")
    result: list[str] = []
    for index, item in enumerate(value):
        text = _text(item, f"{where}[{index}]")
        if allowed is not None and text not in allowed:
            raise SourceAccessError(f"{where}[{index}] has unsupported value {text!r}")
        if pattern is not None and not pattern.fullmatch(text):
            raise SourceAccessError(f"{where}[{index}] has invalid format")
        result.append(text)
    if len(result) != len(set(result)):
        raise SourceAccessError(f"{where} must not contain duplicates")
    return result


def _integer(value: Any, where: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise SourceAccessError(f"{where} must be an integer in [{minimum}, {maximum}]")
    return value


def validate_contract(contract: Any) -> dict[str, Any]:
    obj = _exact_keys(contract, TOP_LEVEL_KEYS, "contract")
    if obj["schema_version"] != "1.0.0":
        raise SourceAccessError("schema_version must equal '1.0.0'")
    access_id = _text(obj["access_id"], "access_id")
    if not ID_RE.fullmatch(access_id):
        raise SourceAccessError("access_id has invalid format")
    _unique_text_list(obj["source_ids"], "source_ids", pattern=SOURCE_ID_RE)
    _text(obj["provider"], "provider")
    _enum(obj["interface_type"], INTERFACE_TYPES, "interface_type")
    status = _enum(obj["status"], STATUSES, "status")
    _https_url(obj["documentation_url"], "documentation_url")
    _https_url(obj["service_root"], "service_root", nullable=True, root=True)
    if obj["api_version"] is not None:
        _text(obj["api_version"], "api_version")
    _unique_text_list(obj["access_scope"], "access_scope", allowed=ACCESS_SCOPES)

    auth = _exact_keys(obj["authentication"], {"mode", "credential_reference", "registration_url", "secret_in_repository"}, "authentication")
    auth_mode = _enum(auth["mode"], AUTH_MODES, "authentication.mode")
    if type(auth["secret_in_repository"]) is not bool or auth["secret_in_repository"] is not False:
        raise SourceAccessError("authentication.secret_in_repository must be exactly false")
    credential = auth["credential_reference"]
    if credential is not None:
        if type(credential) is not str or not ENV_RE.fullmatch(credential):
            raise SourceAccessError("authentication.credential_reference must be a symbolic environment/secret name")
    _https_url(auth["registration_url"], "authentication.registration_url", nullable=True)
    if auth_mode == "none" and credential is not None:
        raise SourceAccessError("anonymous access must not declare a credential reference")
    if auth_mode in CREDENTIAL_AUTH_MODES and credential is None:
        raise SourceAccessError("credential-bearing authentication must declare a symbolic credential reference")

    request = _exact_keys(obj["request_contract"], {"allowed_operations", "path_templates", "parameter_rules"}, "request_contract")
    operations = _unique_text_list(request["allowed_operations"], "request_contract.allowed_operations", pattern=OP_RE)
    paths = _unique_text_list(request["path_templates"], "request_contract.path_templates")
    for path in paths:
        try:
            decoded = stable_percent_decode(path)
        except PercentDecodeError as exc:
            raise SourceAccessError("request path templates must have bounded percent-encoding") from exc
        if (
            not path.startswith("/")
            or path.startswith("//")
            or "\\" in path
            or "\\" in decoded
            or decoded.startswith("//")
            or any(part in {".", ".."} for part in decoded.split("/"))
        ):
            raise SourceAccessError("request path templates must be relative-to-service-root absolute paths without traversal")
        if any(marker in path or marker in decoded for marker in ("://", "?", "#")):
            raise SourceAccessError("request path templates must not contain a URL, query or fragment")
    _text(request["parameter_rules"], "request_contract.parameter_rules")

    response = _exact_keys(obj["response_contract"], {"expected_media_types", "format", "scientific_semantics"}, "response_contract")
    _unique_text_list(response["expected_media_types"], "response_contract.expected_media_types", pattern=MEDIA_RE)
    _text(response["format"], "response_contract.format")
    _text(response["scientific_semantics"], "response_contract.scientific_semantics")

    limits = _exact_keys(obj["operational_constraints"], {"timeout_seconds", "max_probe_bytes", "max_sample_bytes", "retry_policy", "rate_limit_notes", "mutability_notes"}, "operational_constraints")
    _integer(limits["timeout_seconds"], "operational_constraints.timeout_seconds", 1, 120)
    probe_bytes = _integer(limits["max_probe_bytes"], "operational_constraints.max_probe_bytes", 1, 5 * 1024 * 1024)
    sample_bytes = _integer(limits["max_sample_bytes"], "operational_constraints.max_sample_bytes", 1, 50 * 1024 * 1024)
    if sample_bytes < probe_bytes:
        raise SourceAccessError("max_sample_bytes must be >= max_probe_bytes")
    _enum(limits["retry_policy"], RETRY_POLICIES, "operational_constraints.retry_policy")
    _text(limits["rate_limit_notes"], "operational_constraints.rate_limit_notes")
    _text(limits["mutability_notes"], "operational_constraints.mutability_notes")

    rights = _exact_keys(obj["rights_and_policy"], {"dataset_rights_status", "api_terms_status", "terms_url", "commercial_automation_status", "redistribution_status", "notes"}, "rights_and_policy")
    dataset_rights = _enum(rights["dataset_rights_status"], DATASET_RIGHTS, "rights_and_policy.dataset_rights_status")
    api_terms = _enum(rights["api_terms_status"], API_TERMS, "rights_and_policy.api_terms_status")
    terms_url = _https_url(rights["terms_url"], "rights_and_policy.terms_url", nullable=True)
    if api_terms == "separate_reviewed" and terms_url is None:
        raise SourceAccessError("separate_reviewed API terms require an authoritative terms_url")
    commercial = _enum(rights["commercial_automation_status"], RIGHTS_DECISIONS, "rights_and_policy.commercial_automation_status")
    redistribution = _enum(rights["redistribution_status"], RIGHTS_DECISIONS, "rights_and_policy.redistribution_status")
    _text(rights["notes"], "rights_and_policy.notes")
    if dataset_rights != "verified" and (commercial == "allowed" or redistribution == "allowed"):
        raise SourceAccessError("non-verified dataset rights cannot claim allowed commercial automation or redistribution")

    probe = _exact_keys(obj["probe_contract"], {"mode", "operation", "requires_credentials", "expected_evidence"}, "probe_contract")
    probe_mode = _enum(probe["mode"], PROBE_MODES, "probe_contract.mode")
    operation = probe["operation"]
    if operation is not None:
        if type(operation) is not str or operation not in operations:
            raise SourceAccessError("probe_contract.operation must name an allowed operation")
    if type(probe["requires_credentials"]) is not bool:
        raise SourceAccessError("probe_contract.requires_credentials must be boolean")
    if probe_mode == "none" and operation is not None:
        raise SourceAccessError("probe mode none must not name an operation")
    if probe_mode != "none" and operation is None:
        raise SourceAccessError("active probe mode must name an operation")
    if probe["requires_credentials"] != (auth_mode != "none"):
        raise SourceAccessError("probe credential requirement must match authentication mode")
    evidence = probe["expected_evidence"]
    if type(evidence) is not list:
        raise SourceAccessError("probe_contract.expected_evidence must be an array")
    for index, item in enumerate(evidence):
        _text(item, f"probe_contract.expected_evidence[{index}]")
    active_probe = probe_mode != "none"
    if active_probe and not evidence:
        raise SourceAccessError("active probe mode requires non-empty expected evidence")

    implementation = _enum(obj["implementation_decision"], IMPLEMENTATION_DECISIONS, "implementation_decision")

    # Verification status is evidence, not decoration. A documentation/blocked
    # state cannot carry an active probe, and verified states require the probe
    # shape that justifies their claim.
    if status in NONEXECUTABLE_STATUSES:
        if active_probe:
            raise SourceAccessError(f"status {status!r} requires probe mode none")
        if implementation not in {"document_only", "do_not_automate"}:
            raise SourceAccessError(f"status {status!r} requires a non-executable implementation decision")
    elif status == "probe_ready":
        if not active_probe:
            raise SourceAccessError("probe_ready status requires an active bounded probe")
    elif status == "verified_anonymous":
        if auth_mode != "none":
            raise SourceAccessError("verified_anonymous requires anonymous authentication mode")
        if not active_probe or not evidence:
            raise SourceAccessError("verified_anonymous requires an active probe with expected evidence")
    elif status == "verified_authenticated":
        if auth_mode == "none":
            raise SourceAccessError("verified_authenticated requires authenticated access")
        if not active_probe or not evidence:
            raise SourceAccessError("verified_authenticated requires an active probe with expected evidence")

    api_terms_cleared = api_terms in {"same_as_dataset", "separate_reviewed"}
    automation_rights_clear = dataset_rights == "verified" and api_terms_cleared and commercial == "allowed"
    if not automation_rights_clear:
        if active_probe:
            raise SourceAccessError("active probes require verified dataset rights, reviewed API terms and allowed commercial automation")
        if implementation not in {"document_only", "do_not_automate"}:
            raise SourceAccessError("uncleared rights/API terms require a documentation-only implementation decision")
    if implementation == "build_adapter_now" and not automation_rights_clear:
        raise SourceAccessError("build_adapter_now requires fully cleared automation rights")
    if implementation == "do_not_automate" and active_probe:
        raise SourceAccessError("do_not_automate must not declare an active probe")

    reviewed = _text(obj["reviewed_at"], "reviewed_at")
    try:
        date.fromisoformat(reviewed)
    except ValueError as exc:
        raise SourceAccessError("reviewed_at must be a real ISO calendar date") from exc
    evidence_urls = obj["evidence_urls"]
    if type(evidence_urls) is not list or not evidence_urls:
        raise SourceAccessError("evidence_urls must be a non-empty array")
    seen_urls: set[str] = set()
    for index, url in enumerate(evidence_urls):
        normalized = _https_url(url, f"evidence_urls[{index}]")
        assert normalized is not None
        if normalized in seen_urls:
            raise SourceAccessError("evidence_urls must not contain duplicates")
        seen_urls.add(normalized)
    _text(obj["notes"], "notes")
    return obj


def validate_path(path: Path) -> dict[str, Any]:
    return validate_contract(load_strict_json_bytes(path.read_bytes()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate OpenCatastrophe source-access contract JSON.")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    for path in args.paths:
        try:
            validate_path(path)
        except (OSError, SourceAccessError) as exc:
            print(f"FAIL {path}: {exc}", file=sys.stderr)
            return 1
        print(f"PASS {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
