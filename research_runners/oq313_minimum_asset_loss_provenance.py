#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Verify the minimum_asset_loss data flow in the *pinned* OpenQuake 3.13 code.

A successful local probe establishes source-code semantics only: the threshold
removes asset/event losses before both risk_by_event and avg_losses aggregation.
It does not establish whether the *published ESRM20 country reference output*
was generated with the same threshold, data/portfolio, or annualization rule.

No network, imported OpenQuake packages, provider inputs, or country values.
The narrow probe can run on the OQ3.13 checkout already staged in the owner-only
Kosovo workflow before the costly image build. All three original upstream
source files are verified by their immutable Git blob identities.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "oc-eq1-oq313-minimum-asset-loss-source-provenance-v1"
OQ_COMMIT = "16dd69ecea0c6dcaf49c22ca12edc9da3f024889"
MINIMUM_ASSET_LOSS_STRUCTURAL_EUR = 2000
EXPECTED_GIT_BLOBS = {
    "openquake/risklib/scientific.py": "231cfe596c86e3913d73a8478ab0ca472f388d2d",
    "openquake/risklib/riskmodels.py": "7ea791c55360b2b84be039530f198cb8bf32cac5",
    "openquake/calculators/event_based_risk.py": "e5ad45a19a4df8c680a66d08a4d72123829f511b",
}
MAX_BYTES_PER_SOURCE = 128 * 1024


class ThresholdProvenanceError(RuntimeError):
    """Pinned-source integrity or minimum-loss dataflow was not demonstrated."""


