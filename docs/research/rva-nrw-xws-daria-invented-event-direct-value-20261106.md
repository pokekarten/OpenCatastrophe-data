<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Daria 1990: original historical gust, invented NRW direct-value sensitivities

**6 November 2026 — research-only.** This independent arithmetic stage consumes
the **actual, previously verified** four-source XWS Daria-1990-derived 10,000-site
NRW ZIP from [PR #1373](https://github.com/pokekarten/OpenCatastrophe-data/pull/1373)
rather than inventing meteorological wind values. It DOES invent every wind-to-damage
response parameter and every insurance-like site TIV. This is **not** validated
Germany wind vulnerability, real R+V exposure, actual claims, insured gross or net,
Oasis/NextGen native loss, annual event frequency, OEP/AEP or a confidence interval.

## Physically observed/derived part versus scenario part

- Original source: [Extreme Wind Storms catalogue](https://www.europeanwindstorms.org/),
  Daria / Burns Day storm in **January 1990**. Source grids and each of the three
  recalibrated **maximum 3-second 10 m gust** variants are independently pinned to
  the four 2026-11-05 observed full-file SHA-256 hashes in
  [original-site wind proof](rva-nrw-xws-daria-original-wind-source-20261105.md).
  All three fields represent **one** historical physical event, not three
  frequencies or simulations. XWS terms: CC BY 4.0, attribution (c) Copyright
  Met Office, University of Reading and University of Exeter.
- Buildings: **10,000** sampled public **2022** NRW building candidates across
  **53 Kreise** with recorded site-to-XWS-grid IDs and a maximum grid-centroid
  matching distance of **17.11 km**. Neither this crosswalk nor source GFK codes
  prove actual wall or roof material. Public candidate position is not an
  R+V insured property location.
- Economics: **EUR 4,826,029,500 fictional building replacement value**
  using a separate **2025-like** hypothetical model. This is not an estimate
  of R+V's insured site/TIV register, contractual limit or actual claims.
- Response: two invented deterministic **piecewise-linear** monetary direct-value
  damage fractions in gust m/s; the exact knots are declared in the Python
  runner source code and output JSON receipt. No Schwierz/Welker/CLIMADA curve
  was copied or represented as German calibration, and no GPL source was added.
  At 20/30/40 m/s, the illustrative resilient scenario uses 0/0.2/1%
  and the illustrative fragile scenario uses 0/2/10%. Both are illustrative
  assumptions, not research-estimated empirical percentages.

Each invented vulnerability function is applied separately to lower95, mean
and upper95 XWS *views of the same storm*. The resulting six values are
**conditional direct-value impact sensitivities**, not a probability mixture.
No independence, percent confidence, frequency, risk transfer or capital
interpretation is valid. No secondary-uncertainty draw is generated.

## Implemented reproducible contract

`research_runners/rva_nrw_xws_daria_invented_damage_v0.py` reads only the
prior source-derived hazard ZIP (not raw XWS CSVs). It rejects incorrect
original-source SHA-256, missing or changed input/manifest hashes, wrong
source admission booleans, a missing physical county or site, fictitious
"actual insured" claims, invalid 3s gust or reversed XWS views, missing
county mass and unsupported response speed. It preserves exact 10k sites
and 53 Kreis exposure totals; every invented direct-value impact is
rounded per asset to integer EUR cents. An independent county and six-
scenario aggregation must reconcile identically, never silently scale
10k toy sites to the full 1,060,546-contract fictional national book.

The output ZIP has deterministic timestamps and carries site×6 impacts,
county×6 totals, the six-case scenario matrix and an independent receipt
of both upstream and generated content hashes. No provider-original bytes
or real insurer data enter Git. The output carries explicit boolean NO-GO
fields for German vulnerability, insurer losses, risk frequency and annual
EP. Executable negative and hand-calculated synthetic tests are in
`tests/test_rva_nrw_xws_daria_invented_damage_v0.py`.

The same already-existing source workflow
[NRW XWS Daria original open wind source preflight](../../.github/workflows/rva-nrw-xws-daria-source.yml)
can execute this read-only calculation **after** the authentic original-source
10k site gust overlay, before the run deletes ephemeral provider originals.
The separate output is labeled **INVENTED, NOT CAT LOSS** and is a short-lived
research artifact. Successful CI proves a bounded reproducible response
calculation only, not scientific suitability or any R+V gross/net/annual EP.

## Next scientifically necessary gates

A Germany-relevant, independently licensed and tested physical
wind→building/roof vulnerability relationship is required to replace the
invented damage curve. Source-specific building typology, material, construction
era, elevation and local gust/granularity uncertainty need their own analysis.
Then a separately modeled insurance terms and occurrence/loss financial
module can yield conditional insured losses. A scientifically justified
**complete annual catalogue**, including zero-event years, joint-event
clustering and weights, is required before calling any result OEP or AEP.
