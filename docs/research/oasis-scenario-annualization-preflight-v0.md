<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Oasis deterministic scenario annualization preflight v0

**2026-11-05 — research-only, fail closed; not a native Oasis run or dataset admission.**

## Goal and boundary

The [public Oasis candidate source landscape](../../landscape/sources-oasis-public-models-20261105.json)
contains several runnable-looking examples with very different economic meanings. A model
directory, an `events.csv`, an `occurrence.csv` or an analysis option named
`full_uncertainty_oep` does not establish a calibrated annual catalogue, annual period
weights, physical event identity, policy terms, insured/retained losses, or a company
portfolio. Counting scenario rows as independent annual catastrophes creates false
frequencies, misleading exceedance probabilities, and later treaty errors.

The standard-library preflight
[`research_runners/oasis_scenario_annualization_preflight_v0.py`](../../research_runners/oasis_scenario_annualization_preflight_v0.py)
has two explicitly **non-admitting** modes:

- `occurrences` reads **locally supplied** original `events.csv` and
  `occurrence.csv`, checks exact column structure, positive IDs, complete
  references, dates, duplicate rows, and optionally exact upstream Git blob
  identifiers. It reports the number of IDs, occurrence rows and represented
  periods, but **never** infers an annual probability measure from the files.
- `event-sets` reads a locally supplied `model_settings.json` `event_set`
  selector, checks unique option IDs and integer event counts, and reports
  whether the configured default is one of the declared option IDs. It does
  **not** treat alternatives as independent physical storms.

For both valid modes the machine output is intentionally
`status=parsed_but_not_annualized` and `annual_oep_aep_authorized=false`.
A malformed, unexpectedly large, inexact or hash-mismatched input fails with
exit **2** and `status=blocked`. Exit **0** means only that bounded metadata
parsed successfully, **not** that a stochastic model, a financial module or
a site exposure is ready.

## Original upstream evidence — no provider bytes committed here

**IPE France Hail / Ela (6–10 June 2014)**

- Model configuration: [`model_settings.json`](https://github.com/OasisLMF/Scenarios/blob/main/IPE/FranceHail/meta-data/model_settings.json), Git blob `5f9361339f2acfd31975b32dc15c2438ee8351f9`, names the historical Ela event.
- [`events.csv`](https://github.com/OasisLMF/Scenarios/blob/main/IPE/FranceHail/model_data/events.csv), Git blob `bf415bd0437f066ee593d37503fc50bb17f19fcf`, has six event IDs 11–16.
- [`occurrence.csv`](https://github.com/OasisLMF/Scenarios/blob/main/IPE/FranceHail/model_data/occurrence.csv), Git blob `dde40cb030a4a1de06f6cb4d3f04d5b07c709900`, lists all six rows under `period_no=1` with placeholder year 1.
- [`analysis_settings.json`](https://github.com/OasisLMF/Scenarios/blob/main/IPE/FranceHail/analysis_settings.json), Git blob `6a8099370fc72a300719ae47841cafc37d121ac5`, requests GUL AAL and AEP/OEP but has `il_output=false`. Requesting an EP calculation is not independent proof of annual return-period validity.
- The six records could encode storm parts, scenario samples or other event divisions. The source CSVs alone do **not** distinguish these; neither treating them as six independent physical storms nor forcing them into one is justified without the model's physical-event convention.

**Impact Forecasting EUWS / Ciarán and Domingos (November 2023)**

- [EUWS source README](https://github.com/OasisLMF/Scenarios/blob/main/ImpactForecasting/EUWS/source_data/README_EUWS.txt), Git blob `dc47f484937fe5d55415868694c917c5b15ddc6b`, describes two physical storms with three windfield interpolations for each (15, 30 and 40 neighbouring weather stations). They are **alternative footprint views**, not six independent annual storm occurrences.
- [EUWS `model_settings.json`](https://github.com/OasisLMF/Scenarios/blob/main/ImpactForecasting/EUWS/1.0.0/meta-data/model_settings.json), Git blob `08f07cf6d8b52c1d0fc2c47af390ec8c6cd5fd1e`, declares `event_set` IDs `ciaran` and `domingos`, each with three events. Its `default` is `cieren`, which does not match either ID; this is a **configuration-inconsistency candidate**, not a proven Oasis runtime failure.
- `occurrence.bin` in the public model-data tree was listed as zero bytes in the 2026-11-05 GitHub directory review. A full annual event probability measure has not been established.

## Reproduce offline using original public sources

Download the specific upstream files outside this repository under their
per-asset terms, and pin original bytes using the recorded Git blob SHA-1 values.
For example, from the repository root:

```sh
python research_runners/oasis_scenario_annualization_preflight_v0.py occurrences \
  /reviewed/external/FranceHail/events.csv \
  /reviewed/external/FranceHail/occurrence.csv \
  --events-git-blob bf415bd0437f066ee593d37503fc50bb17f19fcf \
  --occurrence-git-blob dde40cb030a4a1de06f6cb4d3f04d5b07c709900

python research_runners/oasis_scenario_annualization_preflight_v0.py event-sets \
  /reviewed/external/EUWS/model_settings.json \
  --settings-git-blob 08f07cf6d8b52c1d0fc2c47af390ec8c6cd5fd1e
```

The paths above are **illustrative external input locations**, not local
files committed to Git or evidence that a download has happened. Git blob
SHA-1 checks protect against accidentally substituting different source bytes
under the same name; for durable original acquisition receipts also record
independent SHA-256, object size, retrieve time and provider rights.

Tests (independently synthetic fixtures only):

```sh
python -m unittest discover -s tests \
  -p 'test_oasis_scenario_annualization_preflight_v0.py' -v
```

## Native CAT model next steps

1. Keep [source-gated R+V hypothetical OED staging PR #1373](https://github.com/pokekarten/OpenCatastrophe-data/pull/1373) independent. Unknown building coordinates and non-admitted model assets block issuer-specific native hazard lookup.
2. For the first **engine-only** smoke, use the independently released fictional [OasisPiWind](https://github.com/OasisLMF/OasisPiWind) model with a pinned software/toolchain, its explicitly demo inputs, and GUL/IL/RI output checks. Keep it separate from this scenario metadata gate.
3. For a **European storm** pilot, first resolve the EUWS selectable event-set mismatch and verify its model-specific licence and alternative-footprint semantics. No hidden conversion of three footprint alternatives into three independent storms.
4. For **gross/net annual EP**, prove the full source-period/sample measure, zero-loss years, intra-year physical-event identity, vulnerability/taxonomy, OED policy and insured/RI/retro contracts, and end-to-end loss-path parity. A single event scenario or a sample GUL figure is not sufficient.

## Rights and science controls

Original source data and model bytes remain outside Git. The Oasis Scenarios
repository has a BSD-3-Clause software/repository notice, but says partner
footprints may have separate use conditions. Any download, processing,
redistribution or commercial use requires the exact product/version's rights
review. This guard grants **no** permissions, performs **no** internet access,
and does **not** turn source observations into an admitted or calibrated model.
