# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded offline profiler for the receipted Athens ESRM20 v1.0 GMPE logic tree."""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from collections import Counter
from typing import Final

EXPECTED_BYTE_COUNT: Final = 6_490
EXPECTED_SHA256: Final = "3c6ff83efcac45cf75125e035060e84b910c45a9e531306d822b4566383d5b78"
EXPECTED_NRML_NAMESPACE: Final = "http://openquake.org/xmlns/nrml/0.5"
MAX_ELEMENTS: Final = 512
MAX_DEPTH: Final = 16
MAX_TEXT_UTF8_BYTES: Final = 4_096
_LOCAL_NAME_RE: Final = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
_FORBIDDEN_DECL_RE: Final = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)


class GmpeLogicTreeProfileError(ValueError):
    """Exact identity or bounded logic-tree structure failed closed."""


def _split_tag(tag: object) -> tuple[str, str]:
    if type(tag) is not str:
        raise GmpeLogicTreeProfileError("non_text_xml_tag")
    if tag.startswith("{"):
        end = tag.find("}")
        if end <= 1:
            raise GmpeLogicTreeProfileError("malformed_expanded_xml_name")
        namespace, local = tag[1:end], tag[end + 1 :]
    else:
        namespace, local = "", tag
    if not _LOCAL_NAME_RE.fullmatch(local):
        raise GmpeLogicTreeProfileError("unsafe_xml_local_name")
    return namespace, local


def _decode(data: bytes) -> str:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise GmpeLogicTreeProfileError("non_utf8_xml_encoding")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise GmpeLogicTreeProfileError("invalid_utf8_xml") from exc
    if "\x00" in text:
        raise GmpeLogicTreeProfileError("nul_character_forbidden")
    if _FORBIDDEN_DECL_RE.search(text):
        raise GmpeLogicTreeProfileError("dtd_or_entity_forbidden")
    return text


