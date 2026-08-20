# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed structural profiler for the receipted ESRM20 v1.0 Greece rupture.

This module performs no network I/O.  It accepts only the exact byte object already
receipted on trusted main for #285 and returns bounded structural facts.  The result
is deliberately not an event-location, validation, holdout, publication, or model-use
assertion.
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from typing import Final

_CANONICAL_EXPECTED_BYTE_COUNT: Final = 666
_CANONICAL_EXPECTED_SHA256: Final = "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b"
_CANONICAL_EXPECTED_NRML_NAMESPACE: Final = "http://openquake.org/xmlns/nrml/0.5"
_CANONICAL_OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS: Final = frozenset(
    {
        "simpleFaultRupture",
        "complexFaultRupture",
        "singlePlaneRupture",
        "multiPlanesRupture",
        "griddedRupture",
    }
)
_CANONICAL_MAX_ELEMENTS: Final = 64
_CANONICAL_MAX_DEPTH: Final = 12

EXPECTED_BYTE_COUNT: Final = _CANONICAL_EXPECTED_BYTE_COUNT
EXPECTED_SHA256: Final = _CANONICAL_EXPECTED_SHA256
EXPECTED_NRML_NAMESPACE: Final = _CANONICAL_EXPECTED_NRML_NAMESPACE
OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS: Final = (
    _CANONICAL_OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS
)
MAX_ELEMENTS: Final = _CANONICAL_MAX_ELEMENTS
MAX_DEPTH: Final = _CANONICAL_MAX_DEPTH
_LOCAL_NAME_RE: Final = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
_XML_DECL_RE: Final = re.compile(r"^\s*<\?xml\s+([^?]*)\?>", re.IGNORECASE)
_ENCODING_RE: Final = re.compile(r"\bencoding\s*=\s*(['\"])([^'\"]+)\1", re.IGNORECASE)
_FORBIDDEN_DECL_RE: Final = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)


class RuptureProfileError(ValueError):
    """The fixed rupture object failed an identity or structural boundary."""


def _require_canonical_authority() -> None:
    identities = (
        (EXPECTED_BYTE_COUNT, _CANONICAL_EXPECTED_BYTE_COUNT, "byte_count"),
        (EXPECTED_SHA256, _CANONICAL_EXPECTED_SHA256, "sha256"),
        (EXPECTED_NRML_NAMESPACE, _CANONICAL_EXPECTED_NRML_NAMESPACE, "nrml_namespace"),
        (
            OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS,
            _CANONICAL_OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS,
            "rupture_elements",
        ),
        (MAX_ELEMENTS, _CANONICAL_MAX_ELEMENTS, "max_elements"),
        (MAX_DEPTH, _CANONICAL_MAX_DEPTH, "max_depth"),
    )
    for observed, expected, label in identities:
        if type(observed) is not type(expected) or observed != expected:
            raise RuptureProfileError(f"production_authority_drift:{label}")


def _split_tag(tag: str) -> tuple[str, str]:
    if not isinstance(tag, str):
        raise RuptureProfileError("non_text_xml_tag")
    if tag.startswith("{"):
        end = tag.find("}")
        if end <= 1:
            raise RuptureProfileError("malformed_expanded_xml_name")
        namespace, local = tag[1:end], tag[end + 1 :]
    else:
        namespace, local = "", tag
    if not _LOCAL_NAME_RE.fullmatch(local):
        raise RuptureProfileError("unsafe_xml_local_name")
    return namespace, local


def _decode_xml(data: bytes) -> str:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise RuptureProfileError("non_utf8_xml_encoding")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RuptureProfileError("invalid_utf8_xml") from exc
    declaration = _XML_DECL_RE.match(text)
    if declaration:
        encoding = _ENCODING_RE.search(declaration.group(1))
        if encoding and encoding.group(2).strip().lower().replace("_", "-") not in {
            "utf-8",
            "utf8",
        }:
            raise RuptureProfileError("xml_encoding_declaration_mismatch")
    if _FORBIDDEN_DECL_RE.search(text):
        raise RuptureProfileError("dtd_or_entity_forbidden")
    return text


