<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GEM September 2026 ↔ EIA-860 2025: release, rights and unit-grain preflight

**Research only. No GEM September 2026 original workbook acquired, no EIA↔GEM asset match confirmed, no licensed GEM raw rows committed, no insurer exposure, no model admission.** Continuation of [issue #1251](https://github.com/pokekarten/OpenCatastrophe-data/issues/1251), which separately establishes real 2026 EPA FRS ↔ EIA annual 2025 plant-ID/state concordance for 15 Delaware source-reported programme IDs.

## Primary-source access and why no legitimate direct workbook was claimed

- Official [Global Integrated Power Tracker](https://globalenergymonitor.org/projects/global-integrated-power-tracker) declares September 2026 as the latest downloadable GIPT release. The page's actual **Download data** area asks for an organization/affiliation and intended use, including an explicit acknowledgment of GEM's license, before **Submit and Download**. This is an **interactive download/terms gate**, not a direct stable original `.xlsx` URL. Research can verify the public page and methodology, but must not invent a downloadable origin, impersonate a user, or submit their contact details/terms on their behalf.
- Official [September 2026 GIPT methodology](https://www.gem.wiki/Global_Integrated_Power_Tracker_Methodology) describes a three-sheet XLSX: `Power facilities`, `About`, `Regions, area, and countries`. The principal **unit or phase** key and the **GEM location ID** are different grains. A plant/project location may contain more than one unit/phase. Thermal generation is usually modeled at individual generator unit, wind/solar by phase, hydropower by plant. The technology-specific tracker inclusion threshold and source-vintage are not uniform; 2026-09 GIPT aggregates source-trackers from several earlier 2026 releases.
- The GIPT methodology documents `Other IDs (unit/phase)`, but **does not establish that every row has an EIA-860/ORIS identifier**. A name match, geographic proximity, U.S. state string, `EIA` substring or arbitrary `ORIS 123` is not an independent cross-ID. The *only* format recognized by the research-only normalized-text preflight below is an explicitly structured `EIA-860: 123` token; **this grammar is an intentionally conservative audit convention, not a claim that the GEM workbook actually publishes such token syntax**. A zero-hit result is a parser/out-of-scope outcome, not proof of no true plant relationship.
- **GEM's actual source license exception matters:** The methodology says CC BY 4.0 for GIPT except rows with a **TransitionZero `TZ ID` in `Other IDs (unit/phase)`**, which are partly/wholly based on TransitionZero Solar Asset Mapper August 2025 and subject to **CC BY-NC 4.0**. Commercial insurance modeling cannot automatically include the NC portion. Even a row without an observed `TZ ID` remains **rights unverified** until original row provenance, publisher terms and attribution obligations are reviewed. GEM's [CC BY 4.0 text](https://globalenergymonitor.org/creative-commons-license) imposes attribution and other conditions; no rights are granted merely by our script.
- **Alternate public GIS service is not the 2026 original.** The [ArcGIS `Global_Integrated_Power_v1` FeatureServer layer](https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/Global_Integrated_Power_v1/FeatureServer/0?f=pjson) has `GEM_location_ID` and `GEM_unit_phase_ID`, but its public metadata lists **dataLastEditDate = 1746548005145 (2025-05-06 UTC)** and `schemaLastEditDate = 1771453731876 (2026-02-18 UTC)`. A 2026 schema timestamp is **not** a 2026 data vintage. The displayed field list lacks a verified original September 2026 `Other IDs (unit/phase)` column and has no source-specific licensing override; **it cannot supply a commercial-rights-clean September 2026 EIA↔GEM join.** It is a legitimate *legacy research and API metadata canary*, not an accepted replacement workbook.

## Executable bounded offline contract

[Research runner](../../research_runners/gem_gipt_eia_rights_grain_v0.py) and [synthetic tests](../../tests/test_gem_gipt_eia_rights_grain_v0.py).

The runner accepts a **caller-prepared normalized CSV research projection**, NOT an authentic publisher workbook and NOT a redistribution channel:

```text
gem_unit_phase_id,gem_location_id,country_area,other_ids_unit_phase
```

Additional restrictions: exact `2026-09` vintage, explicit lowercase SHA-256 of the local normalized projection, optionally the separately recorded **claimed** original workbook SHA-256 (not cryptographically verified), at most 1.5 MB/10,000 rows, exact columns, unique unit/phase key, preserved shared-location cardinality and aggregate-only diagnostic. `United States` is the sole accepted U.S. country-area spelling in this version; other country names do not become U.S. plant evidence. A missing GEM location key cannot establish plant identity.

The test contract deliberately **rejects modeling promotion**. If `Other IDs (unit/phase)` carries a `TZ ID`/TransitionZero marker, that row is quarantined. If a GEM location contains **any** TZ-marked unit, the **entire location-level EIA claim remains quarantined** pending segregation/legal review; this avoids admitting apparently safe sister units as a surrogate for the same commercial site. Even a non-TZ location is labeled **still rights unverified**, not commercial-permitted. A source textual `EIA-860: NNN` match is **only a publisher-ID research claim**, not an independent cross-provider identity proof; its cardinality across GEM *locations*, not across unit rows, is measured against the previously confirmed 15-ID Delaware EPA/EIA pilot.

```bash
python -m unittest tests.test_gem_gipt_eia_rights_grain_v0 -v
python research_runners/gem_gipt_eia_rights_grain_v0.py \
  --projected-csv /approved/private/GIPT-2026-09-normalized-slice.csv \
  --projection-sha256 EXACT_SLICE_SHA256 \
  --native-workbook-sha256 EXACT_ORIGINAL_SHA256_IF_SEPARATELY_CHECKED \
  --release 2026-09
```

The CLI is read-only and offline: no GEM download, no source-row writes, no public row IDs, no name/location/TIV leakage, no database mutation. Do not insert placeholder hashes as real evidence.

## Completion and next empirical requirements

1. Obtain the original GEM September 2026 workbook through the publisher's legitimate download process, under the authorized download user's own acknowledgment of the terms and a documented permissible use. **Do not bypass the form or assert credentials/approval.**
2. Freeze exact source workbook URI/capture time/original SHA-256, sheet names, real `Other IDs (unit/phase)` tokens, original source licenses, and entity/location/unit IDs. Keep raw data outside public Git; record a rights-aware citation and checksum receipt only.
3. Run a **small bounded read-only** U.S./Delaware 15-plant source cohort and partition source rows with `TZ ID` before attempting any EIA/GEM identity join. Trace EIA IDs via explicit original publisher or independent regulator evidence; do not use name or distance alone.
4. For each EIA ID, report actual **location-level** 1:1 / 1:n / n:1 cardinalities with lineage; units within one GEM location are not separate buildings. Any conflicted or license-contaminated site stays in research-only quarantine.
5. Independently verify parent/owner/GEM entity IDs against exact as-of legal sources (GLEIF where possible). Commercial model use, original-source admission, insurer assignment, TIV, business-interruption loss and inward/outward treaty integration require their own controls. **None are currently authorized by this gate.**

**Operational status 2026-11-04:** source URL/methodology/rights and a stale legacy GIS service have been inspected; the September 2026 original GEM workbook remains unavailable through a publicly verified fixed-download URI. This PR implements safeguards, not a fabricated set of matched owners or facilities.
