# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed structure profiler for the frozen ESRM20 Kosovo site-model XML.

The public entry point accepts only bytes matching the already-trusted site
receipt. Byte count and SHA-256 are verified before any XML interpretation.
The result deliberately contains structure and lexical fingerprints only: it
never returns provider coordinates/site values and it does not establish CRS,
units, missingness, GSIM sufficiency, publication, or model-use authority.
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from typing import Any

SCHEMA_VERSION = "oc-esrm20-kosovo-site-content-profile-v0"
SOURCE_ISSUE = 291
SOURCE_SCIENCE_ISSUE = 284
RECEIPT_ISSUE = 342
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Vs30/Site_model_Kosovo.xml"
WORKER_OPERATION_ID = "esrm20-kosovo-site-model-v1"
RECEIPT_COMMENT_ID = 5308044390
RECEIPT_EXECUTION_SHA = "25719e731b0224ba4c9a656b1556db6a9fa76de2"
RECEIPT_RETRIEVED_AT = "2026-08-16T14:56:37Z"
EXPECTED_BYTE_COUNT = 5_891
EXPECTED_SHA256 = "746cf75d91507da8b55a9476c61bb5d884eed42c6268a36b1179f432e8850edd"

MAX_XML_BYTES = 1_048_576
MAX_ELEMENTS = 10_000
MAX_DEPTH = 16
MAX_ATTRIBUTES_PER_ELEMENT = 32
MAX_NAME_UTF8_BYTES = 256
MAX_ATTRIBUTE_VALUE_UTF8_BYTES = 4_096
MAX_TEXT_UTF8_BYTES = 4_096
_UTF8_BOM = b"\xef\xbb\xbf"
_XML_DECLARATION_RE = re.compile(
    r"\A<\?xml[ \t\r\n]+version=(?P<q1>[\"'])(?P<version>1\.0)(?P=q1)"
    r"(?:[ \t\r\n]+encoding=(?P<q2>[\"'])(?P<encoding>[A-Za-z][A-Za-z0-9._-]*)(?P=q2))?"
    r"(?:[ \t\r\n]+standalone=(?P<q3>[\"'])(?P<standalone>yes|no)(?P=q3))?"
    r"[ \t\r\n]*\?>"
)


class KosovoSiteProfileError(RuntimeError):
    """Raised when exact-byte verification or bounded XML profiling fails."""


def _require_expected_identity(expected_byte_count: int, expected_sha256: str) -> None:
    if type(expected_byte_count) is not int or isinstance(expected_byte_count, bool):
        raise KosovoSiteProfileError("expected byte count must be an integer")
    if expected_byte_count < 1 or expected_byte_count > MAX_XML_BYTES:
        raise KosovoSiteProfileError("expected byte count is outside bounded policy")
    if (
        type(expected_sha256) is not str
        or len(expected_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_sha256)
    ):
        raise KosovoSiteProfileError("expected SHA-256 must be 64 lowercase hex characters")


def _verify_bytes(raw: bytes, *, expected_byte_count: int, expected_sha256: str) -> None:
    if type(raw) is not bytes:
        raise KosovoSiteProfileError("site-model input must be immutable bytes")
    _require_expected_identity(expected_byte_count, expected_sha256)
    if len(raw) != expected_byte_count:
        raise KosovoSiteProfileError("site-model byte count does not match trusted receipt")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise KosovoSiteProfileError("site-model SHA-256 does not match trusted receipt")


def _validate_xml_declaration(text: str) -> None:
    """Require an optional XML declaration to agree with the UTF-8 byte gate."""

    marker = "<?xml"
    marker_index = text.find(marker)
    if marker_index < 0:
        return
    if marker_index != 0:
        raise KosovoSiteProfileError("XML declaration must appear at the start of the document")

    match = _XML_DECLARATION_RE.match(text)
    if match is None:
        raise KosovoSiteProfileError("XML declaration is malformed or unsupported")
    encoding = match.group("encoding")
    if encoding is not None and encoding.lower() != "utf-8":
        raise KosovoSiteProfileError(
            "XML declaration encoding does not match strict UTF-8"
        )
    if text.find(marker, match.end()) >= 0:
        raise KosovoSiteProfileError("verified XML contains multiple XML declarations")


def _decode_literal_xml(raw: bytes) -> tuple[str, bool]:
    """Establish one literal UTF-8 boundary before any XML parser semantics."""

    bom_present = raw.startswith(_UTF8_BOM)
    codec = "utf-8-sig" if bom_present else "utf-8"
    try:
        text = raw.decode(codec, errors="strict")
    except UnicodeDecodeError as exc:
        raise KosovoSiteProfileError("verified XML is not strict UTF-8") from exc
    if "\x00" in text:
        raise KosovoSiteProfileError("verified XML contains NUL characters")
    upper = text.upper()
    if "<!DOCTYPE" in upper or "<!ENTITY" in upper:
        raise KosovoSiteProfileError("verified XML unexpectedly declares a DTD or entity")
    _validate_xml_declaration(text)
    return text, bom_present


def _split_qname(name: object) -> tuple[str | None, str]:
    if type(name) is not str or not name:
        raise KosovoSiteProfileError("verified XML contains a non-string or empty name")
    encoded = name.encode("utf-8")
    if len(encoded) > MAX_NAME_UTF8_BYTES:
        raise KosovoSiteProfileError("verified XML name exceeds bounded policy")
    if name.startswith("{"):
        close = name.find("}")
        if close <= 1 or close == len(name) - 1:
            raise KosovoSiteProfileError("verified XML contains a malformed qualified name")
        return name[1:close], name[close + 1 :]
    return None, name


def _qname_profile(name: str) -> dict[str, str | None]:
    namespace, local_name = _split_qname(name)
    return {"namespace": namespace, "local_name": local_name}


