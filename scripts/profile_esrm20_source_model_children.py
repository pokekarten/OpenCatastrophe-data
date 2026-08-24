# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile exact receipted ESRM20 source-model XML without publishing provider bytes.

This module is intentionally transport-free. A trusted-main executor may supply bytes only
for the ten immutable objects below. Each object is byte-verified before XML parsing.
The result exposes bounded structural metadata only; it does not infer nested dependency
syntax, runtime compatibility, publication authority, or model-use fitness.
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
MAX_SOURCES_PER_FILE = 250_000
MAX_TRT_CHARS = 256
MAX_UNIQUE_TRTS_PER_FILE = 64
SUPPORTED_NRML_NAMESPACES = frozenset(
    {
        "http://openquake.org/xmlns/nrml/0.4",
        "http://openquake.org/xmlns/nrml/0.5",
    }
)
SUPPORTED_SOURCE_TYPES = frozenset(
    {
        "areaSource",
        "pointSource",
        "multiPointSource",
        "simpleFaultSource",
        "kiteFaultSource",
        "complexFaultSource",
        "characteristicFaultSource",
        "nonParametricSeismicSource",
        "multiFaultSource",
    }
)
TRT_PROVENANCE_TYPES = frozenset(
    {"direct_source", "group_inherited", "group_effective_direct_confirmed"}
)
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


def _split_tag(tag: object) -> tuple[str, str]:
    if type(tag) is not str or not tag.startswith("{") or "}" not in tag:
        raise SourceModelContentProfileError(
            "source-model XML must use an explicit supported NRML namespace"
        )
    namespace, local = tag[1:].split("}", 1)
    if namespace not in SUPPORTED_NRML_NAMESPACES or not local:
        raise SourceModelContentProfileError("source-model XML uses an unsupported NRML tag")
    return namespace, local


def _local_name_in_namespace(tag: object, namespace: str) -> str:
    observed_namespace, local = _split_tag(tag)
    if observed_namespace != namespace:
        raise SourceModelContentProfileError(
            "source-model structural element namespace does not match root NRML namespace"
        )
    return local


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


def _safe_trt(value: object, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise SourceModelContentProfileError(f"{field} is missing or not canonical")
    if len(value) > MAX_TRT_CHARS:
        raise SourceModelContentProfileError(f"{field} exceeds bounds")
    if not value.isprintable() or any(ord(char) == 127 for char in value):
        raise SourceModelContentProfileError(f"{field} contains controls")
    return value


def _record_source(
    node: ET.Element,
    *,
    namespace: str,
    group_trt: str | None,
    trt_counts: Counter[str],
    provenance_counts: Counter[str],
) -> None:
    source_type = _local_name_in_namespace(node.tag, namespace)
    if source_type not in SUPPORTED_SOURCE_TYPES:
        raise SourceModelContentProfileError(
            f"unsupported source-model child element: {source_type}"
        )
    for descendant in list(node.iter())[1:]:
        descendant_local = _local_name_in_namespace(descendant.tag, namespace)
        if (
            descendant_local == "sourceGroup"
            or descendant_local in SUPPORTED_SOURCE_TYPES
            or descendant_local.endswith("Source")
        ):
            raise SourceModelContentProfileError(
                "nested source/sourceGroup structure is unsupported"
            )

    direct = node.attrib.get("tectonicRegion")
    if group_trt is None:
        effective = _safe_trt(direct, "source tectonicRegion")
        provenance = "direct_source"
    else:
        effective = group_trt
        if direct is None:
            provenance = "group_inherited"
        else:
            direct_trt = _safe_trt(direct, "source tectonicRegion")
            if direct_trt != group_trt:
                raise SourceModelContentProfileError(
                    "source tectonicRegion conflicts with sourceGroup tectonicRegion"
                )
            provenance = "group_effective_direct_confirmed"

    trt_counts[effective] += 1
    provenance_counts[provenance] += 1
    source_count = sum(trt_counts.values())
    if source_count > MAX_SOURCES_PER_FILE:
        raise SourceModelContentProfileError("source count exceeds bounds")
    if len(trt_counts) > MAX_UNIQUE_TRTS_PER_FILE:
        raise SourceModelContentProfileError("tectonic-region count exceeds bounds")


def _profile_trt_structure(root: ET.Element) -> tuple[dict[str, int], dict[str, int]]:
    namespace, root_local = _split_tag(root.tag)
    if root_local != "nrml":
        raise SourceModelContentProfileError("source-model root must be nrml")
    children = list(root)
    if (
        len(children) != 1
        or _local_name_in_namespace(children[0].tag, namespace) != "sourceModel"
    ):
        raise SourceModelContentProfileError("nrml must contain exactly one sourceModel")
    source_model = children[0]
    direct_children = list(source_model)
    if not direct_children:
        raise SourceModelContentProfileError("sourceModel contains no sources")

    trt_counts: Counter[str] = Counter()
    provenance_counts: Counter[str] = Counter()
    child_tags = [
        _local_name_in_namespace(child.tag, namespace) for child in direct_children
    ]
    group_flags = [tag == "sourceGroup" for tag in child_tags]
    if any(group_flags) and not all(group_flags):
        raise SourceModelContentProfileError(
            "sourceModel mixes sourceGroup and direct source children"
        )

    if all(group_flags):
        for group in direct_children:
            group_trt = _safe_trt(
                group.attrib.get("tectonicRegion"), "sourceGroup tectonicRegion"
            )
            group_children = list(group)
            if not group_children:
                raise SourceModelContentProfileError("sourceGroup contains no sources")
            for source_node in group_children:
                _record_source(
                    source_node,
                    namespace=namespace,
                    group_trt=group_trt,
                    trt_counts=trt_counts,
                    provenance_counts=provenance_counts,
                )
    else:
        for source_node in direct_children:
            _record_source(
                source_node,
                namespace=namespace,
                group_trt=None,
                trt_counts=trt_counts,
                provenance_counts=provenance_counts,
            )

    if not trt_counts or sum(trt_counts.values()) != sum(provenance_counts.values()):
        raise SourceModelContentProfileError("source TRT counts do not reconcile")
    return dict(sorted(trt_counts.items())), dict(sorted(provenance_counts.items()))


def profile_source_model(path: str, payload: bytes) -> dict[str, Any]:
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
    counts: Counter[str] = Counter()
    element_count = 0
    for element in root.iter():
        element_count += 1
        if element_count > MAX_ELEMENTS:
            raise SourceModelContentProfileError("source-model XML exceeds element bound")
        if type(element.tag) is not str:
            raise SourceModelContentProfileError("source-model XML contains unsupported node type")
        _, local = _split_tag(element.tag)
        counts[local] += 1
    trt_counts, provenance_counts = _profile_trt_structure(root)
    return {
        "repository_path": path,
        "byte_count": expected_count,
        "sha256": expected_sha256,
        "root_element": _split_tag(root.tag)[1],
        "element_count": element_count,
        "element_type_counts": dict(sorted(counts.items())),
        "tectonic_region_type_counts": trt_counts,
        "trt_provenance_counts": provenance_counts,
        "byte_identity_verified": True,
        "source_model_content_profiled": True,
        "external_reference_scan_performed": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
