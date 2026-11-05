<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Pinned native Oasis PiWind GUL/IL/RI proof v0

**Research-only.** This is a controlled **native-engine demonstration using the
official fictitious UK PiWind test model**, not a calibrated insurer catastrophe
model, not original company exposure, and not a live German hazard or OEP/AEP
calibration.

## Source and engine contract

- Original public model: [OasisLMF/OasisPiWind](https://github.com/OasisLMF/OasisPiWind), exact commit `94820c59f169b222d4c1a72256ff0a8f86a9e5bf`. Repository licence: BSD-2-Clause. Original model `oasislmf.json` uses fictional OED examples, lookup tables, windstorm footprints and example account/reinsurance inputs. The checked-in sample analysis settings request GUL, IL, RI and separate ORD reporting outputs.
- Engine package: [OasisLMF 2.5.8](https://pypi.org/project/oasislmf/2.5.8/) (published 29 September 2026), running on Python 3.12 with `libspatialindex-dev`, using the official `oasislmf model run -C oasislmf.json` interface.
- CI: [`.github/workflows/oasis-piwind-pinned-native.yml`](../../.github/workflows/oasis-piwind-pinned-native.yml) runs on selected source edits or manually; read-only GitHub access, no external database access, no credentials or production sources.
- Inspection: [`research_runners/oasis_piwind_native_smoke_v0.py`](../../research_runners/oasis_piwind_native_smoke_v0.py) verifies the source checkout Git SHA and installed package version, invokes the actual native model, then requires a **single unambiguous** output folder with six nonempty ORD CSVs:
  `gul_S1_palt.csv`, `gul_S1_psept.csv`, `il_S1_palt.csv`, `il_S1_psept.csv`, `ri_S1_palt.csv`, `ri_S1_psept.csv`.
- Each required file receives a reported byte length, SHA-256 and data-row count in a research JSON receipt written to an isolated runner temp directory and printed to the CI log. Source and result bytes are **not committed** to Git.

The plugin/CLI source is separate from this repository; the model clone is
created temporarily and its commit is independently checked after cloning.
The model version and the top-level Oasis package version are pinned, but
transitive Python dependencies and Ubuntu package revisions are **not** frozen
to exact content hashes in this v0 study. Numerical cross-run or cross-platform
exact parity is **not** an acceptance claim. An error, timeout, missing stream,
empty CSV or duplicate output directory blocks rather than fabricates success.

## Run verification

Targeted unit tests use only independently invented rows:

```sh
python -m unittest discover -s tests \
  -p 'test_oasis_piwind_native_smoke_v0.py' -v
```

A manual isolated execution (network access and an authorized licence
interpretation required):

```sh
git clone https://github.com/OasisLMF/OasisPiWind.git /tmp/OasisPiWind
git -C /tmp/OasisPiWind checkout --detach 94820c59f169b222d4c1a72256ff0a8f86a9e5bf
python -m pip install 'oasislmf==2.5.8'
python research_runners/oasis_piwind_native_smoke_v0.py /tmp/OasisPiWind \
  --timeout-seconds 900 --receipt /tmp/piwind-native-receipt.json
```

The manual command presupposes suitable platform libraries including
`libspatialindex`, a **fresh** clone with no existing `runs/` and a pre-existing
receipt parent folder. Use the GitHub workflow for the repeatable Linux
execution profile. The CI result, not merely this README or an expected
output example, decides whether a native engine run has been achieved.

## What successful native output would and would not establish

Passing the model workflow would prove a bounded model-data/lookup/exposure/
sample/financial-module/output chain for **the pinned public PiWind toy** and
a reproducible receipt identifying GUL/IL/RI outputs. It does **not** prove:

- Any real buildings, insured-site location, property TIV, or actual carrier
  portfolio, including the distinct source-gated synthetic residential pilot
  in [PR #1373](https://github.com/pokekarten/OpenCatastrophe-data/pull/1373).
- Vendor-scientific hazard intensity or regional vulnerability calibration,
  annual event clustering semantics, climate trend or source independent loss
  validation.
- R+V-specific financial terms, multi-cedant contracts, outward retro,
  hours clauses, reinstatement premiums, or a gross/retained company EP curve.
- Cross-engine or cross-version numeric equivalence, genuine catastrophe
  capital metrics, exact 1-in-200 pricing or solvency validation.
- Full dataset/source licensing of any future vendor-supplied hazard or
  vulnerability assets.

Native output must preserve a **source-specific** loss perspective and
complete event/period/sample state before it is eligible for a NextGen
source-year bridge. The independent
[Oasis scenario annualization gate](oasis-scenario-annualization-preflight-v0.md)
prevents deterministic scenarios from masquerading as a calibrated annual
stochastic catalogue. The next model step, after a successful PiWind proof,
is a separate insured-loss/treaty mapping with explicit source period
weights, physical event grouping, fictional exposed coordinates and audited
gross–insured–reinsured return-period curves. No silent promotion of this
toy experiment into the carrier model is permitted.
