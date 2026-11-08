<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Oasis model and data source discovery: second pass, 2026-11-05

**Scope:** public links, documentation, publisher dataset metadata and code-tree
inspection only. This work adds discovery metadata, not scientific approval,
commercial reuse authorization, external data bytes or a completed insurer
CAT run.

## Canonical registry and deduplication

Canonical discoveries are in
[`landscape/sources-oasis-model-input-leads-20261105.json`](../../landscape/sources-oasis-model-input-leads-20261105.json).
Its generated Markdown twin is a **read-only projection**, not a separate truth.

This pass adds nine distinct research leads. A live search of the main
repository found the following original sources **already present**, so they
were *not* re-added:

- **GEM Global Exposure Model v2026.0.0:** existing
  `gem.global-exposure-model.v2026.0.0`, with CC BY-NC-SA 4.0
  restrictions; country exposure not policy holdings.
- **GEM Global Vulnerability Model v2026.0.0:** existing
  `gem.global-vulnerability-model.v2026.0.0`, with the same
  noncommercial/sharealike boundary; OpenQuake XML is not automatically
  an Oasis-format vulnerability table.
- **Copernicus Enhanced European Windstorm ERA5 historical reanalysis:**
  existing `copernicus.c3s.european-windstorm-reanalysis` and its
  original-source manifest, plus an active annual-frequency calibration
  research PR #1308. The new C3S **synthetic WISC** event collection is
  scientifically distinct from that historical observed/reanalysis series.
