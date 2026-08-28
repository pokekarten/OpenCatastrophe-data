# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Test one bounded numerical explanation for Kosovo source/runtime exposure drift.

The existing trusted comparison proves that the frozen project-186 source exposure
and project-269 OpenQuake runtime exposure have the same 1,093-row lexical bridge,
while a small number of values differ in five numeric field pairs.  This module
tests one explicit hypothesis only: parse each source numeric token as IEEE-754
binary64 using Python's correctly-rounded ``float`` conversion, render that value
with Python's shortest round-trip ``repr`` form, and compare the resulting Decimal
value with the corresponding runtime token.

A PASS-like all-match result is deliberately only *numerical consistency* with that
projection.  It does not prove that EFEHR used Python, binary64, ``repr``, pandas,
or any particular generator; it does not establish transform lineage, semantic
field equivalence, publication authority, or model-use authority.

Provider rows and raw numeric values are never returned.  The caller supplies the
already-receipted byte objects; this module performs no network access or writes.
"""

from __future__ import annotations

import hashlib
import math
from decimal import Decimal, InvalidOperation
from typing import Any

from scripts import compare_esrm20_kosovo_exposure_runtime as comparison

SCHEMA_VERSION = "oc-esrm20-kosovo-source-runtime-binary64-profile-v1"
HYPOTHESIS_ID = "python-binary64-shortest-roundtrip-decimal-v1"

_PROJECTION_DOMAIN = b"OpenCatastrophe/EQ1/KosovoExposureBinary64Projection/v1\x00"


class KosovoBinary64ProjectionError(RuntimeError):
    """The bounded binary64 projection diagnostic cannot be established safely."""


def _project_source_token(value: str, *, field: str) -> tuple[Decimal, str]:
    """Return shortest binary64 round-trip Decimal plus exact binary64 hex text."""

    if type(value) is not str or not value:
        raise KosovoBinary64ProjectionError(f"invalid source token for {field}")
    try:
        parsed = float(value)
    except (ValueError, OverflowError) as exc:
        raise KosovoBinary64ProjectionError(
            f"source token is not finite binary64-compatible Decimal for {field}"
        ) from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise KosovoBinary64ProjectionError(
            f"source token is not finite non-negative binary64 for {field}"
        )
    rendered = repr(parsed)
    try:
        projected = Decimal(rendered)
    except InvalidOperation as exc:  # pragma: no cover - defensive against runtime drift
        raise KosovoBinary64ProjectionError(
            f"binary64 shortest representation is not Decimal for {field}"
        ) from exc
    if not projected.is_finite() or projected < 0:
        raise KosovoBinary64ProjectionError(
            f"binary64 shortest representation is invalid for {field}"
        )
    return projected, parsed.hex()


def _projection_fingerprint(
    rows: list[tuple[tuple[str, ...], Decimal, Decimal, str]],
) -> str:
    """Bind projected/runtime relations without exposing provider values."""

    digest = hashlib.sha256()
    digest.update(_PROJECTION_DOMAIN)
    framed: list[tuple[bytes, bytes, bytes, bytes]] = []
    seen: dict[bytes, tuple[str, ...]] = {}
    for key, projected, runtime, binary64_hex in rows:
        key_digest = comparison._framed_digest(comparison._KEY_DIGEST_DOMAIN, key)
        previous = seen.get(key_digest)
        if previous is not None and previous != key:
            raise KosovoBinary64ProjectionError("SHA-256 collision in projection key")
        seen[key_digest] = key
        projected_text = comparison.source_value._canonical_decimal(projected).encode("ascii")
        runtime_text = comparison.source_value._canonical_decimal(runtime).encode("ascii")
        hex_text = binary64_hex.encode("ascii")
        framed.append((key_digest, projected_text, runtime_text, hex_text))

    for key_digest, projected_text, runtime_text, hex_text in sorted(
        framed, key=lambda item: item[0]
    ):
        digest.update(key_digest)
        for value in (projected_text, runtime_text, hex_text):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
    return digest.hexdigest()


def profile_verified_exposure_binary64_projection(
    source_raw: bytes,
    runtime_raw: bytes,
    *,
    source_expected_byte_count: int = comparison.source_profile.EXPECTED_BYTE_COUNT,
    source_expected_sha256: str = comparison.source_profile.EXPECTED_SHA256,
    runtime_expected_byte_count: int = comparison.runtime_profile.EXPECTED_BYTE_COUNT,
    runtime_expected_sha256: str = comparison.runtime_profile.EXPECTED_SHA256,
) -> dict[str, Any]:
    """Test the predeclared binary64 projection against two verified CSV byte objects."""

    source_rows = comparison._parse_verified_rows(
        source_raw,
        expected_byte_count=source_expected_byte_count,
        expected_sha256=source_expected_sha256,
        expected_header=comparison.SOURCE_HEADER,
        label="source exposure",
    )
    runtime_rows = comparison._parse_verified_rows(
        runtime_raw,
        expected_byte_count=runtime_expected_byte_count,
        expected_sha256=runtime_expected_sha256,
        expected_header=comparison.RUNTIME_HEADER,
        label="runtime exposure",
    )

    source_fields = tuple(source for source, _runtime in comparison.KEY_FIELD_PAIRS)
    runtime_fields = tuple(runtime for _source, runtime in comparison.KEY_FIELD_PAIRS)
    source_bridge = comparison._build_unique_bridge(
        source_rows, fields=source_fields, label="source"
    )
    runtime_bridge = comparison._build_unique_bridge(
        runtime_rows, fields=runtime_fields, label="runtime"
    )
    source_keys = set(source_bridge)
    runtime_keys = set(runtime_bridge)
    if source_keys != runtime_keys:
        raise KosovoBinary64ProjectionError("source/runtime comparison key sets differ")
    key_set_sha256 = comparison._keyset_sha256(source_keys)

    field_results: list[dict[str, Any]] = []
    for source_field, runtime_field in comparison.NUMERIC_FIELD_PAIRS:
        exact_equal_count = 0
        projection_match_count = 0
        relation_rows: list[tuple[tuple[str, ...], Decimal, Decimal, str]] = []
        for key in source_bridge:
            try:
                source_number = comparison.source_value._parse_decimal(
                    source_bridge[key][source_field], field=source_field
                )
                runtime_number = comparison.source_value._parse_decimal(
                    runtime_bridge[key][runtime_field], field=runtime_field
                )
            except comparison.source_value.ExposureValueSpatialProfileError as exc:
                raise KosovoBinary64ProjectionError(
                    f"numeric parse failed at {source_field}->{runtime_field}"
                ) from exc

            projected, binary64_hex = _project_source_token(
                source_bridge[key][source_field], field=source_field
            )
            exact_equal_count += int(source_number == runtime_number)
            projection_match_count += int(projected == runtime_number)
            relation_rows.append((key, projected, runtime_number, binary64_hex))

        record_count = len(source_bridge)
        field_results.append(
            {
                "source_field": source_field,
                "runtime_field": runtime_field,
                "record_count": record_count,
                "source_runtime_exact_equal_count": exact_equal_count,
                "binary64_projection_match_count": projection_match_count,
                "binary64_projection_mismatch_count": record_count - projection_match_count,
                "all_runtime_values_match_binary64_projection": (
                    projection_match_count == record_count
                ),
                "projection_relation_sha256": _projection_fingerprint(relation_rows),
            }
        )

    canonical_pair = (
        source_expected_byte_count == comparison.source_profile.EXPECTED_BYTE_COUNT
        and source_expected_sha256 == comparison.source_profile.EXPECTED_SHA256
        and runtime_expected_byte_count == comparison.runtime_profile.EXPECTED_BYTE_COUNT
        and runtime_expected_sha256 == comparison.runtime_profile.EXPECTED_SHA256
    )
    all_match = all(
        item["all_runtime_values_match_binary64_projection"] for item in field_results
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": {
            "id": HYPOTHESIS_ID,
            "source_parse": "python-float-from-decimal-text-ieee754-binary64",
            "render": "python-repr-shortest-roundtrip-decimal",
            "comparison": "exact-decimal-equality-to-runtime-token",
            "provider_transform_claimed": False,
        },
        "record_count": len(source_bridge),
        "canonical_receipt_pair_verified": canonical_pair,
        "comparison_key_set_sha256": key_set_sha256,
        "numeric_fields": field_results,
        "all_fields_numerically_consistent_with_hypothesis": all_match,
        "source_to_runtime_transform_lineage_verified": False,
        "provider_generator_identity_verified": False,
        "runtime_values_substitutable_with_source_values": False,
        "source_runtime_semantic_equivalence_verified": False,
        "external_bytes_persisted": False,
        "raw_rows_returned": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