def git_blob_id(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise ThresholdProvenanceError("source blob is not bytes")
    return hashlib.sha1(
        b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
    ).hexdigest()


def _section(source: str, start: str, end: str, *, label: str) -> str:
    left = source.find(start)
    if left < 0 or source.find(start, left + 1) >= 0:
        raise ThresholdProvenanceError(f"{label} entrypoint missing or ambiguous")
    right = source.find(end, left + len(start))
    if right < 0:
        raise ThresholdProvenanceError(f"{label} boundary missing")
    return source[left:right]


def _ordered(section: str, fragments: tuple[str, ...], *, label: str) -> None:
    previous = -1
    for fragment in fragments:
        position = section.find(fragment, previous + 1)
        if position < 0:
            raise ThresholdProvenanceError(f"{label} dataflow mismatch")
        previous = position


def probe_source_bytes(blobs: dict[str, bytes]) -> dict[str, Any]:
    if type(blobs) is not dict or set(blobs) != set(EXPECTED_GIT_BLOBS):
        raise ThresholdProvenanceError("OpenQuake source file set drifted")
    sources: dict[str, str] = {}
    for path, expected_blob in EXPECTED_GIT_BLOBS.items():
        payload = blobs[path]
        if type(payload) is not bytes or not payload or len(payload) > MAX_BYTES_PER_SOURCE:
            raise ThresholdProvenanceError("OpenQuake source size drifted")
        if git_blob_id(payload) != expected_blob:
            raise ThresholdProvenanceError("OpenQuake pinned blob identity drifted")
        try:
            sources[path] = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ThresholdProvenanceError("OpenQuake source encoding drifted") from exc

    riskmodels = sources["openquake/risklib/riskmodels.py"]
    scientific = sources["openquake/risklib/scientific.py"]
    calculator = sources["openquake/calculators/event_based_risk.py"]

    # Source RiskModel forwards the fixed 2000 EUR parameter to the loss
    # calculation, rather than filtering *only* the stored asset loss table.
    forwarding = _section(
        riskmodels,
        "    def event_based_risk(self, loss_type, assets, gmf_df, col, rndgen):",
        "    scenario = ebrisk = scenario_risk = event_based_risk",
        label="risk-model threshold forwarding",
    )
    _ordered(
        forwarding,
        (
            "vf = self.risk_functions[loss_type, 'vulnerability']",
            "return vf(asset_df, gmf_df, col, rndgen,",
            "self.minimum_asset_loss[loss_type]",
        ),
        label="risk-model threshold forwarding",
    )

    # The function receives loss ratios plus actual asset values, samples
    # absolute loss, then removes events at/below the threshold.
    losses = _section(
        scientific,
        "    def __call__(self, asset_df, gmf_df, col, rng=None, minloss=0):",
        "    def strictly_increasing(self):",
        label="vulnerability loss filter",
    )
    _ordered(
        losses,
        (
            "losses = sampler.get_losses(df, covs)",
            "ok = losses > minloss",
            "loss=losses[ok]",
        ),
        label="vulnerability loss filter",
    )
    sampler = _section(
        scientific,
        "    def get_losses(self, df, covs):",
        "    def sampleLN(self, df):",
        label="absolute-loss sampler",
    )
    if "vals = df['val'].to_numpy()" not in sampler or "losses = vals * df['mean'].to_numpy()" not in sampler:
        raise ThresholdProvenanceError("asset replacement-value scaling drifted")

    aggregate = _section(
        calculator,
        "def aggreg(outputs, crmodel, ARKD, kids, rlz_id, monitor):",
        "def event_based_risk(df, oqparam, monitor):",
        label="risk event/annual-average aggregator",
    )
    _ordered(
        aggregate,
        (
            "alt = out[ln].reset_index()",
            "coo = average_losses(",
            "fast_agg(eids + U64(K), values, correl, li, acc)",
        ),
        label="risk event/annual-average aggregator",
    )

    aggregate_result = _section(
        calculator,
        "    def agg_dicts(self, dummy, dic):",
        "    def post_execute(self, dummy):",
        label="annual-average asset accumulation",
    )
    _ordered(
        aggregate_result,
        (
            "for ln, ls in dic['avg'].items():",
            "self.avg_losses[coo.row, coo.col, lti[ln]] += coo.data",
        ),
        label="annual-average asset accumulation",
    )

    post_start = calculator.find("    def post_execute(self, dummy):")
    if post_start < 0:
        raise ThresholdProvenanceError("annual-average post-processing entrypoint missing")
    post = calculator[post_start:]
    _ordered(
        post,
        (
            "self.avg_losses[:, r] *= self.avg_ratio[r]",
            "self.datastore['avg_losses-rlzs'] = self.avg_losses",
        ),
        label="annual-average post-processing",
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PINNED_SOURCE_SEMANTICS_VERIFIED",
        "openquake_source_commit": OQ_COMMIT,
        "source_file_git_blob_ids": EXPECTED_GIT_BLOBS.copy(),
        "source_declared_minimum_asset_loss_structural_eur": MINIMUM_ASSET_LOSS_STRUCTURAL_EUR,
        "loss_filter_predicate": "absolute_asset_event_loss > minimum_asset_loss",
        "loss_equal_to_threshold_is_excluded": True,
        "filter_applied_before_risk_by_event_aggregation": True,
        "filter_applied_before_avg_losses_aggregation": True,
        "can_affect_reconstructed_average_annual_loss": True,
        "published_esrm20_same_threshold_verified": False,
        "threshold_compatibility_verified": False,
        "denominator_semantics_verified": False,
        "annualization_semantics_verified": False,
        "reference_loss_agreement_verified": False,
        "external_bytes_persisted": False,
        "provider_numeric_values_interpreted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def run(source_root: Path) -> dict[str, Any]:
    root = source_root.resolve(strict=True)
    if not root.is_dir() or (root / ".git").is_symlink():
        raise ThresholdProvenanceError("OpenQuake checkout root invalid")
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD^{commit}"],
            check=True, text=True, capture_output=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ThresholdProvenanceError("cannot verify OpenQuake source commit") from exc
    if proc.stdout.strip() != OQ_COMMIT:
        raise ThresholdProvenanceError("OpenQuake source checkout commit drifted")
    raw: dict[str, bytes] = {}
    for name in EXPECTED_GIT_BLOBS:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ThresholdProvenanceError("OpenQuake source path invalid")
        if path.stat().st_size > MAX_BYTES_PER_SOURCE:
            raise ThresholdProvenanceError("OpenQuake source byte limit exceeded")
        raw[name] = path.read_bytes()
    return probe_source_bytes(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = run(args.source_root)
    except (ThresholdProvenanceError, OSError, ValueError):
        print(json.dumps({
            "schema_version": SCHEMA_VERSION,
            "status": "BLOCKED",
            "threshold_compatibility_verified": False,
            "reference_loss_agreement_verified": False,
        }, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
