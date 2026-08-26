# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed exact-key Greece exposure taxonomy to ESRM20 mapping join.

The worker consumes only the three already-receipted ESRM20 v1.0 Greece
runtime-exposure CSV objects plus the already-receipted ESRM20 v1.0 exposure to
vulnerability mapping. Every exposure object is passed through the existing
receipt-first Greece profiler before literal taxonomy extraction. Taxonomy
strings are neither normalized nor aliased; the existing exact mapping-join
semantics are reused unchanged.

A passing result is bounded component-compatibility evidence only. It does not
interpret GEM taxonomy attributes, select vulnerability files or IMTs, establish
hazard compatibility, authorize publication/model use, or execute loss.
"""

from __future__ import annotations

import csv
import hashlib
import io
from typing import Any

from scripts import join_esrm20_kosovo_taxonomy_mapping as exact_join
from scripts import profile_efehr_esrm20_greece_exposure_csvs as greece_source

SCHEMA_VERSION = "oc-esrm20-greece-taxonomy-mapping-join-v1"
SOURCE_ISSUE = 285
PARENT_CONSUMER_ISSUE = 287
SOURCE_PROFILE_TERMINAL_COMMENT_ID = 5417663718
SOURCE_PROFILE_EXECUTION_SHA = "c185974f6d704725f30cb75d2ee225c6c9f6abfe"
TAXONOMY_FIELD = "taxonomy"
EXPECTED_HEADER = (
    "id",
    "lon",
    "lat",
    "taxonomy",
    "number",
    "structural",
    "night",
    "day",
    "transit",
    "occupancy",
    "id_3",
    "id_3_left",
    "name_3",
    "id_3_right",
    "id_1",
    "name_1",
    "id_2",
    "name_2",
)

_CANONICAL_SOURCE_IDENTITY = {
    "source_issue": 285,
    "parent_consumer_issue": 287,
    "dataset_id": "efehr.esrm20.risk-inputs.v1.0",
    "project_id": 269,
    "project_path": "efehr/esrm20",
    "release_tag": "v1.0",
    "commit_sha": "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
    "consumer_event_id": "Greece_07-9-1999",
    "parent_exposure_path": "Exposure/OQ_Exposure_Input_Greece.xml",
    "receipt_comment_id": 5397480571,
    "receipt_execution_sha": "4b1d3c41a5df739b9686303eb753577ca39ec58e",
}

_CANONICAL_RECEIPTS = (
    (
        "Exposure/OQ_Exposure_Input_Greece_Com.csv",
        7_672_810,
        "2281f079a6e0b2215fab696d442f9d98b9b0ba94a2b4b24f23f1fff4018d1b57",
    ),
    (
        "Exposure/OQ_Exposure_Input_Greece_Ind.csv",
        2_822_653,
        "ad6698199d84002d017b41668dc204a2d53835a4b2429bc7e8eea56b328549c7",
    ),
    (
        "Exposure/OQ_Exposure_Input_Greece_Res.csv",
        5_263_604,
        "928ac7f069dfc3181a936f73caafb951a5c2437f70379fa29518c002bbd3ef28",
    ),
)

# Source-derived facts from trusted-main terminal 5417663718. These are used
# only to prove that literal extraction is still reading exactly the profiled
# taxonomy column; they do not assign taxonomy meaning.
_FROZEN_PROFILE_FACTS = {
    "Exposure/OQ_Exposure_Input_Greece_Com.csv": {
        "exposure_class": "commercial",
        "record_count": 37_290,
        "taxonomy_count": 91,
        "taxonomy_value_set_sha256": "8a1c35bc637c526fad162b03bca8bd2cee3b796d9155503dcdc86f4a98187250",
    },
    "Exposure/OQ_Exposure_Input_Greece_Ind.csv": {
        "exposure_class": "industrial",
        "record_count": 13_264,
        "taxonomy_count": 8,
        "taxonomy_value_set_sha256": "9dffe753610b813697108267209d18bca5181c7e15f3e6529001575b6ffd8f07",
    },
    "Exposure/OQ_Exposure_Input_Greece_Res.csv": {
        "exposure_class": "residential",
        "record_count": 24_057,
        "taxonomy_count": 149,
        "taxonomy_value_set_sha256": "384e89d5bf42109c3d0f7f0e8b7ca671e2a7a8d1815cb63710324e06fb269eea",
    },
}

_BASE_RECORD_FIELDS = {"taxonomy", "status", "reason_code", "targets"}
_AMBIGUOUS_REASON_CODES = {
    "matched_row_not_canonical",
    "duplicate_risk_id_semantics",
    "weights_outside_openquake_precision",
}


class GreeceTaxonomyMappingJoinError(ValueError):
    """Raised when exact exposure or mapping compatibility cannot be proven."""


def _value_set_sha256(values: set[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(values):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _require_frozen_exposure_authority() -> None:
    observed = {
        "source_issue": greece_source.SOURCE_ISSUE,
        "parent_consumer_issue": greece_source.PARENT_CONSUMER_ISSUE,
        "dataset_id": greece_source.DATASET_ID,
        "project_id": greece_source.PROJECT_ID,
        "project_path": greece_source.PROJECT_PATH,
        "release_tag": greece_source.RELEASE_TAG,
        "commit_sha": greece_source.COMMIT_SHA,
        "consumer_event_id": greece_source.CONSUMER_EVENT_ID,
        "parent_exposure_path": greece_source.PARENT_EXPOSURE_PATH,
        "receipt_comment_id": greece_source.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": greece_source.RECEIPT_EXECUTION_SHA,
    }
    if observed != _CANONICAL_SOURCE_IDENTITY:
        raise GreeceTaxonomyMappingJoinError("frozen Greece exposure source authority drifted")
    if tuple(greece_source.RECEIPTS) != _CANONICAL_RECEIPTS:
        raise GreeceTaxonomyMappingJoinError("frozen Greece exposure receipt authority drifted")
    if set(_FROZEN_PROFILE_FACTS) != {path for path, _, _ in _CANONICAL_RECEIPTS}:
        raise GreeceTaxonomyMappingJoinError("frozen Greece exposure profile path set drifted")


def _validate_profile_gate(repository_path: str, evidence: Any) -> dict[str, Any]:
    if type(evidence) is not dict or set(evidence) != {
        "repository_path",
        "byte_count",
        "sha256",
        "profile",
    }:
        raise GreeceTaxonomyMappingJoinError("Greece exposure profile result fields drifted")

    receipt_map = {path: (count, digest) for path, count, digest in _CANONICAL_RECEIPTS}
    if repository_path not in receipt_map:
        raise GreeceTaxonomyMappingJoinError("Greece exposure path left frozen receipt set")
    expected_count, expected_sha256 = receipt_map[repository_path]
    if evidence["repository_path"] != repository_path:
        raise GreeceTaxonomyMappingJoinError("Greece exposure profile path drifted")
    if evidence["byte_count"] != expected_count or evidence["sha256"] != expected_sha256:
        raise GreeceTaxonomyMappingJoinError("Greece exposure profile receipt identity drifted")

    profile = evidence["profile"]
    if type(profile) is not dict:
        raise GreeceTaxonomyMappingJoinError("Greece exposure profile payload drifted")
    facts = _FROZEN_PROFILE_FACTS[repository_path]
    if profile.get("schema_version") != greece_source.generic_csv.SCHEMA_VERSION:
        raise GreeceTaxonomyMappingJoinError("Greece exposure profile schema drifted")
    if profile.get("record_count") != facts["record_count"]:
        raise GreeceTaxonomyMappingJoinError("Greece exposure record count drifted")
    if tuple(profile.get("header", ())) != EXPECTED_HEADER:
        raise GreeceTaxonomyMappingJoinError("Greece exposure header drifted")
    parser = profile.get("parser")
    if type(parser) is not dict or (
        parser.get("encoding") != "utf-8"
        or parser.get("bom_present") is not False
        or parser.get("delimiter") != ","
    ):
        raise GreeceTaxonomyMappingJoinError("Greece exposure parser contract drifted")
    for flag in ("raw_rows_returned", "external_bytes_persisted", "publication_authorized"):
        if profile.get(flag) is not False:
            raise GreeceTaxonomyMappingJoinError(f"Greece exposure profile widened {flag}")

    columns = profile.get("columns")
    if type(columns) is not list:
        raise GreeceTaxonomyMappingJoinError("Greece exposure column profile drifted")
    matches = [
        column
        for column in columns
        if type(column) is dict and column.get("name") == TAXONOMY_FIELD
    ]
    if len(matches) != 1:
        raise GreeceTaxonomyMappingJoinError("Greece exposure taxonomy column is not unique")
    taxonomy = matches[0]
    if (
        taxonomy.get("record_count") != facts["record_count"]
        or taxonomy.get("empty_count") != 0
        or taxonomy.get("nonempty_count") != facts["record_count"]
        or taxonomy.get("distinct_count") != facts["taxonomy_count"]
        or taxonomy.get("exact_value_set_sha256") != facts["taxonomy_value_set_sha256"]
    ):
        raise GreeceTaxonomyMappingJoinError("Greece exposure taxonomy profile drifted")
    decimal_summary = taxonomy.get("decimal_summary")
    if type(decimal_summary) is not dict or decimal_summary.get(
        "leading_or_trailing_whitespace_count"
    ) != 0:
        raise GreeceTaxonomyMappingJoinError("Greece exposure taxonomy whitespace profile drifted")
    return facts


def _extract_taxonomies_from_profiled_text(
    text: str,
    *,
    expected_record_count: int,
    expected_taxonomy_count: int,
    expected_value_set_sha256: str,
) -> list[str]:
    if type(text) is not str or "\x00" in text:
        raise GreeceTaxonomyMappingJoinError("verified Greece exposure text is invalid")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",", strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise GreeceTaxonomyMappingJoinError("verified Greece exposure CSV has no header") from exc
    except csv.Error as exc:
        raise GreeceTaxonomyMappingJoinError("verified Greece exposure CSV header is malformed") from exc
    if tuple(header) != EXPECTED_HEADER:
        raise GreeceTaxonomyMappingJoinError("verified Greece exposure CSV header drifted")
    taxonomy_index = header.index(TAXONOMY_FIELD)

    values: set[str] = set()
    record_count = 0
    try:
        for row in reader:
            if len(row) != len(EXPECTED_HEADER):
                raise GreeceTaxonomyMappingJoinError(
                    "verified Greece exposure CSV contains a ragged row"
                )
            record_count += 1
            taxonomy = row[taxonomy_index]
            if not exact_join._is_bounded_literal(
                taxonomy, max_utf8_bytes=exact_join.MAX_TAXONOMY_UTF8_BYTES
            ):
                raise GreeceTaxonomyMappingJoinError(
                    "verified Greece exposure CSV contains an invalid taxonomy literal"
                )
            values.add(taxonomy)
    except csv.Error as exc:
        raise GreeceTaxonomyMappingJoinError("verified Greece exposure CSV is malformed") from exc

    if record_count != expected_record_count:
        raise GreeceTaxonomyMappingJoinError(
            "Greece exposure record count changed after profile gate"
        )
    if len(values) != expected_taxonomy_count:
        raise GreeceTaxonomyMappingJoinError(
            "Greece taxonomy distinct count changed after profile gate"
        )
    if _value_set_sha256(values) != expected_value_set_sha256:
        raise GreeceTaxonomyMappingJoinError(
            "Greece taxonomy value-set fingerprint changed after profile gate"
        )
    return sorted(values)


def _extract_verified_taxonomies(raw: bytes, *, repository_path: str) -> dict[str, Any]:
    try:
        evidence = greece_source.profile_verified_csv_bytes(raw, repository_path=repository_path)
    except greece_source.GreeceExposureCsvProfileError as exc:
        raise GreeceTaxonomyMappingJoinError(
            "Greece exposure receipt/profile gate did not pass"
        ) from exc

    facts = _validate_profile_gate(repository_path, evidence)
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:  # defensive: profile gate already proved this
        raise GreeceTaxonomyMappingJoinError(
            "verified Greece exposure is not strict UTF-8"
        ) from exc
    taxonomies = _extract_taxonomies_from_profiled_text(
        text,
        expected_record_count=facts["record_count"],
        expected_taxonomy_count=facts["taxonomy_count"],
        expected_value_set_sha256=facts["taxonomy_value_set_sha256"],
    )
    return {
        "repository_path": repository_path,
        "exposure_class": facts["exposure_class"],
        "record_count": facts["record_count"],
        "taxonomy_count": facts["taxonomy_count"],
        "taxonomy_value_set_sha256": facts["taxonomy_value_set_sha256"],
        "taxonomies": taxonomies,
    }


def _validate_exact_join_records(
    base_records: object, *, taxonomies: list[str]
) -> list[dict[str, Any]]:
    """Bind the reused exact-join helper to its reviewed output contract."""
    if type(base_records) is not list or len(base_records) != len(taxonomies):
        raise GreeceTaxonomyMappingJoinError("exact mapping join result cardinality drifted")

    observed_taxonomies: list[str] = []
    validated: list[dict[str, Any]] = []
    for base in base_records:
        if type(base) is not dict or set(base) != _BASE_RECORD_FIELDS:
            raise GreeceTaxonomyMappingJoinError("exact mapping join result fields drifted")
        taxonomy = base["taxonomy"]
        status = base["status"]
        reason_code = base["reason_code"]
        targets = base["targets"]
        if type(taxonomy) is not str:
            raise GreeceTaxonomyMappingJoinError("exact mapping join taxonomy drifted")
        observed_taxonomies.append(taxonomy)

        if status == "resolved":
            if reason_code != "exact_mapping_rows_valid" or type(targets) is not list or not targets:
                raise GreeceTaxonomyMappingJoinError("resolved mapping result contract drifted")
            target_risk_ids: list[str] = []
            target_weights: list[float] = []
            for target in targets:
                if type(target) is not dict or set(target) != {"risk_id", "weight"}:
                    raise GreeceTaxonomyMappingJoinError("resolved mapping target fields drifted")
                risk_id = target["risk_id"]
                weight = target["weight"]
                if (
                    not exact_join._is_bounded_literal(
                        risk_id, max_utf8_bytes=exact_join.MAX_RISK_ID_UTF8_BYTES
                    )
                    or risk_id != risk_id.strip()
                ):
                    raise GreeceTaxonomyMappingJoinError("resolved mapping risk id drifted")
                if (
                    type(weight) is not str
                    or not weight
                    or len(weight) > exact_join.MAX_WEIGHT_CHARS
                    or weight != weight.strip()
                ):
                    raise GreeceTaxonomyMappingJoinError("resolved mapping weight shape drifted")
                parsed_weight = exact_join._weight(weight)
                if parsed_weight is None:
                    raise GreeceTaxonomyMappingJoinError("resolved mapping weight semantics drifted")
                target_risk_ids.append(risk_id)
                target_weights.append(parsed_weight)
            if abs(sum(target_weights) - 1.0) > exact_join.OPENQUAKE_WEIGHT_PRECISION:
                raise GreeceTaxonomyMappingJoinError("resolved mapping weight sum drifted")
            if (
                len(set(target_risk_ids)) != len(target_risk_ids)
                or target_risk_ids != sorted(target_risk_ids)
            ):
                raise GreeceTaxonomyMappingJoinError("resolved mapping target order drifted")
        elif status == "unsupported":
            if reason_code != "no_exact_mapping_row" or targets != []:
                raise GreeceTaxonomyMappingJoinError("unsupported mapping result contract drifted")
        elif status == "ambiguous":
            if reason_code not in _AMBIGUOUS_REASON_CODES or targets != []:
                raise GreeceTaxonomyMappingJoinError("ambiguous mapping result contract drifted")
        else:
            raise GreeceTaxonomyMappingJoinError("exact mapping join returned an invalid status")
        validated.append(base)

    if observed_taxonomies != taxonomies:
        raise GreeceTaxonomyMappingJoinError("exact mapping join taxonomy coverage/order drifted")
    return validated


def join_verified_greece_taxonomy_mapping(
    exposure_raw_by_path: dict[str, bytes], mapping_raw: bytes
) -> dict[str, Any]:
    """Verify all frozen inputs and perform exact literal mapping classification."""

    _require_frozen_exposure_authority()
    try:
        exact_join._require_frozen_mapping_authority()
    except exact_join.KosovoMappingJoinError as exc:
        raise GreeceTaxonomyMappingJoinError(
            "frozen ESRM20 mapping authority drifted"
        ) from exc

    if type(exposure_raw_by_path) is not dict:
        raise GreeceTaxonomyMappingJoinError("Greece exposure bundle must be a dict")
    expected_paths = [path for path, _, _ in _CANONICAL_RECEIPTS]
    if set(exposure_raw_by_path) != set(expected_paths):
        raise GreeceTaxonomyMappingJoinError(
            "Greece exposure bundle does not match frozen receipt set"
        )

    extracted = [
        _extract_verified_taxonomies(exposure_raw_by_path[path], repository_path=path)
        for path in expected_paths
    ]
    exposure_classes_by_taxonomy: dict[str, set[str]] = {}
    for item in extracted:
        for taxonomy in item["taxonomies"]:
            exposure_classes_by_taxonomy.setdefault(taxonomy, set()).add(
                item["exposure_class"]
            )
    taxonomies = sorted(exposure_classes_by_taxonomy)
    if not taxonomies:
        raise GreeceTaxonomyMappingJoinError("Greece exposure taxonomy union is empty")

    try:
        base_records = exact_join._join_exact_taxonomies(
            taxonomies,
            mapping_raw,
            expected_byte_count=exact_join._MAPPING_BYTE_COUNT,
            expected_sha256=exact_join._MAPPING_SHA256,
        )
    except exact_join.KosovoMappingJoinError as exc:
        raise GreeceTaxonomyMappingJoinError("ESRM20 exact mapping join failed closed") from exc
    base_records = _validate_exact_join_records(base_records, taxonomies=taxonomies)

    records: list[dict[str, Any]] = []
    counts = {status: 0 for status in ("resolved", "unsupported", "ambiguous")}
    risk_ids: set[str] = set()
    for base in base_records:
        taxonomy = base["taxonomy"]
        status = base["status"]
        counts[status] += 1
        for target in base["targets"]:
            risk_ids.add(target["risk_id"])
        record = dict(base)
        record["exposure_classes"] = sorted(exposure_classes_by_taxonomy[taxonomy])
        records.append(record)

    if len(records) != len(taxonomies) or sum(counts.values()) != len(taxonomies):
        raise GreeceTaxonomyMappingJoinError(
            "Greece mapping classification is not exhaustive"
        )

    exposure_files = [
        {
            "repository_path": item["repository_path"],
            "exposure_class": item["exposure_class"],
            "record_count": item["record_count"],
            "taxonomy_count": item["taxonomy_count"],
            "taxonomy_value_set_sha256": item["taxonomy_value_set_sha256"],
        }
        for item in extracted
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "source_profile_terminal_comment_id": SOURCE_PROFILE_TERMINAL_COMMENT_ID,
        "source_profile_execution_sha": SOURCE_PROFILE_EXECUTION_SHA,
        "consumer_event_id": _CANONICAL_SOURCE_IDENTITY["consumer_event_id"],
        "exposure_source": {
            "dataset_id": _CANONICAL_SOURCE_IDENTITY["dataset_id"],
            "project_id": _CANONICAL_SOURCE_IDENTITY["project_id"],
            "project_path": _CANONICAL_SOURCE_IDENTITY["project_path"],
            "release_tag": _CANONICAL_SOURCE_IDENTITY["release_tag"],
            "commit_sha": _CANONICAL_SOURCE_IDENTITY["commit_sha"],
            "parent_exposure_path": _CANONICAL_SOURCE_IDENTITY["parent_exposure_path"],
            "receipt_comment_id": _CANONICAL_SOURCE_IDENTITY["receipt_comment_id"],
            "receipt_execution_sha": _CANONICAL_SOURCE_IDENTITY["receipt_execution_sha"],
            "files": exposure_files,
        },
        "mapping_source": {
            "dataset_id": exact_join._MAPPING_DATASET_ID,
            "project_id": exact_join._MAPPING_PROJECT_ID,
            "project_path": exact_join._MAPPING_PROJECT_PATH,
            "commit_sha": exact_join._MAPPING_COMMIT_SHA,
            "repository_path": exact_join._MAPPING_REPOSITORY_PATH,
            "byte_count": exact_join._MAPPING_BYTE_COUNT,
            "sha256": exact_join._MAPPING_SHA256,
        },
        "classification_counts": counts,
        "taxonomy_union_count": len(taxonomies),
        "all_taxonomies_resolved": counts["unsupported"] == 0
        and counts["ambiguous"] == 0,
        "mapping_target_risk_ids": sorted(risk_ids),
        "records": records,
        "taxonomy_matching": "exact_literal_equality_only",
        "normalization_applied": False,
        "wildcard_or_fallback_matching_applied": False,
        "taxonomy_semantics_verified": False,
        "bounded_derived_disclosure_authorized": False,
        "vulnerability_file_selection_authorized": False,
        "vulnerability_imt_selection_verified": False,
        "hazard_compatibility_verified": False,
        "ground_up_loss_executed": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "raw_exposure_rows_returned": False,
        "raw_mapping_rows_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
