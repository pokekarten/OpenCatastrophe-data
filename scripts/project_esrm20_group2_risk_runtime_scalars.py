# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Project bounded runtime scalars from exact receipted ESRM20 Group2 config bytes.

This helper deliberately reuses the already reviewed Group1 runtime-scalar parser
semantics instead of creating a second parser. Group2 bytes are still verified
against their own frozen receipt before decoding or interpretation. Missing
settings remain missing; no OpenQuake defaults are supplied or inferred.
"""

from __future__ import annotations

from typing import Any

from scripts import project_esrm20_group1_risk_runtime_scalars as shared_runtime
from scripts import verify_esrm20_ebrisk_risk_config_dependencies as risk_config

SCHEMA_VERSION = "oc-esrm20-group2-risk-runtime-scalars-v1"
CONTROL_ISSUE = 281
SOURCE_ISSUE = risk_config.SOURCE_ISSUE
DATASET_ID = risk_config.DATASET_ID
PROJECT_ID = risk_config.PROJECT_ID
PROJECT_PATH = risk_config.PROJECT_PATH
COMMIT_SHA = risk_config.COMMIT_SHA
GROUP2_KEY = "group2"
GROUP2_SPEC = risk_config.config_spec(GROUP2_KEY)

# Reuse the exact reviewed parser/error surface and frozen OpenQuake reference
# from the Group1 scalar projection. This is a semantic reuse, not evidence that
# Group1 and Group2 have identical configured values.
RiskRuntimeScalarError = shared_runtime.RiskRuntimeScalarError
project_runtime_scalars_from_verified_text = (
    shared_runtime.project_runtime_scalars_from_verified_text
)
OPENQUAKE_REPOSITORY = shared_runtime.OPENQUAKE_REPOSITORY
OPENQUAKE_TAG = shared_runtime.OPENQUAKE_TAG
OPENQUAKE_COMMIT = shared_runtime.OPENQUAKE_COMMIT


def project_group2_risk_runtime_scalars(payload: bytes) -> dict[str, Any]:
    """Verify exact Group2 bytes before returning bounded scalar evidence."""

    digest = risk_config._verify_payload_identity(payload, GROUP2_SPEC)  # noqa: SLF001
    text = risk_config._decode_verified_payload(payload)  # noqa: SLF001
    scalars = project_runtime_scalars_from_verified_text(text)
    return {
        "schema_version": SCHEMA_VERSION,
        "control_issue": CONTROL_ISSUE,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "candidate_key": GROUP2_KEY,
        "repository_path": GROUP2_SPEC.repository_path,
        "byte_count": len(payload),
        "sha256": digest,
        "receipt_comment_id": risk_config.RECEIPT_COMMENT_ID,
        "openquake_reference": {
            "repository": OPENQUAKE_REPOSITORY,
            "tag": OPENQUAKE_TAG,
            "commit_sha": OPENQUAKE_COMMIT,
        },
        "runtime_scalars": scalars,
        "raw_config_returned": False,
        "historical_group_assignment_verified": False,
        "runtime_compatibility_verified": False,
        "numerical_loss_reproduction_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
