# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
from unittest import mock

from scripts import check_esrm20_gsim_runtime_dedup as subject


# Frozen from the reviewed complete ESRM20 projection on main
# 807f3883a8bb3c3392f5263db6b8d0276748c843.  The digest is intentionally
# literal: future production-projector drift must not regenerate its own oracle.
EXPECTED_PROJECTED_CONTRACT_SHA256 = (
    "592076cd65e15a746e23bc9e78c2bdfefff6d95681ee534dfbeb1700790dd4ba"
)


def _projection_digest(
    projection: dict[tuple[str, str], tuple[str, str, str, tuple[str, ...]]],
) -> str:
    rows = [
        [branch_set_id, branch_id, trt, token, request_form, list(argument_keys)]
        for (branch_set_id, branch_id), (
            trt,
            token,
            request_form,
            argument_keys,
        ) in sorted(projection.items())
    ]
    payload = json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validator_result(
    projection: dict[tuple[str, str], tuple[str, str, str, tuple[str, ...]]],
) -> dict[str, object]:
    branches: list[dict[str, object]] = []
    classes: set[str] = set()
    for (branch_set_id, branch_id), (
        trt,
        token,
        request_form,
        argument_keys,
    ) in sorted(projection.items()):
        keys = list(argument_keys)
        branches.append(
            {
                "branch_set_id": branch_set_id,
                "branch_id": branch_id,
                "tectonic_region_type": trt,
                "requested_gsim_token": token,
                "resolved_gsim_class": token,
                "request_form": request_form,
                "alias_definition_present": False,
                "alias_expansion_applied": False,
                "registry_alias_key_used": False,
                "argument_keys": keys,
                "runtime_argument_keys_after_alias": keys,
                "constructor_accepted": True,
            }
        )
        classes.add(token)
    return {
        "branch_count": len(branches),
        "branches": branches,
        "unique_resolved_gsim_classes": sorted(classes),
        "alias_requested_tokens": [],
    }


class Esrm20RuntimeDedupProjectionOracleTests(unittest.TestCase):
    def test_complete_projection_matches_independent_frozen_digest(self) -> None:
        projection = subject._expected_branch_requests()
        self.assertEqual(len(projection), subject._runtime.EXPECTED_BRANCH_COUNT)
        self.assertEqual(
            _projection_digest(projection),
            EXPECTED_PROJECTED_CONTRACT_SHA256,
        )

    def test_frozen_digest_detects_nonrename_projector_drift_that_validator_codrifts_with(
        self,
    ) -> None:
        mutated_base = dict(subject._base._EXPECTED_BRANCH_REQUESTS)
        key = ("BCHydroSubIF", "SUB_IFHighStressCentralAtt")
        trt, token, request_form, argument_keys = mutated_base[key]
        mutated_base[key] = (
            "Mutated Subduction Interface",
            token,
            request_form,
            argument_keys,
        )

        with mock.patch.object(
            subject._base,
            "_EXPECTED_BRANCH_REQUESTS",
            mutated_base,
        ):
            codrifted_projection = subject._expected_branch_requests()

            # Without an external oracle, the validator accepts the same projector
            # mutation because its expected contract and the supplied rows co-drift.
            subject._validate_branches(_validator_result(codrifted_projection))

            # The literal full-contract fingerprint remains independent and catches it.
            self.assertNotEqual(
                _projection_digest(codrifted_projection),
                EXPECTED_PROJECTED_CONTRACT_SHA256,
            )


if __name__ == "__main__":
    unittest.main()
