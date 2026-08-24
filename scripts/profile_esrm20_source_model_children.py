# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile exact receipted ESRM20 source-model XML without publishing provider bytes.

This module is intentionally transport-free. A trusted-main executor may supply bytes only
for the ten immutable objects below. Each object is byte-verified before XML parsing.
The existing structural profile remains stable; the bounded tectonic-region helper exposes
only effective ``tectonicRegion`` counts and declaration provenance. Neither path infers
runtime compatibility, publication authority, or model-use fitness.
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from collections import Counter
from typing import Any

PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
RECEIPT_RESULT_COMMENT_ID = 5312851239
RECEIPT_SET_SHA256 = "621d16b35166cb66c86079106f1a7fd717ff07ef155184c5eed5a028292e4eb8"
MAX_XML_BYTES = 128 * 1024 * 1024
MAX_ELEMENTS = 2_000_000
MAX_TECTONIC_REGION_UTF8_BYTES = 256
_DTD_RE = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)
_ENCODING_RE = re.compile(r"<\?xml\s+[^>]*encoding\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)

# Immutable byte identities from trusted-main #481 receipt PASS 5312851239.
RECEIPTS = {
    "Hazard/source_models/asm_v12e/asm_ver12e_winGT_fs017_combined.xml": (589089, "32dfcefff8acbedabf4fa6d87ce8694ff2dd7b662f5d75c5ea06a2156a6b2aef"),
    "Hazard/source_models/asm_v12e/asm_ver12e_winGT_fs017_twingr.xml": (5258, "a68c60d8d9c1b7eb43031707b55e327060ce875280d7ba719c038cba1f5c5e21"),
    "Hazard/source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_combined.xml": (21717, "9eba3d104a2f62926c3a06415abfc30f2992fe8c00c7207c5c947b45f18b2015"),
    "Hazard/source_models/fsm_v09/fs_ver09e_model_aGR_fMthr_combined.xml": (1266236, "1500111cc0d9f698a3e3cb25f97cebd76f897f6926a736c3ea1e37239741650c"),
    "Hazard/source_models/interface_v12b/CaA_IF2222222_M40.xml": (10493, "85412e58d54bbfa54b5c2843696fcd801d2e99fed80b1030ab38580d0cfd5900"),
    "Hazard/source_models/interface_v12b/CyA_IF2222222_M40.xml": (13217, "16c89632509d5879179c2c5ca3fa9103420804eebe758b057e8af9f7b518e540"),
    "Hazard/source_models/interface_v12b/GiA_IF2222222_M40.xml": (11621, "99266f057d2e271648ed974cc3d1eea14c2e6d4606525f2b6d5972be085e610d"),
    "Hazard/source_models/interface_v12b/HeA_IF2222222_M40.xml": (39917, "b776f45385e30e492c921de4db4712e51654864cc3f1360e0157e2a562f4368d"),
    "Hazard/source_models/ssm_v09/seis_ver12b_fMthr_asm_ver12e_winGT_fs017_agbrs_point.xml": (21820451, "78818fcf6da94ae11b0104663334f79def9a1953cb127312c9c52bffb02fbe93"),
    "Hazard/source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_combined.xml": (3486, "6d4ceabef24b94b3ca48733879043d977d2e97455e5ae26d2c6b4f3a5a746c50"),
}


class SourceModelContentProfileError(RuntimeError):
    """Fail-closed error for exact source-model content profiling."""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _decode_xml_utf8(payload: bytes) -> str:
    try:
        text = payload.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise SourceModelContentProfileError("source-model XML must be UTF-8") from exc
    if "\x00" in text:
        raise SourceModelContentProfileError("source-model XML contains NUL characters")
    declaration = _ENCODING_RE.match(text)
    if declaration is not None and declaration.group(1).casefold().replace("_", "-") not in {
        "utf-8",
        "utf8",
    }:
        raise SourceModelContentProfileError("source-model XML declares a non-UTF-8 encoding")
    if _DTD_RE.search(text) is not None:
        raise SourceModelContentProfileError("DTD/entity declarations are not accepted")
    return text


def _verified_root(path: str, payload: bytes) -> tuple[int, str, ET.Element]:
    if path not in RECEIPTS:
        raise SourceModelContentProfileError("source-model path is outside exact receipt set")
    if type(payload) is not bytes:
        raise SourceModelContentProfileError("source-model payload must be bytes")
    expected_count, expected_sha256 = RECEIPTS[path]
    if len(payload) != expected_count or len(payload) > MAX_XML_BYTES:
        raise SourceModelContentProfileError("source-model byte count disagrees with receipt")
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise SourceModelContentProfileError("source-model SHA-256 disagrees with receipt")
    text = _decode_xml_utf8(payload)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise SourceModelContentProfileError("source-model XML is not well formed") from exc
    return expected_count, expected_sha256, root


def _is_source_node(element: ET.Element) -> bool:
    if type(element.tag) is not str:
        raise SourceModelContentProfileError("source-model XML contains unsupported node type")
    name = _local_name(element.tag)
    return name.endswith("Source") and name != "sourceModel"


def _validated_tectonic_region(value: str | None, *, owner: str) -> str:
    if value is None:
        raise SourceModelContentProfileError(f"{owner} tectonicRegion is missing")
    if not value or value != value.strip():
        raise SourceModelContentProfileError(
            f"{owner} tectonicRegion must be non-empty and trimmed"
        )
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        raise SourceModelContentProfileError(f"{owner} tectonicRegion contains control characters")
    if len(value.encode("utf-8")) > MAX_TECTONIC_REGION_UTF8_BYTES:
        raise SourceModelContentProfileError(f"{owner} tectonicRegion exceeds byte bound")
    return value


def _assert_no_nested_sources(source: ET.Element) -> None:
    for descendant in source.iter():
        if descendant is source:
            continue
        if type(descendant.tag) is not str:
            raise SourceModelContentProfileError("source-model XML contains unsupported node type")
        name = _local_name(descendant.tag)
        if name == "sourceGroup" or _is_source_node(descendant):
            raise SourceModelContentProfileError("source-model contains unsupported source nesting")


def _tectonic_region_profile(root: ET.Element) -> tuple[int, dict[str, int], dict[str, int]]:
    source_models = [
        element
        for element in root.iter()
        if type(element.tag) is str and _local_name(element.tag) == "sourceModel"
    ]
    if len(source_models) != 1:
        raise SourceModelContentProfileError("source-model XML must contain exactly one sourceModel")

    effective: Counter[str] = Counter()
    provenance: Counter[str] = Counter()
    source_count = 0

    def record(source: ET.Element, group_trt: str | None) -> None:
        nonlocal source_count
        _assert_no_nested_sources(source)
        direct_raw = source.attrib.get("tectonicRegion")
        if group_trt is None:
            trt = _validated_tectonic_region(direct_raw, owner="source")
            provenance["direct"] += 1
        elif direct_raw is None:
            trt = group_trt
            provenance["source_group"] += 1
        else:
            direct_trt = _validated_tectonic_region(direct_raw, owner="source")
            if direct_trt != group_trt:
                raise SourceModelContentProfileError(
                    "source tectonicRegion conflicts with sourceGroup tectonicRegion"
                )
            trt = direct_trt
            provenance["direct_and_source_group"] += 1
        effective[trt] += 1
        source_count += 1

    source_model = source_models[0]
    for child in source_model:
        if type(child.tag) is not str:
            raise SourceModelContentProfileError("source-model XML contains unsupported node type")
        name = _local_name(child.tag)
        if name == "sourceGroup":
            group_trt = _validated_tectonic_region(
                child.attrib.get("tectonicRegion"), owner="sourceGroup"
            )
            group_source_count = 0
            for source in child:
                if not _is_source_node(source):
                    raise SourceModelContentProfileError(
                        "sourceGroup contains unsupported non-source child"
                    )
                record(source, group_trt)
                group_source_count += 1
            if group_source_count == 0:
                raise SourceModelContentProfileError("sourceGroup contains no source nodes")
        elif _is_source_node(child):
            record(child, None)
        else:
            raise SourceModelContentProfileError("sourceModel contains unsupported child nesting")

    if source_count == 0:
        raise SourceModelContentProfileError("sourceModel contains no source nodes")
    provenance_counts = {
        key: provenance[key]
        for key in ("direct", "source_group", "direct_and_source_group")
    }
    if sum(effective.values()) != source_count or sum(provenance_counts.values()) != source_count:
        raise SourceModelContentProfileError("tectonic-region source counts do not reconcile")
    return source_count, dict(sorted(effective.items())), provenance_counts


def profile_source_model(path: str, payload: bytes) -> dict[str, Any]:
    expected_count, expected_sha256, root = _verified_root(path, payload)
    counts: Counter[str] = Counter()
    element_count = 0
    for element in root.iter():
        element_count += 1
        if element_count > MAX_ELEMENTS:
            raise SourceModelContentProfileError("source-model XML exceeds element bound")
        if type(element.tag) is not str:
            raise SourceModelContentProfileError("source-model XML contains unsupported node type")
        counts[_local_name(element.tag)] += 1
    return {
        "repository_path": path,
        "byte_count": expected_count,
        "sha256": expected_sha256,
        "root_element": _local_name(root.tag),
        "element_count": element_count,
        "element_type_counts": dict(sorted(counts.items())),
        "byte_identity_verified": True,
        "source_model_content_profiled": True,
        "external_reference_scan_performed": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_source_model_tectonic_regions(path: str, payload: bytes) -> dict[str, Any]:
    """Return bounded effective TRT counts for one exact receipted source-model child."""

    expected_count, expected_sha256, root = _verified_root(path, payload)
    source_count, effective_counts, provenance_counts = _tectonic_region_profile(root)
    return {
        "repository_path": path,
        "byte_count": expected_count,
        "sha256": expected_sha256,
        "source_count": source_count,
        "effective_tectonic_region_counts": effective_counts,
        "tectonic_region_provenance_counts": provenance_counts,
        "byte_identity_verified": True,
        "source_model_tectonic_region_profiled": True,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
