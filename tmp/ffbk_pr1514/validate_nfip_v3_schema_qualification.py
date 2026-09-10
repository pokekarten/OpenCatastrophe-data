#!/usr/bin/env python3
"""Fail-closed validator for NFIP v3 metadata-only qualification receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

V0 = "nfip-v3-registry-qualification-v0"
V1 = "nfip-v3-registry-qualification-v1"
V2 = "nfip-v3-registry-qualification-v2"
ALLOWED_VERSIONS = {V0, V1, V2}

EXPECTED_DATASET = {
    "name": "NfipClaims",
    "version": 3,
    "webService": "https://www.fema.gov/api/open/v3/NfipClaims",
    "dataDictionary": "https://www.fema.gov/openfema-data-page/nfip-redacted-claims-v3",
    "accrualPeriodicity": "R/P1M",
    "hash": "9eaf194937eba43e6df9f1809f311d2c63058c81",
    "id": "38707079-3400-4c56-bb50-3282881e21be",
    "recordCount": 2724656,
}
EXPECTED_METADATA_ENDPOINT = "https://www.fema.gov/api/open/v1/OpenFemaDataSetFields"
EXPECTED_METADATA_FILTER = "openFemaDataSet eq 'NfipClaims' and datasetVersion eq 3"
EXPECTED_METADATA_RECORD_COUNT = 84
EXPECTED_V1_RAW_RESPONSE_SHA256 = "b3001238876d7b8a6232c270fe5dd0c02fa7ccd5e0c0290ed7b0151f72f2fcc9"
EXPECTED_V2_SEMANTIC_SHA256 = "99cb4eb2eb432a83dc52a48a802776308f3811210373bd559f6adaa776db8528"
SEMANTIC_RECORD_KEYS = (
    "datasetId", "openFemaDataSet", "datasetVersion", "name", "title",
    "description", "type", "sortOrder", "isSearchable", "isNestedObject",
    "isNullable", "primaryKey", "id", "hash", "srid",
)
REQUIRED_QUALIFIED_FIELDS = {
    "id", "asOfDate", "dateOfLoss", "yearOfLoss",
    "amountPaidOnBuildingClaim", "amountPaidOnContentsClaim",
    "amountPaidOnIncreasedCostOfComplianceClaim",
    "totalBuildingInsuranceCoverage", "totalContentsInsuranceCoverage",
    "buildingDamageAmount", "contentsDamageAmount",
    "buildingPropertyValue", "contentsPropertyValue",
    "netBuildingPaymentAmount", "netContentsPaymentAmount",
    "buildingDeductibleCode", "contentsDeductibleCode",
    "openDate", "mostRecentPaymentDate", "mostRecentRecoveryDate", "iccCoverage",
}
CORE_FIELD_IDENTITIES = {
    "id": ("ab68526efca22eb37d9921744de7abbdd16c3de1", "bigint", True),
    "asOfDate": ("546604ede998914f7a41b58d9b1cfe33faacde47", "datetime", False),
    "dateOfLoss": ("7136bab1db08037fe424af65f786fad374261fae", "datetime", False),
    "yearOfLoss": ("c4124b641804115e594e4f9804a03b880ddd54a2", "smallint", False),
    "amountPaidOnBuildingClaim": ("1e6a109c301892e9c741e9b6719d81a6e0a4ee31", "decimal(12,2)", False),
    "totalBuildingInsuranceCoverage": ("6a54273419037614e0d2735397a003160627c427", "integer", False),
    "buildingDamageAmount": ("0d681ea7fa6c62a97da0c6529db7dee37b6f0684", "integer", False),
    "netBuildingPaymentAmount": ("55b35795cfd35adc552b152ad7dd7aff915de5ab", "decimal(12,2)", False),
    "openDate": ("7f4644ced8401e3ad6e77a56e798bdd2b7d533b5", "date", False),
    "mostRecentPaymentDate": ("211a7be1ac6cac112b9d571d79a596764ecb5534", "date", False),
}


class QualificationError(RuntimeError):
    pass


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode()


def load(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise QualificationError("receipt must be object")
    return obj


def semantic_field_records(document):
    if not isinstance(document, dict):
        raise QualificationError("metadata response must be object")
    records = document.get("OpenFemaDataSetFields")
    if not isinstance(records, list):
        raise QualificationError("OpenFemaDataSetFields must be list")
    if len(records) != EXPECTED_METADATA_RECORD_COUNT:
        raise QualificationError("authoritative metadata record count mismatch")

    names = []
    normalized = []
    for record in records:
        if not isinstance(record, dict):
            raise QualificationError("metadata field record must be object")
        name = record.get("name")
        if not isinstance(name, str) or not name:
            raise QualificationError("metadata field name missing")
        names.append(name)
        normalized.append({key: record.get(key) for key in SEMANTIC_RECORD_KEYS})

    if len(set(names)) != len(names):
        raise QualificationError("metadata field names must be unique")

    normalized.sort(key=lambda record: record["name"])
    return normalized


def semantic_metadata_sha256(document):
    return hashlib.sha256(canonical(semantic_field_records(document))).hexdigest()


def verify_live_metadata(document, receipt):
    status = validate(receipt)
    if receipt.get("receipt_version") != V2:
        raise QualificationError("live metadata verification requires v2 receipt")
    observed = semantic_metadata_sha256(document)
    expected = receipt["field_semantics"]["metadata_semantic_sha256"]
    if observed != expected:
        raise QualificationError(
            f"authoritative metadata semantic hash mismatch: {observed}"
        )
    return {
        "status": status,
        "metadata_record_count": EXPECTED_METADATA_RECORD_COUNT,
        "metadata_semantic_sha256": observed,
    }


def _validate_registry(reg, dec):
    dataset = reg.get("dataset", {})
    predecessor = reg.get("predecessor", {})
    for key, value in EXPECTED_DATASET.items():
        if dataset.get(key) != value:
            raise QualificationError(f"v3 registry mismatch: {key}")
    if predecessor.get("name") != "FimaNfipClaims" or predecessor.get("version") != 2:
        raise QualificationError("v2 predecessor mismatch")
    if predecessor.get("depDate") != "2026-10-15T00:00:00.000Z":
        raise QualificationError("v2 deprecation mismatch")
    if predecessor.get("data_frozen_as_of") != "2026-06-01":
        raise QualificationError("v2 freeze mismatch")
    if dec.get("v2_v3_naive_vintage_stitching") != "FORBIDDEN":
        raise QualificationError("v2/v3 stitching must be forbidden")
    if dec.get("future_target_access") != "FORBIDDEN":
        raise QualificationError("future target must remain forbidden")
    if dec.get("severity_family_promotion") not in (None, "FORBIDDEN"):
        raise QualificationError("severity-family promotion must remain forbidden")


def _validate_v0(fs, dec):
    qualified = fs.get("authoritative_fields_qualified")
    if not isinstance(qualified, list):
        raise QualificationError("authoritative_fields_qualified must be list")
    if fs.get("materialization_status") == "AUTHORITATIVE_FIELD_SEMANTICS_CONFIRMED":
        raise QualificationError("v0 receipt cannot claim confirmed field semantics")
    if qualified:
        raise QualificationError("unmaterialized dictionary cannot qualify fields")
    if dec.get("historical_snapshot_contract") != "NOT_YET_ADMISSIBLE":
        raise QualificationError("historical contract must remain blocked")
    if fs.get("promotion_status") != "BLOCKED":
        raise QualificationError("promotion must remain blocked")
    return "REGISTRY_CONFIRMED_FIELD_SEMANTICS_BLOCKED"


def _validate_authoritative_common(fs, dec):
    if fs.get("materialization_status") != "AUTHORITATIVE_FIELD_SEMANTICS_CONFIRMED":
        raise QualificationError("authoritative metadata must be confirmed")
    if fs.get("authoritative_metadata_endpoint") != EXPECTED_METADATA_ENDPOINT:
        raise QualificationError("authoritative metadata endpoint mismatch")
    if fs.get("authoritative_metadata_filter") != EXPECTED_METADATA_FILTER:
        raise QualificationError("authoritative metadata filter mismatch")
    if fs.get("metadata_record_count") != EXPECTED_METADATA_RECORD_COUNT:
        raise QualificationError("authoritative metadata record count mismatch")

    qualified = fs.get("authoritative_fields_qualified")
    if not isinstance(qualified, list):
        raise QualificationError("authoritative_fields_qualified must be list")
    qualified_set = set(map(str, qualified))
    if not REQUIRED_QUALIFIED_FIELDS.issubset(qualified_set):
        raise QualificationError("authoritative field qualification incomplete")

    econ = fs.get("economic_classification", {})
    if (
        econ.get("identity_and_vintage", {}).get("finality")
        != "NOT_IDENTIFIED_NO_CLOSE_DATE_FIELD_IN_84_FIELD_METADATA"
    ):
        raise QualificationError("claim finality must remain unproven")
    if (
        econ.get("covered_payment", {}).get("amountPaidOnBuildingClaim")
        != "COVERED_PAYMENT_NOT_GROUND_UP"
    ):
        raise QualificationError("paid-building semantic boundary weakened")
    if (
        econ.get("damage_candidate", {}).get("buildingDamageAmount")
        != "ACTUAL_CASH_VALUE_DAMAGE_AMOUNT_CANDIDATE_NOT_YET_PROSPECTIVE_TARGET"
    ):
        raise QualificationError("damage candidate promoted beyond evidence")
    if fs.get("promotion_status") != "FIELD_METADATA_ONLY_NO_MODEL_PROMOTION":
        raise QualificationError("model promotion must remain forbidden")
    if dec.get("historical_snapshot_contract") != "ADMISSIBLE_FOR_VINTAGE_DRIFT_ONLY":
        raise QualificationError("qualified receipt must remain vintage-drift-only")
    if (
        dec.get("prospective_target_status")
        != "NOT_YET_ADMISSIBLE_MATURITY_AND_TARGET_PROTOCOL_OPEN"
    ):
        raise QualificationError("prospective target must remain blocked")
    return qualified_set


def _validate_v1(fs, dec):
    _validate_authoritative_common(fs, dec)
    if fs.get("metadata_response_sha256") != EXPECTED_V1_RAW_RESPONSE_SHA256:
        raise QualificationError("authoritative metadata response hash mismatch")

    records = fs.get("qualified_field_records")
    if not isinstance(records, list):
        raise QualificationError("qualified_field_records must be list")
    by_name = {record.get("name"): record for record in records if isinstance(record, dict)}
    if not REQUIRED_QUALIFIED_FIELDS.issubset(by_name):
        raise QualificationError("qualified field record missing")
    for name, (field_hash, field_type, primary_key) in CORE_FIELD_IDENTITIES.items():
        record = by_name.get(name, {})
        if (
            record.get("hash") != field_hash
            or record.get("type") != field_type
            or record.get("primaryKey") is not primary_key
        ):
            raise QualificationError(f"authoritative field identity mismatch: {name}")
    return "FIELD_SEMANTICS_CONFIRMED_VINTAGE_ONLY"


def _validate_v2(fs, dec):
    _validate_authoritative_common(fs, dec)
    if fs.get("metadata_semantic_sha256") != EXPECTED_V2_SEMANTIC_SHA256:
        raise QualificationError("authoritative metadata semantic hash mismatch")

    canonicalization = fs.get("canonicalization")
    if not isinstance(canonicalization, dict):
        raise QualificationError("canonicalization contract missing")
    if canonicalization.get("included_record_keys") != list(SEMANTIC_RECORD_KEYS):
        raise QualificationError("canonicalization field set mismatch")
    if canonicalization.get("scope") != "all 84 OpenFemaDataSetFields records sorted by name":
        raise QualificationError("canonicalization scope mismatch")

    identities = fs.get("core_field_identities")
    if not isinstance(identities, dict):
        raise QualificationError("core field identities missing")
    for name, (field_hash, field_type, primary_key) in CORE_FIELD_IDENTITIES.items():
        record = identities.get(name, {})
        if (
            record.get("hash") != field_hash
            or record.get("type") != field_type
            or record.get("primaryKey") is not primary_key
        ):
            raise QualificationError(f"authoritative field identity mismatch: {name}")

    return "FIELD_SEMANTICS_CONFIRMED_VINTAGE_ONLY_STABLE_FINGERPRINT"


def validate(receipt):
    version = receipt.get("receipt_version")
    if version not in ALLOWED_VERSIONS:
        raise QualificationError("receipt_version mismatch")
    if receipt.get("claim_rows_accessed") is not False:
        raise QualificationError("claim_rows_accessed must be false")

    reg = receipt.get("fema_registry")
    fs = receipt.get("field_semantics")
    dec = receipt.get("decision")
    if not all(isinstance(section, dict) for section in (reg, fs, dec)):
        raise QualificationError("missing registry/field/decision section")

    _validate_registry(reg, dec)
    if version == V0:
        return _validate_v0(fs, dec)
    if version == V1:
        return _validate_v1(fs, dec)
    return _validate_v2(fs, dec)


def check():
    root = Path(__file__).resolve().parents[1]
    receipt_path = (
        root
        / "research"
        / "capital-modeling"
        / "nfip-v3-registry-qualification-receipt-v2.json"
    )
    receipt = load(receipt_path)
    result = validate(receipt)
    assert result == "FIELD_SEMANTICS_CONFIRMED_VINTAGE_ONLY_STABLE_FINGERPRINT"

    bad = json.loads(json.dumps(receipt))
    bad["decision"]["future_target_access"] = "ALLOWED"
    try:
        validate(bad)
    except QualificationError as exc:
        assert "future target" in str(exc)
    else:
        raise AssertionError("future target firewall was not enforced")

    bad = json.loads(json.dumps(receipt))
    bad["field_semantics"]["metadata_semantic_sha256"] = "drift"
    try:
        validate(bad)
    except QualificationError as exc:
        assert "semantic hash" in str(exc)
    else:
        raise AssertionError("semantic metadata drift was not blocked")

    print(
        "NFIP_V3_SCHEMA_QUALIFICATION_OK "
        "registry=confirmed fields=authoritative stable_fingerprint=true "
        "vintage_only=true future_target=forbidden"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--metadata")
    parser.add_argument("receipt", nargs="?")
    args = parser.parse_args()

    if args.check:
        check()
        return
    if not args.receipt:
        parser.error("receipt path required")

    receipt = load(args.receipt)
    if args.metadata:
        metadata = load(args.metadata)
        out = verify_live_metadata(metadata, receipt)
    else:
        out = {
            "status": validate(receipt),
            "receipt_sha256": hashlib.sha256(canonical(receipt)).hexdigest(),
        }
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
