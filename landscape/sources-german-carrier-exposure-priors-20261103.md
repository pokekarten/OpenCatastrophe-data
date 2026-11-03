<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-german-carrier-exposure-priors-20261103.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-german-carrier-exposure-priors-20261103.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-03`  
**Purpose:** Non-admission discovery of German regulator carrier-count and German insurance-market district-level penetration/loss priors for probabilistically calibrated synthetic residential property portfolios; all data remain separately rights-scoped and unadmitted.

**Entries:** 3

## BaFin 2025 insurer complaint statistics with reported in-force risk-count denominators

**Candidate ID:** `de.bafin.insurer-complaint-statistics.2025`  
**Provider:** Bundesanstalt für Finanzdienstleistungsaufsicht (BaFin)  
**Categories:** `insurance`, `insurer_entity`, `policy_count_proxy`, `market_statistics`, `disclosure_bias`  
**Spatial scope:** Germany reporting insurers and lines in regulator complaint reporting population  
**Temporal scope:** 2025 complaint publication; in-force counts may refer to 2024 gross premiums and company coverage thresholds  
**Resolution / granularity:** XLSX published complaint counts and denominators by insurer and class where eligible; missing when threshold or data status not met  
**Potential roles:** `carrier_policy_stock_prior_research`, `nonlife_lob_entity_crosscheck`, `company_coverage_completeness_challenge`  
**Access hint:** `public_regulator_xlsx_terms_and_denominator_year_audit_pending`  
**Authoritative source:** <https://bafin.de/DE/die-bafin/publikationen-daten/statistiken/beschwerdestatistik/2025/2025.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Selection-biased: insurers with no complaints absent; in-force risk counts omitted below 10 million EUR threshold on 2024 earned gross class premiums and for EEA undertakings not required to submit; numbers can represent insured persons in group insurance and are not unique policies or buildings. Not fit as a nationwide carrier census or TIV without additional evidence.

## GDV 2026 Naturgefahrenreport county/district residential catastrophe loss frequency and severity

**Candidate ID:** `de.gdv.natcat-district-loss-frequency.2026`  
**Provider:** Gesamtverband der Deutschen Versicherungswirtschaft (GDV)  
**Categories:** `insurance`, `market_losses`, `residential_property`, `storm_hail`, `flood`, `county`, `claims`  
**Spatial scope:** Approximately 400 German districts/cities; insurer industry aggregate only  
**Temporal scope:** Report 2026, historic household/building catastrophe experience including 2002-2024 period and selected 2025 updates  
**Resolution / granularity:** District-level aggregate insured building event loss frequency, average claim and largest cumul event, split wind/hail and flood/heavy rain/earth movement/snow as available  
**Potential roles:** `district_property_natcat_loss_prior`, `industry_peril_region_challenge`, `historical_event_market_frequency_benchmark`  
**Access hint:** `public_web_report_graphs_tables_original_csv_availability_and_reuse_rights_pending`  
**Authoritative source:** <https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport/sachversicherung-naturgefahren/naturgefahren-koennen-jeden-treffen--157404>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Historical normalized district losses are industry-wide and represent insured coverage, not building-level hazard intensities or a specific insurer's actual losses. Preserve insured contract denominator, event as-of, inflation normalization, vintage and peril class; do not distribute reported industry claims into Allianz insured addresses.

## GDV 2026 county-level residential elemental-peril insurance take-up

**Candidate ID:** `de.gdv.natcat-elemental-penetration-district.2026`  
**Provider:** Gesamtverband der Deutschen Versicherungswirtschaft (GDV)  
**Categories:** `insurance`, `insured_penetration`, `residential_property`, `flood`, `district`, `market_statistics`  
**Spatial scope:** Germany approximately 400 counties and independent cities; aggregate insurance-market coverage  
**Temporal scope:** 2020-2025 county take-up series, updated in 2026  
**Resolution / granularity:** Percent of residential buildings with full elemental-peril cover by district; excludes certain stand-alone heavy-rain contracts  
**Potential roles:** `flood_covered_asset_probability_prior`, `regional_insurance_penetration_calibration`, `residential_claim_exposure_denominator_challenge`  
**Access hint:** `public_interactive_map_report_raw_grid_export_and_commercial_rights_review_pending`  
**Authoritative source:** <https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport/sachversicherung-elementar/versicherungsdichte-bei-elementarschadenversicherung-regional-sehr-unterschiedlich-183592>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** A landkreis-level market share of insured buildings is NOT the company-specific percentage or a unique set of coverage addresses; some historical policies included; coverage here means full elemental-peril insurance, not all general homeowners protection. Machine-download rights and spatial/vintage consistency must be reviewed. Keep county IDs, numerator/denominator definitions and publisher revision.
