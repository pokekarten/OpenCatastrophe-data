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
