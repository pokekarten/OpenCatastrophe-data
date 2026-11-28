<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V-like NRW 2022 HU physical 10k geocoded OED — original-source audit and toy valuation

**2026-11-05 — source-geometry full input delivered; carrier data remain fictional.** This artifact is *not* an observed R+V Allgemeine insured-site inventory, policy valuation or a native German Oasis CAT model run. The completed source-to-OED experiment is in [Draft PR #1373](https://github.com/pokekarten/OpenCatastrophe-data/pull/1373).

## First verified source-full scan

- Official primary Geobasis NRW [historical 2022 Hausumringe ZIP](https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_hu_shp/2022_hu_EPSG4647_Shape.zip). Exact downloaded original 901,092,946 bytes; **full original SHA-256** `10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da`. Original file size, four original ZIP source members and their CRCs checked on the full 2022 archive, which was deleted from GitHub temporary runner disk before research output publication. The publicly posted directory labels DL-DE Zero 2.0. Scientific source approval and any third-party licence exclusions remain independent.
- Successful completed original-source [GitHub Actions run 42097472463](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42097472463). Downloadable [derived research artifact 13447603258](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42097472463/artifacts/13447603258), 14-day GitHub retention through 2026-11-19. **Original 901MB external provider ZIP was never uploaded to GitHub.**
- Sequentially inspected all **11,232,755** original SHP/DBF rows, including physical object IDs (not copied into the emitted OED), original AGS (municipality prefix crosswalk), original GFK composite building function and original polygon coordinates in **EPSG:4647**. Pinned pyproj 3.7.2 transforms valid sample polygon interior points to WGS84, Shapely 2.2.0 checks topologies/areas.
- Composite ALKIS GFK **31001_XXXX** (object type **31001** mandatory): **4,425,094** source objects are narrowly classified *residential-related function candidates* using 2017/2021 official codebooks. **4,196,125** source rows belong to selected specifically known nonresidential functions; **1,428,925** malformed-function rows, **1,173,275** unmapped-function rows, **9,336** special/institutional candidate rows remain quarantined. This is *not* a reconciled residential building census or an observed insurer exposure count. Candidate polygon failures are counted only among priority-eligible sampled geometry, not the full population.
- Selected exactly **10,000 unique** official public physical building candidates across **all 53 official NRW 2022 Kreis codes** using reproducible, hashed-OI reservoir priorities, exact per-Kreis conditional quotas from separate **fictional** insurer distributions. The resulting output file includes **10,000 OED 5.0.0 location rows and 10,000 aligned fictional accounts**, `physical_candidate_evidence.csv` with original GFK, measured ground footprint area and SHA256 of original OI (not original source OI or individual customer data), and `manifest.json` with full original archive identity/source audit and output SHA-256. Official pinned `ods-tools==5.0.8` format gate passed.
- Selected 10k original HU function mix includes **9,103** `31001_1010` Wohnhaus; **251** `31001_1110`; **217** `31001_1120`; **184** `31001_1100`; other vetted mixed-use/farm residential function candidates. A historic source GFK function label does **not** confirm exact occupancy, footprint part/parent identity, actual insurer membership, roof material or structural vulnerability.
- Fictional original valuation controls from the NRW source-to-OED sample: **EUR 4,826,029,500** building TIV for these 10k fictional accounts. This is a toy value under the pre-existing 2025 issuer national control and age-archetype scenario, **not R+V NRW actual insured TIV**.

## Measured physical footprint ground area vs hypothetical rebuilding TIV

The selected physical footprint area is an original polygon ground-area observation, **not** actual gross floor area (storeys unknown), construction year, insurer sum insured, replacement-cost contractor survey, land, contents or restoration costs. Source-ground-footprint sample:

- 10,000 sample area observations, **mean 122.265851 m²**, **median 103.325 m²**.
- **Three independent, explicitly invented** storey × EUR/m² replacement-cost sensitivities. All keep **the exact same 10k public physical coordinates, fictional location/account IDs, county assignments and source object evidence**. Only `BuildingTIV` changes:

| Counterfactual storeys × rebuilding cost | Synthetic total TIV for 10k buildings |
| --- | ---: |
| 1 storey × EUR 1,800/m² | EUR 2,200,785,318 |
| 2 storeys × EUR 2,200/m² | EUR 5,379,697,444 |
| 3 storeys × EUR 3,000/m² | EUR 11,003,926,590 |

Full reproduction code: `research_runners/rva_nrw_hu22_geocoded_area_rebuild_tiv_v0.py`. Its unit tests check strict source manifest SHA/CRC/admission boundaries, stable coordinates/IDs and policy counts across all scenarios, that the official function code maps into the approved residential-candidate categories and that the stored toy TIV sum exactly balances row-level amounts. This is **not a fitted cost model**; no factual estimate of actual R+V insured values or true national/NRW CAT risk is supported.

## Exact source, vintage and insurer boundaries

The 2022 official HU physical candidate population is distinct from the **2022-05-15 Census 4,042,220 NRW buildings with living space**. Neither is the **2025 R+V Allgemeine solo national 1,060,546 year-end building policies** or the **2026 MaStR-derived 876,684 registered NRW building PV generating units**. The latter are generating units, not rooftop counts or insured PV endorsements. Source date/administrative boundary-year reconciliation and complete codebook year matching are **still not independently admitted**. Policy-to-physical-site correspondence is purely *hypothetical*.

## Next admission tasks

1. Audit original 2022 HU physical building candidate selection: municipality-to-Kreis crosswalk, duplicates/parts/parent geometry, complete CRS and GFK version, polygon area source quality by Landkreis; geographically held-out comparisons to another original/licensed source and Zensus denominator alignment with coverage uncertainty.
2. Add a genuinely grounded source for per-site gross floor area/actual storeys, rebuilding-cost index vintages and construction material; preserve unobserved/uncertain by building. Stop treating assumed storeys/costs as measurements.
3. Run a **Germany-capable native Oasis hazard/event/vulnerability** contract gate, model-valid construction/occupancy mapping, explicit fictional insurance financial policy terms (deductibles/limits), fictional reinsurance with common loss samples and matched events/periods. Only then can gross/net OEP/AEP be scientifically evaluated. A syntactically valid OED source is **not** a model-valid German CAT exposure.
4. **Full ~901MB source acquisition is now manual-only** using explicit `workflow_dispatch` on `.github/workflows/rva-nrw-hu22-full-one-shot.yml`, to prevent expensive downloads on every normal PR commit. The previously successful first full source run is already documented; further normal PR tests do not need repeating it.

**Status:** Source-verified, geometrically geocoded public building-candidate **synthetic** OED book available; **actual insurer sites/TIV/coverage and German CAT GUL/IL/RI/OEP/AEP remain NO-GO**.


## Independent 10k original-footprint versus fictional-TIV diagnostic (2026-11-05)

A separate **full-artifact** audit independently opened the immutable successful [original physical-source 10k artifact #13447603258](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42097472463/artifacts/13447603258) (ZIP digest `5b0055ce71314f7d7baf4f67008cd4abba3df28a4bce0690bbe9521a3cc35757`), checked **all three** published CSV SHA-256 digests against `manifest.json`, matched 10,000 fictional location, account and original physical-candidate-evidence IDs, retained 53 Kreis codes and the original 4.8260295bn EUR **toy** national NRW sample TIV, and calculated the following **diagnostic only**:

| Metric on 10,000 fictional policies joined to public physical footprint candidates | Measured or computed value |
| --- | ---: |
| Original HU physical ground footprint p1 / median / p95 / p99 | 24.83 / 103.32 / 250.35 / 470.45 m² |
| Existing invented OED BuildingTIV ÷ *ground footprint* p1 / median / p95 / p99 | 737.63 / 3,903.85 / 14,641.60 / 24,765.15 EUR/m² |
| Fictional cases above 10,000 EUR per **ground footprint** m² | 1,137 / 10,000 = 11.37% |
| Fictional cases below 2,000 EUR per **ground footprint** m² | 1,488 / 10,000 = 14.88% |
| Original measured ground footprint area vs **invented** OED BuildingTIV (Pearson) | **−0.003029** |
| Same pair, rank correlation (Spearman with average-rank ties) | **−0.002655** |

**Interpretation:** The initial OED 10k `age_archetype` valuation is effectively *uncorrelated* with measured physical footprint area; it is an intentional, source-unfitted fictional assignment, not evidence of the market or insured valuation. Rates above 10,000 EUR per *ground* m² are **not inherently an error**: footprint area is not usable gross floor area, and unknown storeys, partial structures, building category and building quality matter. But the huge resulting fictional range is a quantitative reason to prefer the existing **three area × explicitly assumed floor count × rebuilding-cost** sensitivity variants for future structural exposure analyses, retaining the same geometry and county weights. Their 2.2008–11.0039bn EUR toy TIV spread remains scenario uncertainty, **not a source-calibrated confidence interval**.

The full artifacts, original HU22 source ZIP SHA and 10k sample IDs remain distinct from real R+V premises. No individual original source OI identifiers, original third-party ZIP, R+V customers, personally attributed addresses or hazard/treaty risk claims were added to this note. For a future defensible primary valuation, independently source/pin floor counts or a probabilistic height/story proxy, functional occupancy, region-specific indexed rebuilding rates, construction, and separately validate the reconstructed *gross floor* value basis. Never calibrate a Germany wind vulnerability function from a near-zero correlation of fictional TIV to physical footprint.

**Availability note:** The original GitHub Actions artifact currently has 14-day retention; the pinned output source/hash and derived *aggregate-only* statistics must be preserved independently of that retention window.
