<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# European windstorm: existing open-source building-loss model & modelled risk benchmark

Date: 2026-11-04. **Metadata/source code research only. No external model executable, dataset raw bytes, insurer portfolios, or actual hazard-loss calibration executed in this investigation.** This note is additive to, not a replacement for, the current C3S EWS source-identity review or PR #1308 frequency calibration.

## First-party OSS upstream: WISC building-level wind risk & loss

- Project: [ElcoK/WISC](https://github.com/ElcoK/WISC) — `master` exact checked head [c3779b387664b37cdfc49399202c74ab30531066](https://github.com/ElcoK/WISC/tree/c3779b387664b37cdfc49399202c74ab30531066) at research time. Python modules: `scripts/functions.py`, `scripts/utils.py`, `scripts/analyze.py`, `scripts/sensitivity.py`, `scripts/plotting.py`.
- [WISC original user guide](https://wisc.readthedocs.io/en/latest/) documents methods to build NUTS3 regional exposure, extract OSM buildings, intersect CORINE land-use classes, overlay storm gust rasters, apply fragility curves and compute building/region wind loss and sensitivity. The original repository README/config indicates legacy Conda/GeoPandas/Rasterio/GDAL/GIS dependencies; **not proven runnable in Python 3.13/3.14 or integrated with NextGen**. Avoid importing/updating old dependencies blindly.
- **Code rights:** repo `LICENSE` explicitly **MIT** (checked direct GitHub contents). Keep upstream copyright/license notice on any code reused, and pin individual source bytes and modifications. **Data rights differ**: source product historically uses OpenStreetMap building footprints under ODbL. The official C3S legacy Tier3 guides warn derived products using OSM need appropriate ODbL treatment; separate component-specific rights/legal review required for source data reuse/republication.

## Published scientific basis and comparison universe

- [Koks & Haer (2020), Scientific Reports 10:6866](https://doi.org/10.1038/s41598-020-63580-w), independently peer-reviewed. Building-scale wind damage for **53 historical storms across 21 European countries**, with validation on *reported* storm damages and a parameter sensitivity analysis. This paper is an important published **methodology and reasonableness reference**, not a location/policy list of Zurich properties.
- [Official 1979–2021 C3S winter windstorm indicators](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-indicators) DOI **10.24381/cds.9b4ea013** (older, separate dataset from 2025 C3S EWS DOI 10.24381/bf1f06a9). Historical **Tier 3 loss indicators** are **model estimates** on a building/NUTS3 basis per storm, not observed insurance claims. The [loss user guide](https://confluence.ecmwf.int/spaces/CKB/pages/253724006/Loss+indicators+Tier+3+Product+User+Guide) specifies OSM + CORINE 2012 + PAGER building-mix assumptions, six Feuerstein (2011) construction-dependent fragility curves, regional reconstruction-cost/GDP adjustment, historical footprints, and reported **USD** building losses. Note the unusual per-building identifier / NUTS3 vintage and risk of public OSM coverage gaps.
- The same legacy source's **Tier 3 risk indicator** is modelled expected annual damage (EAD), not event loss; the [risk guide](https://confluence.ecmwf.int/spaces/CKB/pages/253724009/Risk+indicators+Tier+3+Product+User+Guide) says it uses a **1,600-event SUBSET** of the separate C3S/WISC synthetic storm set. It is NOT the complete 22,980-event raw hazard event set, and 1,600 is NOT a count of simulation years. Do not treat risk and event-loss rows as interchangeable or sum both.
- Legacy Tier3 documentation was marked **unsupported on 2026-07-02 and slated for removal** from CDS. Make an archive/access-risk plan; do not assume these raw data will remain accessible. The newer C3S EWS (1940–present, monthly updated) offers annual storm counts, tracks and gust footprints, **not** a replacement Tier3 building-loss product with identical economics.

## First realistic modelling pilot (not yet implemented)

1. Select an exact physical storm/year / region in Germany, e.g. historical western/central EU wind event. Pin older WISC benchmark source or new EWS event footprint, source algorithm, 72h gust definition, original NetCDF/CSV hashes and 2D coordinates. Do not silently mix old 3-second wind gusts, new 10m maxima, grid downscaling and risk/event versions.
2. Create a **synthetic—not Zurich-owned—property inventory** from independently licensed/resolved building locations, building/land-use classes and replacement-cost assumptions. Prohibit unsourced claims of a real carrier × building position.
3. Run MIT WISC source or modern CLIMADA `ImpactFuncSet` independently, only after runtime/library version pinning, fragility interpolation and units tests. Compare its **modelled physical building losses** against the old C3S Tier3 building/region modelled losses where same events, exposure vintage and currencies are demonstrably compatible. This is **model-vs-model challenge**, not validation against observed insurance claims.
4. Use the paper's reported historical storm-loss comparators only with independent **holdout** controls: exact loss definition, observation year, currency/indexation, insured-vs-economic basis, country footprint and any Koks & Haer parameter fit leakage must be audited. The 2020 study uses some reported events for verification and could reuse them as tuning anchors; no automatic out-of-sample admission.
5. Connect the resulting per-physical-event per-asset **GUL** to native NextGen original policy/cedant, Inward Cat-XL and Retro in **shared chronological worlds**, preserving zero-loss years, annual frequency, multi-event years, peril correlations, physical event ID and original source bytes. Emit insurer/reinsurer gross and net **OEP and AEP**, with independent event-tape and annual-tape hashes (NextGen PR #280).
6. Compare independent Zurich *net* Europe-wind AEL/PML disclosure **only after** geographical group/LoB/currency/treaty net-scope mapping; never force synthetic gross/net scaling to match the single published target.

## Formal admission / blockers

- [x] Confirm exact **public OSS upstream** and its MIT code licence at checked commit
- [x] Pin original source method and *distinct* 2020 paper and old Tier3 guides
- [ ] Retrieve/hash/rights-review original permitted storm/OSM/exposure/Tier3 data; external CDS user login and terms acceptance may be required
- [ ] Verify original code runs in pinned research environment and compare independently against selected genuine source assets
- [ ] Verify contemporary per-asset building vintage/coordinate/taxonomy vs old 2018 OSM, old NUTS3 and 2012 CORINE, including missing-stock uncertainty
- [ ] Independently admit raw observed loss holdout; distinguish economic building damage from carrier insured or reinsured losses
- [ ] Replay physical events through exact native NextGen insurance/retro and reconcile Gross/Net OEP/AEP under original frequency semantics
- [ ] Explicit review before promoting source beyond metadata candidate; no production DB raw admission

**State:** qualified OSS+data **candidate**, scientific/rights/source runtime **not admitted**.


## Verified upstream execution risk: incorrect argument order (static source audit)

A second, *independent GitHub source-level review* identified a concrete blocker
to calling the original WISC top-level `analyze.exposure()` as-is:

- Original [`scripts/functions.py`](https://github.com/ElcoK/WISC/blob/c3779b387664b37cdfc49399202c74ab30531066/scripts/functions.py),
  Git blob `da6278d5dc61fb05dd89018fa854d77b36f16f2b`, declares
  `region_exposure(region, include_storms=True, event_set=False, sens_analysis_storms=[], save=True)`.
- Original [`scripts/analyze.py`](https://github.com/ElcoK/WISC/blob/c3779b387664b37cdfc49399202c74ab30531066/scripts/analyze.py),
  Git blob `79b311c58354bb478088ec547dc53b23c625f483`, passes
  `Pool.starmap(region_exposure, zip(regions, country_list, storms))`;
  the serial route passes `region_exposure(region, country, True)`,
  including on the `include_storms=False` branch.
- Thus the *country code string* is passed into boolean `include_storms`,
  and the `storms` indicator is passed into `event_set`. The intended
  source option and hazard semantics can be silently swapped. This is a
  deterministic **signature/argument mismatch in the original tracked code**,
  not an executed catastrophe-loss numerical failure. Do not run a source
  pipeline or claim original economics until this is fixed and separately
  regression-tested in a maintained, clearly identified adapter/fork.
- README prescribes `.environment.yml`, but this file is **absent at the
  checked upstream commit**. `scripts/functions.py` also imports GDAL,
  Rasterio, Rasterstats, GeoPandas, scikit-learn, NumPy and Pandas. A pinned,
  verified modern environment is therefore needed; do not assume installability
  merely because the published source code is MIT.
- Favor a clean modern adapter to CLIMADA's `StormEurope`/impact-function
  pathway as the primary compatible research engine, with WISC formulas,
  fragility assumptions and independently comparable Tier3 outputs as an
  **explicit model-vs-model challenger**, rather than blindly re-running the
  legacy `analyze.exposure()`.

This exact-head static inspection **does not** replace a native successful
WISC execution, a source-footprint or claims calibration, or verification
of an actual RNV/Zurich insured inventory.
