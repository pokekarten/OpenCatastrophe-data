<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-nfip-penetration-2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-nfip-penetration-2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission discovery registry for FEMA NFIP county-level aggregate insurance-penetration benchmarks.

**Entries:** 1

## OpenFEMA NFIP Residential Penetration Rates v1

**Candidate ID:** `fema.openfema.nfip-residential-penetration-rates.v1`  
**Provider:** Federal Emergency Management Agency (FEMA) / National Flood Insurance Program  
**Categories:** `insurance`, `flood`, `coverage_gap`, `county`, `penetration_rate`, `exposure_benchmark`  
**Spatial scope:** United States; aggregate regional programme statistics (county/community coverage subject to original fields)  
**Temporal scope:** Official OpenFEMA catalogue lastDataSetRefresh 2026-08-04; published product snapshot, not a historical insurer-level series  
**Resolution / granularity:** Official OpenFEMA v1 API dataset; 3159 provider-reported rows at 2026-10-31 catalogue snapshot; NFIP residential penetration derived against NSI 2022 structure stock  
**Potential roles:** `nfip_county_coverage_benchmark`, `regional_flood_insurance_protection_gap`, `independent_national_programme_sanity_check`, `aggregate_nsi_crosscheck`  
**Access hint:** `public_read_only_openfema_api_terms_and_exact_field_review_pending`  
**Authoritative source:** <https://www.fema.gov/api/open/v1/NfipResidentialPenetrationRates>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original official OpenFEMA catalogue records version 1, 3159 rows, no deprecation, and lastDataSetRefresh 2026-08-04. FEMA warns that the denominator draws on older NSI 2022 estimated structure stock, which can be incomplete; some calculated penetration rates exceed 100%. The metric excludes private flood insurance and is not an actual building, policyholder, claim, insurer portfolio or property-level exposure. API rights, exact fields, source bytes, version and regional coverage need separate review before any use. Do not treat as an independent check against NSI 2022 without recording shared lineage.
