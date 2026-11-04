<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NRW official rooftop PV opportunity: 2026-03-12 original XLSX proof for R+V-like exposure scenarios

**2026-11-04 | source preflight only | model admission DENIED.**

## Exact original publisher data asset

- State provider official product: [OpenGeodata NRW, Photovoltaik-Dachflächen](https://www.opengeodata.nrw.de/produkte/umwelt_klima/energie/solarkataster/photovoltaik/).
- Specifically listed original file: [Dach-PV-nach-Gebaeudekategorien-Gemeindeebene_Excel.xlsx](https://www.opengeodata.nrw.de/produkte/umwelt_klima/energie/solarkataster/photovoltaik/Dach-PV-nach-Gebaeudekategorien-Gemeindeebene_Excel.xlsx); publisher listing date **2026-03-12 13:24:12** and size **1.4 MB**.
- Publisher page explicitly advertises **Datenlizenz Deutschland – Zero – Version 2.0**; record exact licence and original file edition in any later admitted ingestion. Listed GeoDatabases and municipality Shape ZIPs are **different** products, typically tens/hundreds of MB; not downloaded here.
- The original observable dimensions are **municipality × building-category technical rooftop PV *potential***, NOT installed PV, investment/replacement cost, policyholder count, insurance take-up or R+V-specific rooftop additions.

## Reproducible byte- and shape-only canary

- `research_runners/rva_nrw_original_rooftop_pv_xlsx_v0.py`: HTTPS **only** to the exact publisher-listed asset, ephemeral download with hard **8 MiB size** gate; recompute **full-source SHA-256**; reject unsafe member names, macro content, external links, ZIP excess size, OOXML formulas; inspect workbook/worksheet XML using Python stdlib; print only SHA, byte length, workbook sheet count, occupied XML row count per sheet and max occupied columns, never raw cells, personal information or town names. Parsing XML does NOT execute spreadsheet formula macros. Failure blocks the original-data workflow.
- `.github/workflows/rva-nrw-official-roof-pv-original-xlsx.yml`: source-specific read-only official HTTPS workflow (PR-only paths and manual trigger), no DB credentials, no upload of raw workbook or parsed municipality rows. The source is fetched at workflow runtime, **not committed to GitHub**.
- `tests/test_rva_nrw_original_rooftop_pv_xlsx_v0.py`: bounded synthetic XSLX/OOXML tests, containing no genuine source data, negative tests for fake file, macro, external links, formulas, insufficient columns, traversal, failed source size and no R+V claims.

The first official run is deliberately **un-pinned** to observe the live publisher SHA-256 and actual OOXML structure without inventing a byte hash. After the verified original run, update a follow-up exact source SHA/size pin and repeat the original canary; until then `original_sha_pinned_in_source_code=false` and `actual_model_input_admitted=false` regardless of workflow success. The workbook can be published anew at the same URL, so pinned original SHA is more reliable than relying on the 2026-03-12 publisher listing date. **SHA protects byte identity, not the scientific truth of statistical cells.**

## R+V inference safeguards

For synthetic German building exposure from **R+V Allgemeine solo**:
- Compare candidate NRW municipal roof-PV *potential* to **independent actual registered PV counts** from Bundesnetzagentur MaStR, preferably privacy-safe *county aggregation* after licence/snapshot/vintage validation. Potential per building is NOT actual installed plant, and MaStR unit record is not a demonstrated building roof or insured policy.
- Compare with dated building-type mix from **Zensus 2022** and open state LoD2 geometry (NRW) only after those *separate* source assets are attested. Beware shared upstream LoD2/rooftop-surface lineage; these are not independent ground-truth assets.
- Store candidate attributes in an **hypothesis** with negative flags for real R+V insured address, property value, PV policy endorsement, insurance terms, hazard, GUL/IL/RI and OEP/AEP. In particular, R+V 2025 **1,060,546 connected-buildings contracts** does not mean 1,060,546 actual insured distinct physical buildings, and the roof-potential table does not assign these policies to municipalities.
- For hail/wind PV vulnerability, distinguish roof inclination/area and hypothetical panel installation/mounting standard, property vs auxiliary PV coverage, commercial vs residential, and CAT policy coverage before computing replacement cost.

## Next scientific admission gates

1. Original full file SHA and bounded actual sheet structure at GitHub Actions **at exact PR HEAD**.
2. Check original manufacturer schema, column meaning, suppressed/zero values and category codebook from the exact Excel data **without public individual-location export**.
3. Define fixed territorial coding (AGS/gemeindecodes + administrative boundary year), apply data vintage crosswalk for R+V 2025.
4. Compare roof *potential* vs actual MaStR installed stock with **mismatched universe** and negative tests; do not estimate R+V insurance share without further evidence.
5. Keep official per-object/licence notes and model source status distinct: SOURCE_DISCOVERED → ORIGINAL_BYTES_VERIFIED → RIGHTS_REVIEWED → SCIENTIFICALLY_VALIDATED → APPROVED_FOR_SCENARIO_INPUT.

This PR is a research-source operational preflight. No insurer sites, risk-level TIV or real PV attachment rate is admitted.
