#!/usr/bin/env python3
"""Predeclared no-count-cap sensitivity for the independent freMTPL2 duration study."""
from __future__ import annotations

import hashlib
import json

import tmp_ffbk_duration_meanclass_independent as base


def main() -> None:
    if hashlib.sha256(base.QUESTION_FINGERPRINT.encode()).hexdigest() != base.QUESTION_SHA256:
        raise RuntimeError("question SHA mismatch")
    d, meta = base.load_data(cap_claimnb=False)
    results = [base.run_split(d, s) for s in base.OUTER_SEEDS]
    payload = {
        "experiment": "independent-underwriting-fremtpl2-duration-risk-meanclass-v0-no-count-cap",
        "classification": "PREDECLARED_SENSITIVITY / INDEPENDENT_REPLICATION / MODERN_MODEL_RESEARCH",
        "question_fingerprint": base.QUESTION_FINGERPRINT,
        "question_sha256": base.QUESTION_SHA256,
        "openml": meta,
        "data": {
            "rows": int(len(d)),
            "unique_policy_ids": bool(not d["IDpol"].duplicated().any()),
            "exposure_sum": float(d["Exposure"].sum()),
            "claim_count": float(d["ClaimNb"].sum()),
            "cap_claimnb": False,
            "policies_claimnb_gt4_after_prepare": int((d["ClaimNb"] > 4).sum()),
        },
        "runtime": base.runtime(),
        "outer_seeds": list(base.OUTER_SEEDS),
        "protocol": {
            "target": "standalone freMTPL2freq.ClaimNb; no count cap sensitivity",
            "outer_test_fraction": 0.25,
            "bootstrap_reps": 1000,
            "glm_alpha": base.GLM_ALPHA,
            "hgb_learning_rate": 0.05,
            "hgb_early_stopping": False,
            "hgb_random_state": 0,
            "hgb_max_bins": 255,
            "hgb_capacity_grid": [{"id": cid, **cfg} for cid, cfg in base.HGB_CONFIGS],
        },
        "results": results,
        "nextgen_promotion": "NONE",
    }
    core = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    payload["result_payload_sha256_without_receipt"] = hashlib.sha256(core).hexdigest()
    with open("tmp_ffbk_duration_no_count_cap_result.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    main()