def _walk(
    root: ET.Element,
    *,
    expected_namespace: str,
    max_elements: int,
    max_depth: int,
) -> tuple[int, int, dict[str, int]]:
    count = 0
    observed_max_depth = 0
    local_counts: dict[str, int] = {}
    stack: list[tuple[ET.Element, int]] = [(root, 1)]
    while stack:
        element, depth = stack.pop()
        count += 1
        if count > max_elements:
            raise RuptureProfileError("xml_element_limit_exceeded")
        if depth > max_depth:
            raise RuptureProfileError("xml_depth_limit_exceeded")
        observed_max_depth = max(observed_max_depth, depth)
        namespace, local = _split_tag(element.tag)
        if namespace != expected_namespace:
            raise RuptureProfileError("foreign_xml_namespace")
        local_counts[local] = local_counts.get(local, 0) + 1
        children = list(element)
        stack.extend((child, depth + 1) for child in reversed(children))
    return count, observed_max_depth, local_counts


def _profile_verified_greece_rupture(
    data: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
    expected_namespace: str,
    allowed_rupture_elements: frozenset[str],
    max_elements: int = _CANONICAL_MAX_ELEMENTS,
    max_depth: int = _CANONICAL_MAX_DEPTH,
) -> dict[str, object]:
    """Private injection seam for already-bound bytes and parser tests."""
    if type(data) is not bytes:
        raise TypeError("data must be bytes")
    if len(data) != expected_byte_count:
        raise RuptureProfileError("byte_count_mismatch")
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise RuptureProfileError("sha256_mismatch")

    text = _decode_xml(data)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise RuptureProfileError("invalid_xml") from exc

    root_namespace, root_local = _split_tag(root.tag)
    if root_namespace != expected_namespace or root_local != "nrml":
        raise RuptureProfileError("unexpected_nrml_root")
    children = list(root)
    if len(children) != 1:
        raise RuptureProfileError("rupture_top_level_cardinality")
    rupture_namespace, rupture_local = _split_tag(children[0].tag)
    if rupture_namespace != expected_namespace:
        raise RuptureProfileError("foreign_rupture_namespace")
    if rupture_local not in allowed_rupture_elements:
        raise RuptureProfileError("unsupported_rupture_element")

    element_count, observed_max_depth, local_counts = _walk(
        root,
        expected_namespace=expected_namespace,
        max_elements=max_elements,
        max_depth=max_depth,
    )
    return {
        "schema_version": "oc-esrm20-scenario-v10-greece-rupture-profile-v1",
        "byte_count": expected_byte_count,
        "sha256": expected_sha256,
        "nrml_namespace": expected_namespace,
        "rupture_element_local_name": rupture_local,
        "element_count": element_count,
        "max_depth": observed_max_depth,
        "magnitude_element_count": local_counts.get("magnitude", 0),
        "rake_element_count": local_counts.get("rake", 0),
        "hypocenter_element_count": local_counts.get("hypocenter", 0),
        "provider_file_content_profiled": True,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_fixed_greece_rupture(data: bytes) -> dict[str, object]:
    """Return bounded structure for the exact receipted 666-byte rupture object."""
    _require_canonical_authority()
    return _profile_verified_greece_rupture(
        data,
        expected_byte_count=_CANONICAL_EXPECTED_BYTE_COUNT,
        expected_sha256=_CANONICAL_EXPECTED_SHA256,
        expected_namespace=_CANONICAL_EXPECTED_NRML_NAMESPACE,
        allowed_rupture_elements=_CANONICAL_OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS,
        max_elements=_CANONICAL_MAX_ELEMENTS,
        max_depth=_CANONICAL_MAX_DEPTH,
    )
