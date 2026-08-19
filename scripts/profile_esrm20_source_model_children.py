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
    declaration = _ENCODING_RE.search(text[:512])
    if declaration is not None and declaration.group(1).casefold().replace("_", "-") not in {
        "utf-8",
        "utf8",
    }:
        raise SourceModelContentProfileError("source-model XML declares a non-UTF-8 encoding")
    if _DTD_RE.search(text) is not None:
        raise SourceModelContentProfileError("DTD/entity declarations are not accepted")
    return text


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