- **EFEHR ESRM20 European exposure v1.0:** already represented by
  `manifests/efehr.esrm20.european-exposure-model.v1.0.json`.
  Source is CC BY 4.0, but repository approval is **limited to one exact
  Kosovo taxonomy derivative**; neither the original entire Europe exposure
  dataset nor new Germany inputs have blanket local admission. Use
  [the official exposure publisher](https://eu-risk.eucentre.it/exposure/)
  to re-review the particular release and source bytes.
- **JRC Huizinga depth-damage functions, EFEHR vulnerability v2.1 and
  CLIMK wind footprints:** already have separate source-landscape entries.
  Do not pretend that finding a new Oasis adapter creates a new source dataset.

## Three strongest new technical leads

### 1. Synthetic WISC 22,980 European storm footprints

[Copernicus CDS dataset](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-synthetic-events?tab=overview),
DOI `10.24381/cds.ce973f02`, metadata updated January 2025.
The official portal describes 22,980 footprints, three alternative
calibration/downscaling methods, five independent initial-condition
ensembles, maximum 3-second 10-m gust in m/s over a 72-hour event window,
and NetCDF-4 arrays on interpolated ~4.4-km spatial support.
The original 7,660-event WISC set was used in an Oasis-compatible model;
**it is a lineage subset, not an additional independent 7,660 losses**.
The WISC user portal itself has been retired.

Research pipeline, **not yet executed or admitted**:
(1) acquire publisher exact dataset/version/API request under CC-BY terms;
(2) pin full file byte length, SHA-256 and units; (3) identify original
event ID, source climate member, independent physical storm and year;
(4) construct reproducible grid/areaperil `footprint.csv`, `events.csv`
and `occurrence.csv` under one immutable world/sample/period contract;
(5) compare original gust values against an independent ERA5 historical
validation cohort; (6) select a source-licensed, wind-speed-unit- and
building-taxonomy-compatible vulnerability curve; (7) only after
source-year statistical validation construct insured/reinsured loss paths.

**Hard stop:** dividing or multiplying 22,980 storms by any guessed year
count does not yield a defensible annual event frequency or calibrated
German 1-in-200 OEP. The related C3S historical ERA5 source has a
separate admitted metadata manifest and a separate independent holdout
calibration candidate.

### 2. Independent LA earthquake Oasis package

[Community repository](https://github.com/ekrishgupta/oasis-eq-cat-model)
has an actual `oasislmf.json`, source scripts to fetch USGS ShakeMaps
and building footprints, and a published `model_data/` set that
includes event IDs, loss vulnerability tables and an occurrence table.
It is a useful reference for the **architecture and source conversion
steps** from USGS intensity grids plus FEMA Hazus earthquake tables to
Oasis hazard/vulnerability/exposure and financial calculation.

**Hard stop:** no repository LICENSE was observed. A public GitHub repo
is NOT a general right to copy software, derived asset tables,
USGS/FEMA/Microsoft inputs or result artifacts. Treat the claimed loss
figures as author-provided, **not independently reproduced or validated**.
Do not execute scripts with unrestricted Docker permissions on trusted
runners without separate supply-chain review. This is a research lead,
not a new admitted earthquake model.

### 3. German building valuation research and executable flood curves

The [GFZ Ahrweiler sanitized-value model archive](https://zenodo.org/records/20038906)
covers independently modelled valuation-method alternatives with
construction/type benchmark samples. Crucially, **the sanitized tables do
not provide precise building coordinates**. Full location geometry
requires separate permission, and third-party building-cost material
can have distinct rights. These data could challenge hypothetical
replacement-cost priors, not establish real insurer assets or
policy/TIV mapping. The current source licence was not conclusively
resolved in this pass.

[Delft-FIAT](https://github.com/Deltares/Delft-FIAT) is MIT software
and defines explicit depth-damage `vulnerability.csv` tables.
It is **not** an Oasis model. A future original-source-rights-gated
adapter could convert metres of water depth, damage-fraction curves and
occupancy classes to Oasis intensity/damage bins. The MIT software
licence does not override third-party scientific damage function rights.

## Independent WISC academic wind loss code (newly found)

[ElcoK/WISC](https://github.com/ElcoK/WISC) is the original academic
European windstorm loss/risk modelling Python research implementation
(Elco Koks / Vrije Universiteit Amsterdam), with a directly inspected
**MIT software licence** (LICENSE Git blob
`638dd62ec2a1b317979f283a533cee683dbdb447`).
Its [`scripts/functions.py`](https://github.com/ElcoK/WISC/blob/master/scripts/functions.py)
(Git blob `da6278d5dc61fb05dd89018fa854d77b36f16f2b`) contains
`region_exposure`, `region_losses`, `loss_calculation`,
`load_curves` and `load_max_dam`; region orchestration is in
[`scripts/analyze.py`](https://github.com/ElcoK/WISC/blob/master/scripts/analyze.py)
(Git blob `79b311c58354bb478088ec547dc53b23c625f483`).
This is relevant as a **WISC exposure/vulnerability methodology
challenger** and possible alternative to proprietary and
noncommercial damage functions.

**Hard stop:** it is **not** a native Oasis model package and does not
include a licensed original 22,980-event C3S NetCDF archive, complete
versioned externally required exposure/curve data, original insurer
locations, OED financial contracts, or a confirmed contemporary
runnable loss path. The MIT licence on academic SOFTWARE must not be
propagated to externally sourced WISC weather data, OSM buildings,
construction costs or damage curves. Scientific calibration,
compatibility with current geo libraries and per-asset legal rights
remain open. It is independently registered as
`research.elcok.wisc.european-wind-damage` with
`admission_status=not_admitted`.

## Additional validation and licensed model sourcing

The [GEM 2026 country risk profiles](https://github.com/gem/risk-profiles/tree/v2026.0.0)
may provide independent **aggregate earthquake loss and exposure
benchmarks** for 204 countries and territories. They are CC
BY-NC-SA 4.0, and may not be used commercially on that licence alone.
They do not furnish Oasis stochastic events or a direct licence for the
already-registered GEM exposure/vulnerability source products.

The [IDF RMSG CatRiskTools catalogue](https://idf-rmsg.github.io/CatRiskTools/)
is a machine-/human-research lead to open **and commercial**
catastrophe-model offerings, including a field on whether each can
run on Oasis. The
[Oasis May 2025 provider model listing](https://oasislmf.org/download_file/force/1718/229)
identifies further full-vendor product families, including Germany
hail and European windstorm. Its 2025 snapshot cannot establish
current 2026 executable access or source redistribution rights.
Vendor contracting, model-version evidence and financial layer scope
must be checked with each provider; deterministic freely viewable
storm scenarios are not substitutes for licensed probabilistic models.

## Next reproducible acceptance experiment

Prefer a small and bounded, **purely synthetic, no-third-party-bytes
committed** European windstorm Oasis adapter challenge. Require source
dataset licence and a witnessed exact NetCDF asset, separate
`event_id`, `source_year`, `physical_storm_id`,
`ensemble_member`, `recalibration_method`, `areaperil_id`,
`gust_m_per_s` and their immutable receipts. Include a negative
control that fails if three recalibration methods are silently treated
as three independent weather events, or if zero-storm years are lost.

The [native PiWind runner PR #1383](https://github.com/pokekarten/OpenCatastrophe-data/pull/1383)
is an independent **fictional engine execution proof**, not a
windstorm model calibration; do not conflate it with this future
data-admission and probability-measure gate. The
[source-gated synthetic OED PR #1373](https://github.com/pokekarten/OpenCatastrophe-data/pull/1373)
also remains independent and does not prove company insured-site
coordinates.