def _profile_verified(data: bytes, *, expected_byte_count: int, expected_sha256: str) -> dict[str, object]:
    if type(data) is not bytes:
        raise TypeError("data must be bytes")
    if len(data) != expected_byte_count:
        raise GmpeLogicTreeProfileError("byte_count_mismatch")
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise GmpeLogicTreeProfileError("sha256_mismatch")

    try:
        root = ET.fromstring(_decode(data))
    except ET.ParseError as exc:
        raise GmpeLogicTreeProfileError("invalid_xml") from exc

    namespace, local = _split_tag(root.tag)
    if namespace != EXPECTED_NRML_NAMESPACE or local != "nrml":
        raise GmpeLogicTreeProfileError("unexpected_nrml_root")
    top = list(root)
    if len(top) != 1 or _split_tag(top[0].tag) != (EXPECTED_NRML_NAMESPACE, "logicTree"):
        raise GmpeLogicTreeProfileError("unexpected_logic_tree_root")

    counts: Counter[str] = Counter()
    attribute_names: Counter[str] = Counter()
    text_element_count = 0
    text_value_fingerprints: set[str] = set()
    element_count = 0
    max_depth = 0
    stack: list[tuple[ET.Element, int]] = [(root, 1)]
    expected_direct_children = {
        "logicTree": "logicTreeBranchingLevel",
        "logicTreeBranchingLevel": "logicTreeBranchSet",
        "logicTreeBranchSet": "logicTreeBranch",
    }
    while stack:
        element, depth = stack.pop()
        element_count += 1
        if element_count > MAX_ELEMENTS:
            raise GmpeLogicTreeProfileError("xml_element_limit_exceeded")
        if depth > MAX_DEPTH:
            raise GmpeLogicTreeProfileError("xml_depth_limit_exceeded")
        max_depth = max(max_depth, depth)
        ns, name = _split_tag(element.tag)
        if ns != EXPECTED_NRML_NAMESPACE:
            raise GmpeLogicTreeProfileError("foreign_xml_namespace")
        counts[name] += 1
        children = list(element)
        if name in expected_direct_children:
            expected_child = expected_direct_children[name]
            if not children:
                raise GmpeLogicTreeProfileError(f"missing_direct_child:{name}:{expected_child}")
            for child in children:
                child_ns, child_name = _split_tag(child.tag)
                if child_ns != EXPECTED_NRML_NAMESPACE:
                    raise GmpeLogicTreeProfileError("foreign_xml_namespace")
                if child_name != expected_child:
                    raise GmpeLogicTreeProfileError(f"unexpected_direct_child:{name}:{child_name}")
        if name == "logicTreeBranch":
            direct_child_names: Counter[str] = Counter()
            for child in children:
                child_ns, child_name = _split_tag(child.tag)
                if child_ns != EXPECTED_NRML_NAMESPACE:
                    raise GmpeLogicTreeProfileError("foreign_xml_namespace")
                direct_child_names[child_name] += 1
            if direct_child_names != Counter({"uncertaintyModel": 1, "uncertaintyWeight": 1}):
                raise GmpeLogicTreeProfileError("branch_direct_child_cardinality_mismatch")
        for raw_name, value in element.attrib.items():
            attr_ns, attr_name = _split_tag(raw_name)
            if attr_ns:
                raise GmpeLogicTreeProfileError("namespaced_attribute_forbidden")
            if len(value.encode("utf-8")) > 512:
                raise GmpeLogicTreeProfileError("attribute_value_too_large")
            attribute_names[attr_name] += 1
        text = element.text or ""
        if text.strip():
            raw = text.strip().encode("utf-8")
            if len(raw) > MAX_TEXT_UTF8_BYTES:
                raise GmpeLogicTreeProfileError("element_text_too_large")
            text_element_count += 1
            text_value_fingerprints.add(hashlib.sha256(raw).hexdigest())
        stack.extend((child, depth + 1) for child in reversed(children))

    required = {
        "logicTree": 1,
        "logicTreeBranchingLevel": 1,
        "logicTreeBranchSet": 1,
        "logicTreeBranch": 1,
        "uncertaintyModel": 1,
        "uncertaintyWeight": 1,
    }
    for name, minimum in required.items():
        if counts[name] < minimum:
            raise GmpeLogicTreeProfileError(f"missing_required_element:{name}")
    if counts["uncertaintyModel"] != counts["logicTreeBranch"]:
        raise GmpeLogicTreeProfileError("branch_model_cardinality_mismatch")
    if counts["uncertaintyWeight"] != counts["logicTreeBranch"]:
        raise GmpeLogicTreeProfileError("branch_weight_cardinality_mismatch")

    return {
        "schema_version": "oc-esrm20-scenario-v10-greece-gmpe-logic-tree-profile-v1",
        "byte_count": expected_byte_count,
        "sha256": expected_sha256,
        "nrml_namespace": EXPECTED_NRML_NAMESPACE,
        "element_count": element_count,
        "max_depth": max_depth,
        "branching_level_count": counts["logicTreeBranchingLevel"],
        "branch_set_count": counts["logicTreeBranchSet"],
        "branch_count": counts["logicTreeBranch"],
        "uncertainty_model_count": counts["uncertaintyModel"],
        "uncertainty_weight_count": counts["uncertaintyWeight"],
        "non_whitespace_text_element_count": text_element_count,
        "distinct_text_value_fingerprint_count": len(text_value_fingerprints),
        "attribute_name_counts": dict(sorted(attribute_names.items())),
        "raw_model_values_returned": False,
        "gmpe_semantics_verified": False,
        "gmpe_applicability_verified": False,
        "numerical_equivalence_verified": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_fixed_greece_gmpe_logic_tree(data: bytes) -> dict[str, object]:
    """Profile only the exact receipted 6,490-byte Athens GMPE logic-tree object."""
    return _profile_verified(data, expected_byte_count=EXPECTED_BYTE_COUNT, expected_sha256=EXPECTED_SHA256)
