<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# First genuine, licence-labelled European wind footprints for the NRW 10k physical portfolio

**2026-11-05 / Live original Daria source and 10,000-site historic wind overlay verified. No actual insured sites, wind vulnerability, CAT loss or OEP/AEP.**

The current public physical NRW portfolio has 10,000 sample source-geometry positions spread across all 53 2022 Kreise, with solely **hypothetical** R+V-like insurance policies and valuation (source Draft PR #1373). Its 20 × 13 synthetic 0.25° grid is **NOT an actual meteorological source grid**.

An independently researched **alternative to CDS-authenticated C3S EWS** is the original [Extreme Wind Storms Catalogue (XWS)](https://www.europeanwindstorms.org/). XWS states that its original footprint data are available in CSV and NetCDF under **CC BY 4.0** for research *and commercial use* with the attribution: **(c) Copyright Met Office, University of Reading and University of Exeter. Licensed under Creative Commons CC BY 4.0 International.** The original [XWS source data description](https://www.europeanwindstorms.org/database/dataDesc/) explicitly identifies a *rotated-pole* ~0.22° grid and a separate WGS84 long/lat-by-grid-ID CSV. The storm footprint data measure **the maximum 3-second gust over a 72-hour storm window in m/s**, which is a hazard intensity only, not a damage or insured loss.

## Strict original provider URLs (XWS Daria, 25 January 1990)

Official [storm detail and data download links](https://www.europeanwindstorms.org/cgi-bin/storms/storms.cgi?storm1=Daria) provide the following **four separate original files**:

1. Grid ID to public lon/lat: https://www.europeanwindstorms.org/database/dataDesc/grid_locations.csv
2. Daria lower 95% recalibrated storm footprint: https://www.europeanwindstorms.org/repository/Daria/Daria_biasL95.csv
3. Daria recalibrated **mean** storm footprint: https://www.europeanwindstorms.org/repository/Daria/Daria_biasMean.csv
4. Daria upper 95% recalibrated storm footprint: https://www.europeanwindstorms.org/repository/Daria/Daria_biasU95.csv

The independent XWS page also offers the original raw/uncontaminated windstorm footprint in CSV/NetCDF; do **not** interpret recalibrated mean/lower/upper 95% fields as three independent storms or stochastic yearly model draws. Keep all these variants under the **same original Daria physical event identity**.

The first original source-admission implementation is `research_runners/xws_daria_1990_original_csv_preflight_v0.py`: it acquires up to 24 MB of original bytes per file by **explicit --live** only and rejects changed final URLs, HTTP status, truncated/over-budget files, invalid original grid IDs or WGS84 lat/lon, inconsistent row populations, wind-unit domain errors, incomplete sources, and pointwise lower/mean/upper inversions. It stores **only original file SHA-256, byte counts, source variant summary and CC BY 4.0 attribution**. Full original CSV bytes never enter the repository or GitHub artifacts.

The [independent small live original-source CI](../../.github/workflows/rva-nrw-xws-daria-source.yml) runs fake-source negative fixtures first, then reads the original four XWS CSVs and uploads only that metadata receipt. It is not an authorized download of Copernicus C3S and does not require a CDS account.

## Scientific model gating and next spatial work

- A successful source-only XWS CSV preflight establishes a **publicly accessible, original and hashed historical European wind hazard field**, not its geographic attachment to 2022 NRW physical footprints. A subsequent separate source-space crosswalk must convert the supplied original public WGS84 **grid point coordinates** to a bounded nearest-cell/interpolation rule with explicit distance and missing-data diagnostics. The ~0.22° rotated source grid **must never** be read as the existing fake 0.25° C3S grid or passed to the ERA5 staging module without a bespoke typed source adapter.
- The exact 10k asset public physical locations and their fictional TIV can be used to calculate **event-conditional exposure to wind gusts**, but **HU building function/GFK does NOT reveal wall/roof construction, calibrated fragility or insurance coverage**. The output must be *site gust in m/s only*, not GUL/IL/RI or an OEP/AEP. A hypothetical damage response would need a separate explicitly fictional parameterized test branch; a scientifically admitted Germany wind vulnerability needs independent licence and validation.
- XWS has a deliberately **extreme-storm-selected** catalogue (historically 50 storms), not a complete unbiased calendar of all European storms or a stochastic yearly loss table. Its physically selected event sample is **not** annual frequency or a 10k-world catastrophe distribution. Storm clustering, out-of-sample baseline, all zero storm-years, 72-hour overlap, and annual model set calibration must be established independently.
- XWS and C3S storm IDs / source eras / downscaling methods are unrelated without an original physical event crosswalk. A year or familiar storm name alone cannot justify reusing a vendor event ID or vulnerability calibration.
- If the primary-source preflight succeeds, implement a **source-specific WGS84 XWS lat/lon nearest-grid overlay** on the existing 10k public HU locations. Preserve nearest-point distances, exact XWS grid row IDs, full XWS input digests, and same physical event ID across the three uncertainty variants. Audit the 53-Kreis population and EUR 4,826,029,500 fictional total building value, but **never** present gust-weighted buildings as actual R+V insured risks.
- Before a native Oasis/NextGen Germany CAT model can run: independently source the **original wind vulnerability**, coverage/values/terms, event frequency/occurrence, and financial model crosswalk. Only then run pathwise wind damage, insured financial module, reinsurance and valid annual EP curves.

**No source-specific loss calculations, licence transfer, registered insurer-site data or production admission have occurred here.**

## Original-source Daria spatial application (first 10k hazard overlay code)

A second source-specific implementation now exists:
`research_runners/rva_nrw_xws_daria_10k_original_gust_overlay_v0.py` and
`tests/test_rva_nrw_xws_daria_10k_original_gust_overlay_v0.py`.
It streams four actual original XWS CSVs in ephemeral CI storage and obtains the
already-validated, source-geocoded 10k fictional NRW OED from the prior successful
[original NRW source run #42097472463](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42097472463).

The spatial method **uses the original WGS84 grid-point lon/lat from XWS**, not
the invented 0.25° C3S-style grid. It searches nearby half-degree geographical
buckets, chooses the minimum exact spherical great-circle distance to the original
source point (tie-break by original integer grid ID), and **rejects** any point
with no original grid point within 45 km. The original source's ~0.22° rotated
grid is only a provenance descriptor; the algorithm does not assume its native
rotated-pole coordinates are already ordinary WGS84.

Outputs after a passing live original CI will be:
- 10,000 *fictional* NRW policy/sample asset IDs with matched **original Daria
  1990 3-second wind gusts (lower 95%, mean and upper 95% in m/s)** and exact
  original XWS grid ID and nearest-point distance;
- a 53-Kreis summary of fictional building value exposed to the **same**
  original Daria event, including source mean gust >=25 m/s;
- original four full-file XWS SHA-256s, prior full original HU22 archive SHA,
  XWS CC-BY-4.0 attribution and explicit false model/insurer/yearly-event claims.

No original XWS grid/footprint files are committed or uploaded to GitHub
artifacts. The public source-derived 10k *site-gust* table is shared under
its original CC BY 4.0 attribution. A single original **1990** historical storm
on **2022** public building locations with entirely fictional **2025** insurer
values is a retrospective *counterfactual* hazard exposure; it cannot be
interpreted as historical insured claims, today's underwriting exposure,
a calibrated conditional damage model, a sample of independent years or
a premium / solvency-risk estimate.

**CI admission:** The exact live original-source and 10k join workflows must
show a completed SUCCESS before any site-gust artifacts or numerical results
are called verified. A failed source row schema, drifted original URL,
missing county, unusually distant grid mapping, source uncertainty inversion
or source artifact mismatch must remain NO-GO.

## Verified original source and 10k real-source hazard replay (2026-11-05)

**COMPLETED** original-source and 10k WGS84 building-gust overlay [GitHub run #42112975393](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42112975393). The full repository CI plus the XWS, source HU, R+V OED and Berlin BLD4 workflows all passed at the source-replay head before subsequent metadata-hardening commits.

Independently calculated and pinned **FULL original files**:

| XWS original file | Complete bytes | Full SHA-256 |
| --- | ---: | --- |
| `grid_locations.csv` (source column is literally `Latitde`, not `Latitude`) | 550,415 | `decb09d473db9086df7a497bcebc95641238d4ee365ff26d8e83c266a6f32599` |
| `Daria_biasL95.csv` | 350,030 | `4381de5fdb5e66489efde09ac587e295b93906cac643325ad5517a278d5e2bff` |
| `Daria_biasMean.csv` | 350,061 | `34b9c02768aa6f54aa541e185381e4735f3b2cd852fc23a724ddc00c301a1d50` |
| `Daria_biasU95.csv` | 350,179 | `8b63a95adf0961da00c1e8874fbb99a49cd38b58de6263f8c4f1c65637cc6007` |

The original XWS reference grid has **28,124 longitude/latitude positions**. From the entire source grid, maximum modelled gust values across lower/mean/upper variants are respectively **72.317, 113.005, 176.587 m/s**. The upper statistical 95% field contains **39** original points above 150 m/s; these must **not** be clipped or silently ingested into NextGen's 0–150 m/s physical wind VLT domain. XWS original grid metadata uses an actual misspelling `Latitde`, admitted by an exact provenance-specific parser only.

[Derived 10k public-source building gust research artifact](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42112975393/artifacts/13455338570), not original XWS raw CSVs: **10,000 public 2022 NRW building candidates**, all **53 NRW Kreise**, **79 original XWS grid locations assigned**, maximum nearest original source-grid distance **17.11 km**. The 10k physical-building site sampled wind gust distribution in m/s:

| Daria 1990 gust branch | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| Lower 95% | 18.743 | 20.388 | 21.985 |
| Recalibrated mean | 27.852 | 30.339 | 33.361 |
| Upper 95% | 41.378 | 45.162 | 50.964 |

All 10,000 fictional exposure sites have Daria **mean gust ≥25 m/s** in this original nearest-grid replay. Aggregate value of the **explicitly imaginary** underlying 2025 R+V-like policies remains **EUR 4,826,029,500**; this is an ecological counterfactual on 2022 public physical buildings, not 1990/2025 R+V observed insurance liabilities. The source uncertainty branches are the **same physical storm**, not 3 independent storms or 3 simulated years. No German annual rate, calibrated damage, original insurance, RI or EP has been calculated.

Implementation file `research_runners/rva_nrw_xws_daria_10k_original_gust_overlay_v0.py` now **requires all four exact independently recorded original source file byte counts and SHA-256s**. Upstream source mutation will fail closed rather than silently change the research data basis. The CI replays the original public source in an ephemeral runner and never republishes raw original site-grid CSVs, but it can publish the 10k derived site-gust table with explicit CC BY attribution and a no-CAT-loss manifest. Licence citation required: **(c) Copyright Met Office, University of Reading and University of Exeter. Licensed under Creative Commons CC BY 4.0 International.**

## Observed exact-head original-source run — 2026-11-05

[GitHub Actions #42112975393](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42112975393) completed **SUCCESS** on source-branch commit `599cc4c82dd1fcd1a1b9caa9a0fe625bdf261ac5`, including original four XWS CSV retrieval/parsing, original 2022 NRW 10k research-artifact retrieval, strict geographic matching, synthetic negative tests and two limited research artifact uploads.

The actual live receipt printed in the workflow job log reports:

| Measured/declared output | Verified result |
| --- | ---: |
| Original XWS published grid points | 28,124 |
| Public 2022 NRW building candidates with original XWS gust assignment | 10,000 |
| Source 2022 NRW administrative counties represented | 53 |
| Distinct original XWS grid points matched | 79 |
| Maximum nearest original XWS grid distance | 17.11 km |
| Sites whose Daria-1990 *mean 3-second gust* is at least 25 m/s | 10,000 / 10,000 |
| **Invented** 2025-like building values attached to those candidates | EUR 4,826,029,500 |
| Genuine carrier losses or annual occurrence probabilities | **None** |

The provider's `daria_mean`, `daria_lower95` and `daria_upper95` are **alternative estimates for one historical physical event**, not three storms or stochastic years. The observed 10k threshold is a property of the specifically selected, historic extreme storm and fictional candidate buildings: it does not establish a hazard return period, damage ratio or real R+V portfolio composition. The 1990 / 2022 / 2025 source-vintage mismatch is material.

The **actual full downloaded original CSV byte identities** in this run (SHA-256 calculated on the complete source bytes, not publisher-signed checksums) were:

| Exact XWS original input | Bytes | Observed SHA-256 |
| --- | ---: | --- |
| `grid_locations.csv` | 550,415 | `decb09d473db9086df7a497bcebc95641238d4ee365ff26d8e83c266a6f32599` |
| `Daria_biasL95.csv` | 350,030 | `4381de5fdb5e66489efde09ac587e295b93906cac643325ad5517a278d5e2bff` |
| `Daria_biasMean.csv` | 350,061 | `34b9c02768aa6f54aa541e185381e4735f3b2cd852fc23a724ddc00c301a1d50` |
| `Daria_biasU95.csv` | 350,179 | `8b63a95adf0961da00c1e8874fbb99a49cd38b58de6263f8c4f1c65637cc6007` |

These hashes fix the reproducible **observed source version** in permanent Git metadata after time-limited Action artifacts expire. They do not grant broader reuse rights, prove the provider published these digests, or imply the storm has an independently estimated annual frequency.

Generated research artifacts, temporarily available for 14 days (not committed source files):

- [Source-grounded public-site historical gust ZIP, artifact #13455338570](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42112975393/artifacts/13455338570). It contains derived site/county gust and provenance only, **not** an insurer loss table.
- [Original four-file XWS checksum and rights receipt, artifact #13454413160](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42112975393/artifacts/13454413160). It does not include the publisher's original CSV bytes.

**Next actual model gate:** Independently review a Germany-relevant wind-intensity→damage vulnerability response, mark synthetic scenario assumptions separately from any scientifically calibrated response, and only then calculate *event-conditional direct damage* on the matched sites. A single selected Daria storm, even with real gust bytes, is not a basis for annual gross/net OEP, AEP or pricing.
