<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Independent XWS Daria-1990 cubic wind-severity research challenger (6 Nov 2026)

## Method and evidence boundary

**A threshold-excess wind-intensity index, not a monetary catastrophe loss.**
The [original XWS storm-selection method](https://www.europeanwindstorms.org/method/select/)
documents a fixed 25 m/s, excess-cubed original-footprint storm-severity
construction. Klawa and Ulbrich (2003,
<https://doi.org/10.5194/nhess-3-725-2003>) and the later review
<https://doi.org/10.5194/nhess-24-3445-2024> discuss wind excess cubed,
particularly when site- and period-specific local **98th percentile**
thresholds are available. This study **does not** estimate those local
percentiles. A fixed 25 m/s is only the explicitly selected XWS method
variant. These are **scientific conceptual indices**, not building damage
fractions or insurance claims.

Inputs are the already source/byte-authenticated [Daria XWS source
overlay](rva-nrw-xws-daria-original-wind-source-20261105.md) combining:

- One original XWS historical storm of January **1990**; original
  lower95 / recalibrated mean / upper95 footprint uncertainties
  are views of **one physical event**, not three independent events,
  not three historical years, and not direct storm occurrence weights.
- **10,000** public 2022 NRW candidate-building locations over **53 Kreise**
  with an existing source-grid spatial join. No actual insured R+V sites.
- EUR **4,826,029,500** **invented** insurance-like 2025 building value,
  used only for an explicitly labeled value-weighted *index*.
- Pinned provider bytes, attribution and source data rights from XWS
  (c) Copyright Met Office, University of Reading and University of Exeter,
  CC BY 4.0.

For each site `i` and original Daria gust view `h`, define
`E(i,h) = max(v(i,h) - 25 m/s, 0)^3`. For every 2022 Kreis, output:

1. `sum_i E(i,h)`, units **(m/s)^3**, over *sampled candidate buildings*.
2. `sum_i fictional_TIV_i × E(i,h)`, units **fictional EUR × (m/s)^3**.
3. The number of sample buildings above the fixed threshold.

The summed index **does not reproduce original XWS full-grid SSI**:
sampling 10,000 buildings weights source cells by candidate density and
samples the same original grid point multiple times. The second index
is even more explicitly *hypothetical*, since its TIV weights were invented.
No severity-to-money scale or effect on individual building vulnerability
is identified; in particular, multiplication by EUR values **does not
turn its units into EUR losses**. Do not cross-calibrate its index directly
against the six invented wind damage functions or assume the units match.

## Executable boundaries

- Module:
  `research_runners/rva_nrw_xws_daria_excess_cube_index_v0.py`.
  It uses the existing provider SHA-pinned original-XWS CSV validation,
  10k source-OED receipt, original WGS84 source-grid index and geographic
  matching. It refuses unverified event/source bytes, fake real-insurer
  status, improperly combined storm variants, unknown counties, altered
  TIV, nonfinite wind and non-conserving county/site totals.
- Offline negative test:
  `tests/test_rva_nrw_xws_daria_excess_cube_index_v0.py`. Its invented
  three-site hand oracle checks original 25 m/s threshold, mean excess,
  exact integer/Decimal cubing and county sums with no engine dependency.
- CI job:
  [NRW original XWS Daria source workflow](../../.github/workflows/rva-nrw-xws-daria-source.yml).
  After source retrieval and original 10k site overlay, it runs the
  pure-math index on the **same original bytes**, saves a separate ZIP
  carrying only county-level index and full SHA receipt, and deletes
  ephemeral original provider/source location files.

The output must keep `no_GUL_IL_RI_OEP_AEP=true`,
`local_98th_percentile_not_estimated=true` and
`no_real_RV_insured_sites_or_money_losses=true`.
It is intentionally independent of the invented damage-response module.

## What would make this more scientific?

Construct a source-vintage-matched historical *daily* gust climatology,
estimate the local 98th percentile for each grid/site using sufficient
ordinary and zero-extreme days, and document the selection window,
stationarity, calendar completeness and historical/reanalysis observation
bias. Validate severity index against **out-of-sample** actual event
insured-loss data where contract/product and reuse rights permit. Then
source independent German building/roof typology, vulnerability and
insurance terms. A full annual, physically coherent event model is
still required before gross/insured/net OEP/AEP.

**No original raw XWS CSVs, third-party GPL model code or empirical
vulnerability table is copied to this Apache-2.0 repo.**
