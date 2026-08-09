# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict dependency-free validation for transformation contract v0."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROFILE_VERSION = "0.2.0"
ROW_SEMANTICS = "one_to_one"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
FIELD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+-]{0,63}$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
MUTABLE_VERSION_ALIASES = {"latest", "stable", "main", "master", "develop"}
OPERATIONS = {"copy", "rename", "code_map", "unit_conversion"}
METRICS = {"count", "sum", "null_count", "unique_count"}
COMPARISONS = {"equal", "absolute_tolerance"}
RELATIONS = {"equal", "affine"}


class TransformationContractError(ValueError):
    """Raised when a transformation contract fails closed validation."""


@dataclass(frozen=True, slots=True)
class RuleInfo:
    """Validated rule semantics used for reconciliation cross-checks."""

    rule_id: str
    operation: str
    source_field: str
    target_field: str
    lossy: bool
    reversible: bool
    factor: float | None = None
    offset: float | None = None


def _reject_constant(value: str) -> None:
    raise TransformationContractError(f"non-finite JSON number is forbidden: {value}")


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TransformationContractError(f"duplicate JSON key is forbidden: {key}")
        result[key] = value
    return result


def load_strict_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, TransformationContractError) as exc:
        raise TransformationContractError(f"unable to load strict JSON from {path}: {exc}") from exc


