# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Extend Agent Action semantic identity for the fixed CEMS RP10 receipt."""

from __future__ import annotations

from typing import Any

try:
    from scripts import agent_action_protocol_country_risk as _legacy
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import agent_action_protocol_country_risk as _legacy

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

CEMS_RP10_RECEIPT_ACTION = "cems_europe_rp10_receipt"
NETWORK_ACQUISITION_ACTIONS = _legacy.NETWORK_ACQUISITION_ACTIONS | {
    CEMS_RP10_RECEIPT_ACTION
}


def semantic_request_id(
    request: dict[str, Any], execution_sha: str, repository: str
) -> str:
    if (
        type(request) is dict
        and request.get("action") == CEMS_RP10_RECEIPT_ACTION
        and request.get("target_sha") != execution_sha
    ):
        raise ProtocolError(
            "network acquisition target_sha must equal trusted execution_sha"
        )
    return _legacy.semantic_request_id(request, execution_sha, repository)


def semantic_request_id_from_result(result: dict[str, Any]) -> str:
    required = ("action", "dataset_id", "target_sha", "execution_sha", "repository")
    for field in required:
        if field not in result:
            raise ProtocolError(f"result missing semantic field: {field}")
    request_view = {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "action": result["action"],
        "dataset_id": result["dataset_id"],
        "target_sha": result["target_sha"],
    }
    return semantic_request_id(
        request_view, result["execution_sha"], result["repository"]
    )
