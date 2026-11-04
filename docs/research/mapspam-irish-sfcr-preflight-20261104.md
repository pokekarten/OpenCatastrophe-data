<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source-specific preflight: IFPRI MapSPAM 2020 v2r2 and Irish SFCR 2025 (2026-11-04)

**Scope:** Research and non-admission source identity, rights contradiction, structural preflight and possible future OpenCatastrophe/NextGen consumer roles. No external original data files were acquired or committed, no private database was modified, no source was admitted or used as a CAT model input.

## 1. IFPRI MapSPAM 2020: source family versus cloud representation

- Original publisher product: IFPRI *Global Spatially-Disaggregated Crop Production Statistics Data for 2020 Version 2.0 Release 2*, DOI [10.7910/DVN/SWPENT](https://doi.org/10.7910/DVN/SWPENT). Publisher data center: https://www.mapspam.info/data/ . The currently described release is **v2r2** / SPAM 2020 v2.2, updated 2026-05-05. This product is a **2020 agricultural reference-year estimate**, not a new measurement in 2026.
- Independent documented distribution: [CGIAR Climate Action Data Hub](https://cgiar-climate-data-hub.github.io/catalog/spam2020/) provides a derived Zarr data cube (approximately 287 MB advertised) and 12 COGs (four variables × three technology groups), including:
  - Zarr: https://digital-atlas.s3.amazonaws.com/cdh/data/mapspam2020-v2r2/spam2020-v2r2.zarr
  - Single COG example: https://digital-atlas.s3.amazonaws.com/cdh/data/mapspam2020-v2r2/cog/spam2020-physical_area-all.tif
  - Crop codes: https://digital-atlas.s3.amazonaws.com/cdh/data/mapspam2020-v2r2/crop-codes.json
- The CGIAR representation is a **transformation/distribution of IFPRI's original**, NOT independent observational validation. Pin the exact original Harvard Dataverse file UUID/version and each transformed artifact's lineage before claiming provenance; DOI alone can resolve to a newer Dataverse release.
- Scientific unit contract (per official CGIAR data dictionary):

  | Variable | Unit | Correct aggregation |
  | --- | --- | --- |
  | \`physical_area\` | hectares | Sum compatible nonoverlapping cells and categories with technology/crop treatment declared |
  | \`harvested_area\` | hectares | Sum compatible cells; multi-cropping can make harvested area exceed physical area |
  | \`production\` | tonnes | Sum cells after declared crop/technology slicing |
  | \`yield\` | kilograms/hectare | **Never sum**; regional estimate needs harvested-area-weighted mean with proper zero/missing handling |

- The underlying grid is 5 arc-minutes (~9.3 km near the equator), much coarser than fields/farms; downscaling to individual insured addresses would be a *synthetic allocation*, not an observed crop location. The crop list includes aggregate families and individual crops; additive summation must screen parent/subcategory duplication.
- **Blocking rights ambiguity:** official IFPRI [terms](https://www.mapspam.info/terms/) state CC BY-NC 3.0 for website datasets/documents, while CGIAR's [MAPSPAM v2r2 page](https://cgiar-climate-data-hub.github.io/catalog/spam2020/) labels the derivative **CC BY-SA 4.0**. This is not proof that the original 2020 v2r2 was relicensed for commercial use. The original Harvard Dataverse exact file and licensing terms, transformation authority and COG/Zarr derivative rights must be explicitly checked; until resolved, do **not** promote for commercial CAT or NextGen model use or publish transformed bytes in Git.
- Next falsifiable checks: original Dataverse API metadata and version/file identity; CGIAR object metadata (no-sign HEAD for a single pinned COG and Zarr .zmetadata if present); approved-size bounded range/COG header probe; pixel units/nodata/crop ordering, 2020 reference vintage, no-parent-double-count synthetic invariant. No provider-byte probe was executed here.

## 2. Irish Central Bank SFCR 2025: executable structural gate

- Official regulator [SFCR repository](https://www.centralbank.ie/regulation/industry-market-sectors/insurance-reinsurance/solvency-and-financial-condition-report-repository) and 2025 CSV indexed at [first-party file URL](https://edit.centralbank.ie/docs/default-source/regulation/industry-market-sectors/insurance-reinsurance/solvency-ii/solvency-and-financial-condition-report-repository/data-repository-sfcr-template-information-2025.csv?sfvrsn=1ced741a_1). Exa's original-page intermediary returned CSV header and rows; **no full original 2025 CSV was directly fetched or hashed**. Indexed header is 18 fields, including \`ReportingDate\`, \`InstitutionName\`, \`InstitutionNumber\`, \`LEICode\`, \`InstitutionType\`, \`year_end\`, \`templates\`, QRT row/column codes, and euro/local value fields.
- The official site advertises a ~12,132 KB CSV for year 2025; because a separate web-page cache returned only 2024 and prior versions, exact original source/last-updated header and current version must be preserved on a trusted direct fetch. The centralbank.ie 2025 CSV is not automatically the same as the separately versioned [Irish Open Data portal dataset](https://opendata.centralbank.ie/dataset/data-repository-sfcr-template-information), whose published portal resources include 2022–2024 and CC BY 4.0 metadata. A 2024 portal licence does **not** grant 2025 raw-asset rights.
- Evidence of header and year semantics from the publisher-page intermediary: a 2025 row reports date \`30/06/2025\`, institution number \`33489\`, legal identifier column \`LEICode\`, template \`S.02.01.02\`, row \`R0420\`, and column \`C0010\`. This is **only a provider representation**, not a complete audited source snapshot. In particular, 2025 reporting is not automatically all 31 December 2025.
- Added local-only, no-network structural preflight: \`research_runners/cbi_sfcr_2025_preflight_v0.py\`. The script accepts a *separately and lawfully acquired* local original CSV, outside the repository tree, then checks exact 2025 schema, 2025 report dates, undertaking IDs, LEI format (not checksum), QRT codes, finite financial values, row/size ceilings, and provides an SHA-256 of the submitted original bytes. It emits **only aggregate counts** by template and status flags; no company-level records, sums or inferred insured exposures.
- Reproduction after separately obtaining a permitted original 2025 asset:

  \`\`\`bash
  python -m unittest tests.test_cbi_sfcr_2025_preflight_v0
  python research_runners/cbi_sfcr_2025_preflight_v0.py --csv /secure/original-sfcr-2025.csv
  \`\`\`

- Structural checks do NOT establish upstream authenticity, 2025 reporting completeness, licence, QRT taxonomy consistency, company ownership, geography of insured risks or actuarial usability. Source \`InstitutionNumber\` is an identifier to reconcile with legal-entity registers/LEI and solo/group perimeter; it is not an insurer-wide portfolio identifier. \`S.05\` line-by-line earned/written/gross/net figures cannot be summed blindly; \`S.04\` country of business is not necessarily property risk situs, and S.02 assets/reserves are not TIV.
- Next rights and scientific gate: freeze original CSV response SHA, disposition/version/time, determine file-specific reuse terms, check euro amount/thousand-unit ratio by QRT cell (percentages excluded), validate census of entity/reporting-date populations, group/solo overlaps, full QRT taxonomy and missing/duplicated identifiers; then only derive aggregated, clearly uncertain line-of-business priors, with no real insured locations.

## 3. Consumer decision

- **MapSPAM:** potential global agricultural *exposure prior* for synthetic portfolio generation after original-asset rights and pixel/unit calibration; no independent event hazard or claims.
- **Irish SFCR:** potential legal entity / line-of-business capital and premium constraints for synthetic insurer portfolio inference after reporting scope and source-byte gates; neither a building register nor an insurer property-level CAT exposure.
- **NextGen use:** both would require a named consumer plus admitted source manifest, exact artifact/derivation hashes, allowed scientific roles and explicit synthetic allocations. Current status: **research-only, not admitted, no model-ready assertion**.
