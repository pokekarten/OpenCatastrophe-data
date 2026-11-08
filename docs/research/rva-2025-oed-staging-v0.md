<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V-like 2025: deterministic synthetic OED staging v0

**Scope:** research only. No real R+V insured site, insured TIV, financial contract, territory distribution, outward treaty or calibrated Germany model is identified. The carrier anchor is R+V Allgemeine Versicherung AG **solo** and its 2025 connected-building **year-end contracts** and HGB **annual written premium**, not the whole R+V group.

## Source evidence and hypothetical assumptions

- Reuse the already source-pinned Destatis Zensus 2022 original 400-Kreis physical building counts and ten age classes, and the original 2025 R+V solo HGB observations of **1,060,546 building contracts / EUR 997,710,000 booked annual gross written premium**.
- Reuse the existing original-source and actuarial-scenario validator in research_runners/rva_2025_kreis_age_source_sensitivity_v0.py; it checks original source hashes and all 400 regions.
- Alternative **fictional** distribution cases are equal hypothetical age affinity; pre-1950 age-group affinity 1.5x; post-2000 affinity 1.5x. The age variables describe the physical 2022 population, not actual insurer contract ages, materials or roof age.
- Three mutually separate **invented** BuildingTIV-per-policy valuations: LOW EUR 250,000, CENTRAL EUR 450,000 and HIGH EUR 750,000. These values are NOT inferred from R+V premiums or independent insured appraisals. One fictional contract equals one fictional location/building **solely in this experiment**; no assertion of R+V location or asset totals.
- Default deterministic **10,000-contract sample**, largest-remainder allocated over all 400 x 10 county-age cells, with exact conservation of sample counts. --sample-size 0 exports all **1,060,546** hypothetical policies, on a machine with sufficient disk/compute. **Never** scale sampled claims into net losses by multiplication when terms are nonlinear.

## Execution from the repository root (Python >= 3.11)

- Default: python research_runners/rva_2025_oed_staging_v0.py /tmp/rva-like-oed-10k
- Full fictional alternative: python research_runners/rva_2025_oed_staging_v0.py /tmp/rva-like-oed-full --case HISTORIC_PRE1950_AFFINITY_1_5X --valuation high --sample-size 0
- Offline tests: python -m unittest discover -s tests -p test_rva_2025_oed_staging_v0.py -v

Output directory **must not already exist**. Result files:
1. location.csv: OED 5.0.0 columns, one entirely fictional building/policy per location; country DE, EUR, synthetic peril group WW2 (wind without storm surge), invented BuildingTIV. Other TIVs zero only as a scenario choice. **Latitude and Longitude intentionally empty**.
2. account.csv: matching unique fictional account and policy, EUR, WW2. It does not assert actual deductibles, limits or coverage.
3. cohort_receipt.csv: all 4,000 county-age cells, exact published 2022 physical age counts, hypothetical national 2025 insurer distribution, and extracted sample counts.
4. manifest.json: original national observed accounting controls, exact input and output SHA-256, fictional assumptions, row/TIV counts, sample vs full status, and mandatory **NOT_GEOLOCATED_NOT_MODEL_READY** gate.

## Prerequisites before ANY native Oasis model run

1. **Spatial model input:** add independently licensed candidate physical building coordinates (BKG VG250 county polygon edition check, Overture/ALKIS building polygons, de-duplication, correct risk-unit and structural classes). Do not use county centroids as if they were the 1,060,546 insured R+V addresses; do not silently invent point positions. Check 2022 vs later regional boundary vintage and source rights. BKG 2026 VG250 product: https://gdz.bkg.bund.de/index.php/default/open-data/verwaltungsgebiete-1-250-000-stand-01-01-vg250-01-01.html
2. **Vulnerability mapping:** map verified or clearly hypothetical occupancy, building material, area, roof, floor and construction year to the **exact** selected German hazard/vulnerability model taxonomy. Matching Oasis column names does not mean valid model lookup.
3. **Valuation:** source independent replacement cost, size and insured cover values as separate distributions; scenario stress, not premium to TIV conversion. Distinguish household/commercial housing, farm, mixed-use and PV; building year alone is not vulnerability.
4. **Financial model:** after independent German peril catalogue and a fully source-licensed model, demonstrate native GUL -> insured gross IL -> fictional outward QS / CAT XL -> net ORD and annual OEP/AEP on identical physical event, period and sample IDs. Tests in OpenCatastrophe PR #23/#24 currently retain strict numerical/parity blockers.
5. **Database identity:** read-only Neon readiness in OpenCatastrophe-data PR #1372 on 2026-11-05 had 0 verified solo R+V insurer legal identities, 0 source-linked exact property financial metrics and 0 company-linked exposures. No production DB mutation is authorized by this research script.

