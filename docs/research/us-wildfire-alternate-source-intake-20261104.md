<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Alternative wildfire footprints and integrated event sources (2026-11-04)

**Discovery-only.** This document describes scientific-use candidates, not redistributable data, active authenticated API credentials, accepted source manifests or runnable CAT events. The five canonical candidate IDs are in [our generated source landscape](../../landscape/sources-wildfire-alternative-footprints-20261104.md).

## Why the original MTBS/FPA approach needs complements

In the [2024 FPA size-conditioned source-key audit](us-wildfire-size-conditioned-mtbs-linkage-20261104.md), 87,708 reported FPA occurrences included 415 MTBS_ID values; key availability was 1/43,445 for size A, 0 for size B and C, 224/388 for F, and 153/235 for G. The 2024 MTBS perimeter service separately includes prescribed/other types. These datasets must not be summed or assumed independent.

Original [MTBS FAQ](https://mtbs.gov/faq/fire-mapping) explains why the program targets large fires: mapping all ignitions is neither feasible nor its purpose; thresholds were chosen to capture approximately 95% of total annual **area burned**, not occurrence counts. The [2023 ICS-209-PLUS peer-reviewed research](https://doi.org/10.1038/s41597-023-01955-0) describes several nontrivial event-complex joins and **7,263 additional FIRED footprint matches** absent from MTBS. Such a published match statistic is a methodology lead, not an acceptance target for our 2024 data.

## Candidate triage by real access constraints

| Candidate | Scientific role | Original availability | Main blocker |
| --- | --- | --- | --- |
| [NASA FEDS 2012–2025](https://zenodo.org/records/22921773) | VIIRS-derived sub-daily fire progression | Zenodo metadata visible, **Files restricted**, 0 public bytes listed | Access cannot be assumed even if external catalogues suggest CC BY |
| [WUMI2026a Dryad](https://datadryad.org/dataset/doi:10.5061/dryad.63xsj3vd4) | Multiagency western US incident/perimeter deduplication and fire complexes | Dryad 2026 version, individual small fire-list archives; upstream `original_data.zip` ~100 GB | Publisher vintage/provenance and rights; many inputs duplicate FPA/MTBS |
| [FIREDpy global products](https://github.com/earthlab/firedpy) | MODIS derived event and daily boundaries for multiple countries | Public software, product availability/permission **varies by dataset/release** | Explicit PI permission for new unpublished products; 2021 half-pixel/CRS warning |
| [NASA iWED v1](https://doi.org/10.3334/ORNLDAAC/2452) | US 1992–2021 incident list + sources and quality notes | Open scientific metadata, ZIP may use Earthdata protected download | **No individual event lat/lon in v1**; state-level only |
| [JRC GlobFire v2](https://developers.google.com/earth-engine/datasets/catalog/JRC_GWIS_GlobFire_v2_DailyPerimeters) | Worldwide MODIS daily event boundaries, historical baseline | Earth Engine dataset page lists CC BY 4.0, 2001–2020 | Google Earth Engine access, event/geometry QC, same MCD64A1 lineage as FIREDpy |

**Important WUMI lineage trap:** The 2025 [WUMI2024a peer-reviewed paper](https://doi.org/10.5194/essd-17-7359-2025) discusses 1984–2024 and **22,234** western wildfires when fire complexes are disaggregated. The [Dryad DOI now also hosts WUMI2026a as an August 2026 updated version](https://datadryad.org/dataset/doi:10.5061/dryad.63xsj3vd4) and the landing page abstract has some old 2024a language. Do not silently equate the 2026 file with the 2025 methods/results or the older separate WUMI2 product. Pin a specific Dryad version, upstream product and asset SHA-256.

**Important FEDS trap:** The latest [2026 Zenodo FEDS record](https://zenodo.org/records/22921773) describes 375 m VIIRS active-fire processing every 12 hours. Published postprocessed `feds_lf_perimeter_YYYY.fgb` covers fires **above 4 km²**, while raw `feds_allfires_` / `allpixels` are not postprocessed and need additional identity/merge review. The record explicitly marks source files **Restricted**. A metadata listing is not a valid downloadable source asset. No use of FEDS data is approved here.

**Important FIREDpy trap:** [Original project README](https://github.com/earthlab/firedpy) says newer unpublished data products require creator permission before use in publications or public dissemination. It separately warns some Fall 2021 products may have a half-pixel shift and/or missing CRS. These issues require asset-level/edition-level review; do not infer software MIT/GPL (if any) applies to country-level data.

## Priority for usable NextGen model inputs

1. **First executable scope:** small, explicitly approved, versioned US wildfire parent-event and burned-area **research** cohorts, using existing FPA + MTBS keys and alternate WUMI **fire-list metadata**. Do not download the 100 GB WUMI upstream archive.
2. **Historical holdout/replication:** FIREDpy original existing 2024f country dataset or GlobFire daily historical perimeters only after source-specific rights and exact publisher byte/CRS receipt. MODIS derived from both is **not independent**. Compare event aliases, linked-perimeter multiplicity and unburned cells.
3. **State-level independent auditing:** iWED source notes can explain agency and reporting gaps but the first version **cannot** directly overlay exposure buildings.
4. **Access-resolution gate:** FEDS requires verified authorized file access, explicit permission and a pinned full postprocessed original product; until then it is **blocked**, not an active model source.
5. **Future insurance line:** Keep observed ignition, reporting unit, perimeter/burn fraction, structure damage (e.g. DINS), building TIV, vulnerability and insurance treatment as separate typed stages. Never infer insured loss from fire-area totals, FIRED/MTBS coverage or event multiplicity.

All five entries retain `evidence_checked`, `rights_review_status=not_reviewed`, `scientific_review_status=not_reviewed`, `admission_status=not_admitted`. Access/rights claims must be checked at the **original specific asset**, not just a DOI or a public GitHub code repository.