def _obj(value: Any, where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise TransformationContractError(f"{where} must be an object")
    return value


def _arr(value: Any, where: str) -> list[Any]:
    if type(value) is not list:
        raise TransformationContractError(f"{where} must be an array")
    return value


def _str(value: Any, where: str, *, max_length: int | None = None) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise TransformationContractError(f"{where} must be a non-empty trimmed string")
    if CONTROL_RE.search(value):
        raise TransformationContractError(f"{where} must not contain control characters")
    if max_length is not None and len(value) > max_length:
        raise TransformationContractError(f"{where} exceeds {max_length} characters")
    return value


def _bool(value: Any, where: str) -> bool:
    if type(value) is not bool:
        raise TransformationContractError(f"{where} must be a boolean")
    return value


def _number(value: Any, where: str) -> float:
    if type(value) not in {int, float}:
        raise TransformationContractError(f"{where} must be a number")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise TransformationContractError(f"{where} must be a finite representable number") from exc
    if not math.isfinite(result):
        raise TransformationContractError(f"{where} must be finite")
    return result


def _closed(obj: dict[str, Any], where: str, required: set[str], allowed: set[str]) -> None:
    missing = sorted(required - obj.keys())
    extras = sorted(obj.keys() - allowed)
    if missing:
        raise TransformationContractError(f"{where} missing required fields: {', '.join(missing)}")
    if extras:
        raise TransformationContractError(f"{where} has unexpected fields: {', '.join(extras)}")


def _id(value: Any, where: str) -> str:
    text = _str(value, where)
    if not ID_RE.fullmatch(text):
        raise TransformationContractError(f"{where} has an invalid identifier format")
    return text


def _field(value: Any, where: str) -> str:
    text = _str(value, where)
    if not FIELD_RE.fullmatch(text):
        raise TransformationContractError(f"{where} has an invalid field identifier")
    return text


def _version(value: Any, where: str) -> str:
    text = _str(value, where, max_length=64)
    if not VERSION_RE.fullmatch(text):
        raise TransformationContractError(f"{where} has an invalid version format")
    if text.casefold() in MUTABLE_VERSION_ALIASES:
        raise TransformationContractError(
            f"{where} must identify an immutable version, not a mutable alias"
        )
    return text


def _profile(value: Any, where: str) -> None:
    profile = _obj(value, where)
    _closed(profile, where, {"name", "version"}, {"name", "version"})
    _id(profile["name"], f"{where}.name")
    _version(profile["version"], f"{where}.version")


def _rule(value: Any, where: str) -> RuleInfo:
    rule = _obj(value, where)
    common = {"rule_id", "operation", "source_field", "target_field", "lossy", "reversible"}
    _closed(rule, where, common, common | {"mapping", "from_unit", "to_unit", "factor", "offset"})
    rule_id = _id(rule["rule_id"], f"{where}.rule_id")
    operation = _str(rule["operation"], f"{where}.operation")
    if operation not in OPERATIONS:
        raise TransformationContractError(f"{where}.operation is unsupported: {operation}")
    source = _field(rule["source_field"], f"{where}.source_field")
    target = _field(rule["target_field"], f"{where}.target_field")
    lossy = _bool(rule["lossy"], f"{where}.lossy")
    reversible = _bool(rule["reversible"], f"{where}.reversible")
    if lossy and reversible:
        raise TransformationContractError(f"{where} cannot be both lossy and reversible")

    factor: float | None = None
    offset: float | None = None
    if operation in {"copy", "rename"}:
        if set(rule) != common:
            raise TransformationContractError(f"{where} {operation} rule has operation-specific extra fields")
    elif operation == "code_map":
        expected = common | {"mapping"}
        if set(rule) != expected:
            raise TransformationContractError(f"{where} code_map rule must contain exactly {sorted(expected)}")
        mapping = _arr(rule["mapping"], f"{where}.mapping")
        if not mapping:
            raise TransformationContractError(f"{where}.mapping must not be empty")
        source_codes: set[str] = set()
        target_codes: set[str] = set()
        for index, pair_value in enumerate(mapping):
            pair = _obj(pair_value, f"{where}.mapping[{index}]")
            _closed(pair, f"{where}.mapping[{index}]", {"from", "to"}, {"from", "to"})
            source_code = _str(
                pair["from"], f"{where}.mapping[{index}].from", max_length=256
            )
            target_code = _str(
                pair["to"], f"{where}.mapping[{index}].to", max_length=256
            )
            if source_code in source_codes:
                raise TransformationContractError(f"{where}.mapping has duplicate source code: {source_code}")
            source_codes.add(source_code)
            if reversible and target_code in target_codes:
                raise TransformationContractError(
                    f"{where}.mapping cannot be reversible with duplicate target codes"
                )
            target_codes.add(target_code)
    else:
        expected = common | {"from_unit", "to_unit", "factor", "offset"}
        if set(rule) != expected:
            raise TransformationContractError(
                f"{where} unit_conversion rule must contain exactly {sorted(expected)}"
            )
        from_unit = _str(rule["from_unit"], f"{where}.from_unit", max_length=64)
        to_unit = _str(rule["to_unit"], f"{where}.to_unit", max_length=64)
        factor = _number(rule["factor"], f"{where}.factor")
        offset = _number(rule["offset"], f"{where}.offset")
        if from_unit == to_unit:
            raise TransformationContractError(f"{where} unit_conversion must change the declared unit")
        if factor == 0:
            raise TransformationContractError(f"{where}.factor must not be zero")

    return RuleInfo(
        rule_id=rule_id,
        operation=operation,
        source_field=source,
        target_field=target,
        lossy=lossy,
        reversible=reversible,
        factor=factor,
        offset=offset,
    )


def _comparison(value: Any, where: str) -> None:
    comparison = _obj(value, where)
    _closed(comparison, where, {"method"}, {"method", "tolerance"})
    method = _str(comparison["method"], f"{where}.method")
    if method not in COMPARISONS:
        raise TransformationContractError(f"{where}.method is unsupported: {method}")
    if method == "equal":
        if "tolerance" in comparison:
            raise TransformationContractError(f"{where}.tolerance is forbidden for equal comparison")
    else:
        if "tolerance" not in comparison:
            raise TransformationContractError(f"{where}.tolerance is required for absolute_tolerance")
        if _number(comparison["tolerance"], f"{where}.tolerance") < 0:
            raise TransformationContractError(f"{where}.tolerance must be >= 0")


def _relation(value: Any, where: str) -> tuple[str, float | None, float | None]:
    relation = _obj(value, where)
    kind = _str(relation.get("kind"), f"{where}.kind")
    if kind not in RELATIONS:
        raise TransformationContractError(f"{where}.kind is unsupported: {kind}")
    if kind == "equal":
        _closed(relation, where, {"kind"}, {"kind"})
        return kind, None, None
    _closed(
        relation,
        where,
        {"kind", "factor", "offset_per_record"},
        {"kind", "factor", "offset_per_record"},
    )
    factor = _number(relation["factor"], f"{where}.factor")
    offset = _number(relation["offset_per_record"], f"{where}.offset_per_record")
    if factor == 0:
        raise TransformationContractError(f"{where}.factor must not be zero")
    return kind, factor, offset


def _group_fields(value: Any, where: str, known_fields: set[str]) -> list[str]:
    fields = [
        _field(item, f"{where}[{index}]")
        for index, item in enumerate(_arr(value, where))
    ]
    if len(fields) != len(set(fields)):
        raise TransformationContractError(f"{where} must not contain duplicates")
    for field in fields:
        if field not in known_fields:
            raise TransformationContractError(f"{where} references unknown field: {field}")
    return fields


def _mapping_rule(
    source: str,
    target: str,
    where: str,
    rules_by_pair: dict[tuple[str, str], RuleInfo],
) -> RuleInfo:
    try:
        return rules_by_pair[(source, target)]
    except KeyError as exc:
        raise TransformationContractError(
            f"{where} has no declared mapping rule from {source} to {target}"
        ) from exc


def _reconciliation(
    value: Any,
    where: str,
    *,
    source_fields: set[str],
    target_fields: set[str],
    rules_by_pair: dict[tuple[str, str], RuleInfo],
) -> str:
    check = _obj(value, where)
    required = {
        "check_id",
        "metric",
        "source_group_by",
        "target_group_by",
        "relation",
        "comparison",
    }
    allowed = required | {"source_field", "target_field"}
    _closed(check, where, required, allowed)
    check_id = _id(check["check_id"], f"{where}.check_id")
    metric = _str(check["metric"], f"{where}.metric")
    if metric not in METRICS:
        raise TransformationContractError(f"{where}.metric is unsupported: {metric}")

    source_groups = _group_fields(
        check["source_group_by"], f"{where}.source_group_by", source_fields
    )
    target_groups = _group_fields(
        check["target_group_by"], f"{where}.target_group_by", target_fields
    )
    if len(source_groups) != len(target_groups):
        raise TransformationContractError(
            f"{where} source_group_by and target_group_by must have equal length"
        )
    for index, (source_group, target_group) in enumerate(zip(source_groups, target_groups)):
        rule = _mapping_rule(
            source_group,
            target_group,
            f"{where}.group_pair[{index}]",
            rules_by_pair,
        )
        if rule.lossy or not rule.reversible:
            raise TransformationContractError(
                f"{where}.group_pair[{index}] requires a lossless reversible mapping"
            )

    relation_kind, relation_factor, relation_offset = _relation(
        check["relation"], f"{where}.relation"
    )

    if metric == "count":
        if "source_field" in check or "target_field" in check:
            raise TransformationContractError(
                f"{where} count must not declare source_field or target_field"
            )
        if relation_kind != "equal":
            raise TransformationContractError(f"{where} count requires equal relation")
    else:
        if "source_field" not in check or "target_field" not in check:
            raise TransformationContractError(
                f"{where} {metric} requires source_field and target_field"
            )
        source_field = _field(check["source_field"], f"{where}.source_field")
        target_field = _field(check["target_field"], f"{where}.target_field")
        if source_field not in source_fields:
            raise TransformationContractError(
                f"{where}.source_field references unknown mapped source field: {source_field}"
            )
        if target_field not in target_fields:
            raise TransformationContractError(
                f"{where}.target_field references unknown mapped target field: {target_field}"
            )
        rule = _mapping_rule(source_field, target_field, where, rules_by_pair)

        if metric == "sum":
            if rule.operation in {"copy", "rename"}:
                if rule.lossy or relation_kind != "equal":
                    raise TransformationContractError(
                        f"{where} sum over copy/rename requires a lossless equal relation"
                    )
            elif rule.operation == "unit_conversion":
                if relation_kind != "affine":
                    raise TransformationContractError(
                        f"{where} sum over unit_conversion requires affine relation"
                    )
                if relation_factor != rule.factor or relation_offset != rule.offset:
                    raise TransformationContractError(
                        f"{where} affine relation must match the unit-conversion factor and offset"
                    )
            else:
                raise TransformationContractError(
                    f"{where} sum is not defined for code_map in transformation contract v0"
                )
        else:
            if relation_kind != "equal":
                raise TransformationContractError(f"{where} {metric} requires equal relation")
            if rule.lossy or not rule.reversible:
                raise TransformationContractError(
                    f"{where} {metric} requires a lossless reversible field mapping"
                )

    _comparison(check["comparison"], f"{where}.comparison")
    return check_id


def validate_contract(payload: Any) -> None:
    contract = _obj(payload, "contract")
    required = {
        "profile_version",
        "mapping_id",
        "mapping_version",
        "source_profile",
        "target_profile",
        "row_semantics",
        "rules",
        "unsupported_fields",
        "semantics",
        "reconciliation_checks",
    }
    _closed(contract, "contract", required, required)
    if _str(contract["profile_version"], "contract.profile_version") != PROFILE_VERSION:
        raise TransformationContractError(
            f"contract.profile_version must equal {PROFILE_VERSION}"
        )
    _id(contract["mapping_id"], "contract.mapping_id")
    _version(contract["mapping_version"], "contract.mapping_version")
    _profile(contract["source_profile"], "contract.source_profile")
    _profile(contract["target_profile"], "contract.target_profile")
    if _str(contract["row_semantics"], "contract.row_semantics") != ROW_SEMANTICS:
        raise TransformationContractError(
            f"contract.row_semantics must equal {ROW_SEMANTICS} in profile {PROFILE_VERSION}"
        )

    rules = _arr(contract["rules"], "contract.rules")
    if not rules:
        raise TransformationContractError("contract.rules must not be empty")
    rule_ids: set[str] = set()
    source_fields: set[str] = set()
    target_fields: set[str] = set()
    rules_by_pair: dict[tuple[str, str], RuleInfo] = {}
    any_rule_lossy = False
    for index, rule_value in enumerate(rules):
        rule = _rule(rule_value, f"contract.rules[{index}]")
        if rule.rule_id in rule_ids:
            raise TransformationContractError(
                f"contract.rules has duplicate rule_id: {rule.rule_id}"
            )
        if rule.target_field in target_fields:
            raise TransformationContractError(
                f"contract.rules write target field more than once: {rule.target_field}"
            )
        pair = (rule.source_field, rule.target_field)
        if pair in rules_by_pair:
            raise TransformationContractError(
                f"contract.rules duplicate mapping pair: {rule.source_field}->{rule.target_field}"
            )
        rule_ids.add(rule.rule_id)
        source_fields.add(rule.source_field)
        target_fields.add(rule.target_field)
        rules_by_pair[pair] = rule
        any_rule_lossy = any_rule_lossy or rule.lossy

    unsupported = [
        _field(item, f"contract.unsupported_fields[{index}]")
        for index, item in enumerate(
            _arr(contract["unsupported_fields"], "contract.unsupported_fields")
        )
    ]
    if len(unsupported) != len(set(unsupported)):
        raise TransformationContractError(
            "contract.unsupported_fields must not contain duplicates"
        )
    overlap = sorted(set(unsupported) & source_fields)
    if overlap:
        raise TransformationContractError(
            f"unsupported fields cannot also be mapped: {', '.join(overlap)}"
        )

    semantics = _obj(contract["semantics"], "contract.semantics")
    _closed(semantics, "contract.semantics", {"lossy", "notes"}, {"lossy", "notes"})
    overall_lossy = _bool(semantics["lossy"], "contract.semantics.lossy")
    _str(semantics["notes"], "contract.semantics.notes", max_length=1000)
    if (any_rule_lossy or unsupported) and not overall_lossy:
        raise TransformationContractError(
            "contract.semantics.lossy must be true when a rule is lossy or fields are unsupported"
        )

    checks = _arr(contract["reconciliation_checks"], "contract.reconciliation_checks")
    if not checks:
        raise TransformationContractError(
            "contract.reconciliation_checks must not be empty"
        )
    check_ids: set[str] = set()
    for index, check_value in enumerate(checks):
        check_id = _reconciliation(
            check_value,
            f"contract.reconciliation_checks[{index}]",
            source_fields=source_fields,
            target_fields=target_fields,
            rules_by_pair=rules_by_pair,
        )
        if check_id in check_ids:
            raise TransformationContractError(
                f"contract.reconciliation_checks has duplicate check_id: {check_id}"
            )
        check_ids.add(check_id)


def canonical_bytes(payload: Any) -> bytes:
    validate_contract(payload)
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def contract_identity(payload: Any) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="transformation contract JSON file")
    parser.add_argument(
        "--identity", action="store_true", help="print deterministic contract SHA-256"
    )
    args = parser.parse_args(argv)
    try:
        payload = load_strict_json(args.path)
        validate_contract(payload)
        if args.identity:
            print(contract_identity(payload))
        else:
            print("PASS")
        return 0
    except TransformationContractError as exc:
        print(f"BLOCKED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