def _value_set_sha256(values: set[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(values):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _decimal_lexical_count(values: list[str]) -> int:
    count = 0
    for value in values:
        if not value or value != value.strip():
            continue
        try:
            number = Decimal(value)
        except InvalidOperation:
            continue
        if number.is_finite():
            count += 1
    return count


def _depth(root: ET.Element) -> int:
    maximum = 0
    stack: list[tuple[ET.Element, int]] = [(root, 1)]
    while stack:
        element, depth = stack.pop()
        maximum = max(maximum, depth)
        if maximum > MAX_DEPTH:
            raise KosovoSiteProfileError("verified XML nesting exceeds bounded policy")
        stack.extend((child, depth + 1) for child in list(element))
    return maximum


def profile_verified_xml_bytes(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, Any]:
    """Verify identity first, then emit bounded structure-only XML evidence."""

    _verify_bytes(
        raw,
        expected_byte_count=expected_byte_count,
        expected_sha256=expected_sha256,
    )
    text, bom_present = _decode_literal_xml(raw)

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise KosovoSiteProfileError("verified site-model XML is malformed") from exc

    elements = list(root.iter())
    if not elements or len(elements) > MAX_ELEMENTS:
        raise KosovoSiteProfileError("verified XML element count is outside bounded policy")

    max_depth = _depth(root)
    tag_counts: Counter[str] = Counter()
    namespace_counts: Counter[str] = Counter()
    attribute_values: dict[str, list[str]] = defaultdict(list)
    non_whitespace_text_element_count = 0
    leaf_element_count = 0

    for element in elements:
        namespace, local_name = _split_qname(element.tag)
        canonical_tag = f"{{{namespace}}}{local_name}" if namespace is not None else local_name
        tag_counts[canonical_tag] += 1
        if namespace is not None:
            namespace_counts[namespace] += 1
        if len(element.attrib) > MAX_ATTRIBUTES_PER_ELEMENT:
            raise KosovoSiteProfileError("verified XML attribute count exceeds bounded policy")
        if not list(element):
            leaf_element_count += 1

        element_text = element.text or ""
        if element_text.strip():
            if len(element_text.encode("utf-8")) > MAX_TEXT_UTF8_BYTES:
                raise KosovoSiteProfileError("verified XML element text exceeds bounded policy")
            non_whitespace_text_element_count += 1
        tail = element.tail or ""
        if tail.strip() and len(tail.encode("utf-8")) > MAX_TEXT_UTF8_BYTES:
            raise KosovoSiteProfileError("verified XML element tail exceeds bounded policy")

        for raw_name, value in element.attrib.items():
            attr_namespace, attr_local_name = _split_qname(raw_name)
            canonical_attr = (
                f"{{{attr_namespace}}}{attr_local_name}"
                if attr_namespace is not None
                else attr_local_name
            )
            if type(value) is not str:
                raise KosovoSiteProfileError("verified XML contains a non-string attribute value")
            if len(value.encode("utf-8")) > MAX_ATTRIBUTE_VALUE_UTF8_BYTES:
                raise KosovoSiteProfileError("verified XML attribute value exceeds bounded policy")
            attribute_values[canonical_attr].append(value)

    attribute_profiles: list[dict[str, Any]] = []
    for name in sorted(attribute_values):
        values = attribute_values[name]
        distinct = set(values)
        attribute_profiles.append(
            {
                "name": _qname_profile(name),
                "occurrence_count": len(values),
                "empty_count": sum(value == "" for value in values),
                "leading_or_trailing_whitespace_count": sum(
                    value != value.strip() for value in values if value != ""
                ),
                "distinct_count": len(distinct),
                "exact_value_set_sha256": _value_set_sha256(distinct),
                "finite_decimal_lexical_count": _decimal_lexical_count(values),
                "true_lexical_count": sum(value == "true" for value in values),
                "false_lexical_count": sum(value == "false" for value in values),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "parser": {
            "xml_parser": "strict-utf8-text->xml.etree.ElementTree.fromstring",
            "verified_encoding": "utf-8",
            "bom_present": bom_present,
            "dtd_or_entity_allowed": False,
        },
        "root": _qname_profile(root.tag),
        "element_count": len(elements),
        "leaf_element_count": leaf_element_count,
        "max_depth": max_depth,
        "tag_counts": [
            {"name": _qname_profile(name), "count": count}
            for name, count in sorted(tag_counts.items())
        ],
        "namespace_counts": [
            {"namespace": namespace, "element_count": count}
            for namespace, count in sorted(namespace_counts.items())
        ],
        "attribute_profiles": attribute_profiles,
        "non_whitespace_text_element_count": non_whitespace_text_element_count,
        "raw_xml_returned": False,
        "raw_attribute_values_returned": False,
        "crs_coordinate_semantics_verified": False,
        "site_parameter_units_verified": False,
        "missingness_semantics_verified": False,
        "gsim_site_parameter_sufficiency_verified": False,
        "site_adjusted_reference_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_verified_kosovo_site_model(raw: bytes) -> dict[str, Any]:
    """Profile only the exact bytes bound by the trusted Kosovo site receipt."""

    profile = profile_verified_xml_bytes(
        raw,
        expected_byte_count=EXPECTED_BYTE_COUNT,
        expected_sha256=EXPECTED_SHA256,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "source_science_issue": SOURCE_SCIENCE_ISSUE,
        "receipt_issue": RECEIPT_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "worker_operation_id": WORKER_OPERATION_ID,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
        "receipt_retrieved_at": RECEIPT_RETRIEVED_AT,
        "byte_count": EXPECTED_BYTE_COUNT,
        "sha256": EXPECTED_SHA256,
        "profile": profile,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
