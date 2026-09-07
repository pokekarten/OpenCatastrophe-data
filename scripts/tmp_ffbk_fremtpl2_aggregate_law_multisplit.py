#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import tmp_ffbk_fremtpl2_aggregate_law as study

# Fixed before multi-split execution; do not tune from target outcomes.
SEEDS = (26090731, 26090747, 26090773)
OUT = Path("tmp_ffbk_aggregate_law_multisplit_result.json")


def main() -> None:
    runs = []
    for seed in SEEDS:
        path = Path(f"tmp_ffbk_aggregate_law_result_{seed}.json")
        study.SEED = seed
        study.OUT = path
        study.main()
        runs.append(json.loads(path.read_text()))

    def deltas(key: str) -> list[float]:
        return [float(r["scores"]["paired_crps"][key]) for r in runs]

    ig_delta = deltas("ig_minus_gamma_eur")
    im_delta = deltas("mean_matched_ig_minus_gamma_eur")
    summary = {
        "seeds": list(SEEDS),
        "ig_crps_wins": sum(x < 0 for x in ig_delta),
        "ig_crps_bootstrap_ci_excludes_zero_favourably": sum(
            r["scores"]["paired_crps"]["ig_minus_gamma_bootstrap_ci95_eur"][1] < 0
            for r in runs
        ),
        "mean_matched_ig_crps_wins": sum(x < 0 for x in im_delta),
        "mean_matched_ig_crps_bootstrap_ci_excludes_zero_favourably": sum(
            r["scores"]["paired_crps"]["mean_matched_ig_minus_gamma_bootstrap_ci95_eur"][1] < 0
            for r in runs
        ),
        "ig_minus_gamma_crps_eur": ig_delta,
        "ig_minus_gamma_relative_pct": [
            float(r["scores"]["paired_crps"]["ig_minus_gamma_relative_pct"]) for r in runs
        ],
        "mean_matched_ig_minus_gamma_crps_eur": im_delta,
        "mean_matched_ig_minus_gamma_relative_pct": [
            float(r["scores"]["paired_crps"]["mean_matched_ig_minus_gamma_relative_pct"]) for r in runs
        ],
        "tail_brier_ig_wins": {
            "development_q99_threshold": sum(
                r["scores"]["inverse_gaussian"]["tail_1_brier"] < r["scores"]["gamma"]["tail_1_brier"]
                for r in runs
            ),
            "development_q995_threshold": sum(
                r["scores"]["inverse_gaussian"]["tail_2_brier"] < r["scores"]["gamma"]["tail_2_brier"]
                for r in runs
            ),
        },
        "mean_matched_tail_brier_ig_wins": {
            "development_q99_threshold": sum(
                r["scores"]["inverse_gaussian_mean_matched_to_gamma"]["tail_1_brier"] < r["scores"]["gamma"]["tail_1_brier"]
                for r in runs
            ),
            "development_q995_threshold": sum(
                r["scores"]["inverse_gaussian_mean_matched_to_gamma"]["tail_2_brier"] < r["scores"]["gamma"]["tail_2_brier"]
                for r in runs
            ),
        },
    }
    OUT.write_text(json.dumps({"summary": summary, "runs": runs}, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
