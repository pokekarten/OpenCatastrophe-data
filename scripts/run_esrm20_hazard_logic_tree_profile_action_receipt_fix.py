# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bind the existing #481 hazard-profile action to canonical #476 receipt hashes.

This adapter changes no parser, provider target, request/result schema, or
authority semantics. It exists solely because two SHA-256 values were
transcribed incorrectly when the #481 action was first authored. The trusted
#476 bot result is the byte-identity authority.
"""

from __future__ import annotations

from scripts import run_esrm20_hazard_logic_tree_profile_action as _subject

CANONICAL_GSIM_SHA256 = "f3efd16d56189c7804824d94b20ed75d6ceefc879144d8bd697c1f9b47cf17b4"
CANONICAL_SOURCE_SHA256 = "caebf9142da6b4d6d1e970c3c008627d34943da83c977fb1da4d15d1e34d8a12"
CANONICAL_RECEIPT_COMMENT_ID = 5310057117

_subject.GSIM_SHA256 = CANONICAL_GSIM_SHA256
_subject.SOURCE_SHA256 = CANONICAL_SOURCE_SHA256
_subject.RECEIPT_COMMENT_ID = CANONICAL_RECEIPT_COMMENT_ID

REQUEST_MARKER = _subject.REQUEST_MARKER
RESULT_MARKER = _subject.RESULT_MARKER
REQUEST_SCHEMA_VERSION = _subject.REQUEST_SCHEMA_VERSION
RESULT_SCHEMA_VERSION = _subject.RESULT_SCHEMA_VERSION
ACTION = _subject.ACTION
CONTROL_ISSUE = _subject.CONTROL_ISSUE
SOURCE_SCIENCE_ISSUE = _subject.SOURCE_SCIENCE_ISSUE
DATASET_ID = _subject.DATASET_ID
GSIM_BYTE_COUNT = _subject.GSIM_BYTE_COUNT
GSIM_SHA256 = _subject.GSIM_SHA256
SOURCE_BYTE_COUNT = _subject.SOURCE_BYTE_COUNT
SOURCE_SHA256 = _subject.SOURCE_SHA256
RECEIPT_COMMENT_ID = _subject.RECEIPT_COMMENT_ID

validate_request = _subject.validate_request
has_terminal_result = _subject.has_terminal_result
_validate_profile = _subject._validate_profile
run_profile = _subject.run_profile
main = _subject.main


def assert_canonical_receipt_binding() -> None:
    if _subject.GSIM_SHA256 != CANONICAL_GSIM_SHA256:
        raise RuntimeError("GSIM receipt hash binding drifted")
    if _subject.SOURCE_SHA256 != CANONICAL_SOURCE_SHA256:
        raise RuntimeError("source receipt hash binding drifted")
    if _subject.RECEIPT_COMMENT_ID != CANONICAL_RECEIPT_COMMENT_ID:
        raise RuntimeError("canonical hazard receipt comment binding drifted")


assert_canonical_receipt_binding()

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