**External validation:** This branch's offline synthetic exporter tests are not ODS_Tools 5.0 compatibility certification, a native Oasis GUL/IL run or a calibrated model. Original 400-Kreis source integration requires an actual clean checkout run. Never label the resulting synthetic portfolio as actual R+V insured buildings or insurer gross/net EP.


## 2026-11-05 continuation — heterogeneous fictional valuation and exact-head CI gate

The original flat EUR 250k/450k/750k per site was deliberately insufficient as a realistic loss severity distribution. The exporter now includes an **opt-in** `--valuation-pattern age_archetype` case, while preserving `flat` as the reproducible baseline.

- **Age factors:** ten explicitly invented percentages `[135,125,110,95,90,90,100,110,115,120]` applied to the **2022 published building-age classes** as synthetic valuation *sensitivity*, NOT measured property values, roof-condition rating, construction material or natural-catastrophe vulnerability.
- **Fictional building mix:** stable SHA-256 synthetic-policy-ID pseudo-assignment to four categories: 45% small residential at 60% of base value; 42% standard at 100%; 10% multiunit at 260%; 3% mixed residential at 175%. Frequencies are **assumptions, not fitted using census or R+V**. Independent account/insured-site multiplicity still unknown. Real occupancy must not be assigned from these categories without original building evidence.
- The resulting `BuildingTIV` differs by fictitious class and age, with integer-euro arithmetic. `cohort_receipt.csv` now includes the **sum of exported hypothetical TIV** per Kreis × construction-age cell; `manifest.json` includes the exact assumed factors, achieved archetype counts and full sample TIV. Neither the national HGB premium nor a census building count was turned into an insured value.
- Local synthetic test-fixture executed with 10,000 artificial policies: **4/4 tests PASS** (including new nonuniform exact conservation test). A self-contained fixture with **artificial county identifiers** has 10,000 site/policy rows, 4,000 cohort rows, 32 unique assumed TIV values and EUR **4,899,740,625** toy sample TIV. This result is **NOT** the actual 400-Kreis source-aligned export and not calibrated.
- New [source-authenticated + official OED compatibility gate](../../.github/workflows/rva-2025-oed-staging.yml) checks out this PR, executes original source validators and exports exactly 10,000 synthetic contracts, then validates against pinned `ods-tools==5.0.8` and source/output SHA receipts. The [format checker](../../research_runners/validate_rva_2025_oed_staging_ods_v0.py) rejects missing/shifted original issuer and census source controls, changing county/age counts or claiming geocoding/production readiness. **Workflow success not yet recorded for this PR.**

Example of the explicitly invented heterogeneous alternative:

```bash
python research_runners/rva_2025_oed_staging_v0.py /tmp/rva-like-10k-mixed \
  --case HISTORIC_PRE1950_AFFINITY_1_5X \
  --valuation central --valuation-pattern age_archetype --sample-size 10000
```

## Next geospatial *source-admission* bridge (not implemented)

Preferred restricted pilot is the known **53 NRW Kreis** public Census/PV scope before widening to Germany. Take one exact original, date-pinned Overture Maps buildings release (2026-10-21.0 as catalogued) from original public GeoParquet: [official query examples](https://docs.overturemaps.org/getting-data/), [building footprint/roof/floor schema](https://docs.overturemaps.org/schema/reference/buildings/building/), [building licence ODbL](https://docs.overturemaps.org/guides/buildings/). Overture original building polygons represent public **physical opportunity**, not R+V insurance exposure. Footprint/roofprint uncertainty, incomplete roof/floor attributes and per-feature source attribution must be preserved.

Join verified candidate footprint geometries to **correct-vintage** BKG Kreis administrative polygons (not guessed AGS strings or postal-code centroids), reject county-boundary or geometry mismatches, repeated building part vs parent duplication and unsupported roof/vulnerability taxonomy. Use actual point-on-surface only after valid polygon and official region membership checks. Never write individual third-party building rows to this public Git repository or Neon without licensing and identity review; keep original external bytes separate with SHA receipts. Assign fictional insurer selection probabilities *after* this spatial opportunity layer and report these jointly with uncertainty.

Physical footprints still do not prove building floor areas, replacement costs, insurance coverage, company selection or catastrophe fragility. A final German Oasis native-run gate must additionally independently admit peril-specific event catalogue, compatible vulnerability IDs, OED financial mapping and source-matched event/period/sample keys, before Gross/Net OEP/AEP can be called runnable.
