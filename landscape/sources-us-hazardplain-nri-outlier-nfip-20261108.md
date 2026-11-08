<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-us-hazardplain-nri-outlier-nfip-20261108.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-us-hazardplain-nri-outlier-nfip-20261108.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-08`  
**Purpose:** Non-admission source discovery of three distinct national county-level Hazard Plain 2026-10 bulk tables useful for US hazard and insured-flood research. Exact table sizes and SHA-256 are claims in the publisher's bulk manifest, NOT hashes independently recomputed on external data bytes. No source file, model input, commercial-use approval or independent validation is admitted.

**Entries:** 3

## Hazard Plain 2026-10 national county-by-hazard NRI risk and exposure baseline

**Candidate ID:** `us.hazardplain.nri-county-hazard.2026-10`  
**Provider:** Hazard Plain (independent public-data derivative of FEMA NRI v1.20 and NOAA Storm Events)  
**Categories:** `united_states`, `natural_hazards`, `expected_annual_loss`, `exposure`, `county`, `multi_peril`, `secondary_source`  
**Spatial scope:** United States 3232 county areas and equivalents; one candidate row per county and 18 risk categories, not physical insurance locations  
**Temporal scope:** Hazard Plain release 2026-10, data as of 2026-09-30; underlying FEMA NRI v1.20 December 2025 and NOAA Storm Events through 2026-06-30; built 2026-10-17  
**Resolution / granularity:** National CSV `nri_county_hazard.csv`: publisher manifest lists 58176 rows, 23764594 bytes, SHA-256 262d0dbc42dfc123408f28d3723bde49c6249c8f734adb2fafb720bb4f770eae. County FIPS × 18 hazards, modeled NRI total/building/agriculture/people expected annual loss, exposure, frequency descriptors and Storm Events summaries  
**Potential roles:** `county_hazard_exposure_prior`, `synthetic_portfolio_peril_mix_challenge`, `nri_version_and_census_join`, `source_lineage_and_overlap_audit`  
**Access hint:** `public_2026_10_csv_parquet_manifest_and_ccby_4_claim_exact_file_and_upstream_openfema_terms_review_required`  
**Authoritative source:** <https://hazardplain.org/downloads/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher bulk manifest is https://files.hazardplain.org/r/2026-10/bulk/manifest.json; publisher CSV is https://files.hazardplain.org/r/2026-10/bulk/national/nri_county_hazard.csv. Original CSV byte identity independently verified in GitHub Actions run 42529431183 on 2026-11-08: exactly 23,764,594 bytes, SHA-256 262d0dbc42dfc123408f28d3723bde49c6249c8f734adb2fafb720bb4f770eae, 58,176 parsed records and original header names matching the pinned manifest. See docs/research/hazardplain-202610-original-csv-exact-byte-receipt-20261108.md; this is research-only verification, NOT rights/scientific admission. Hazard Plain claims CC BY 4.0 attribution for its outputs; exact table rights and underlying federal source/API conditions require project rights review. The 'independent product' label means independent publisher, NOT statistically independent information: the NRI AAL/building values are derived from FEMA NRI, and NOAA observations are shared. Do not calibrate to NRI and then claim this table an independent holdout. County EAL is modeled economic expectation, not a carrier's covered TIV, claim severity, or event-loss data.

## Hazard Plain 2026-10 county-peril expected-annual-loss anomaly and caveat tests

**Candidate ID:** `us.hazardplain.eal-outliers.2026-10`  
**Provider:** Hazard Plain (derived FEMA NRI/NOAA/Census-adjacency diagnostics)  
**Categories:** `united_states`, `county`, `multi_peril`, `expected_annual_loss`, `quality_control`, `outliers`, `source_diagnostics`  
**Spatial scope:** United States; county and hazard candidates with sufficient inputs for the publisher's expected annual loss anomaly screen  
**Temporal scope:** Release 2026-10, source snapshot through 2026-09-30, NOAA Storm Events through 2026-06-30; constructed 2026-10-17  
**Resolution / granularity:** National CSV `eal_outliers.csv`, manifest reports 45853 rows, 10265835 bytes and SHA-256 47c50202b0c6b57fd0c75624e51d3b7b87bb11ae2951ac7b4f5e299882525815; county × peril, modeled NRI EAL and exposed value, geographic neighbor-median comparisons, NOAA observation check and diagnostic flags  
**Potential roles:** `county_eal_outlier_challenge`, `spatial_prior_sensitivity`, `risk_measure_outlier_audit`, `modelled_vs_observed_lineage_tracking`  
**Access hint:** `public_2026_10_csv_parquet_publisher_checksums_authoritative_manifest_provenance_and_terms_review_required`  
**Authoritative source:** <https://hazardplain.org/downloads/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher manifest https://files.hazardplain.org/r/2026-10/bulk/manifest.json lists file `national/eal_outliers.csv`; Original provider CSV was independently downloaded and verified in GitHub Actions run 42529431183 on 2026-11-08: exactly 10,265,835 bytes, SHA-256 47c50202b0c6b57fd0c75624e51d3b7b87bb11ae2951ac7b4f5e299882525815, 45,853 parsed records and header columns matching the pinned manifest. See docs/research/hazardplain-202610-original-csv-exact-byte-receipt-20261108.md; still not admitted for modeling. This is a SECONDARY diagnostic of FEMA NRI and NOAA Storm Events, not an independent validation or observed insurer-loss source. Neighbor-median anomalies need county adjacency 2024 vintage, hazard applicability and missing/storm-event-record caveats; an outlier flag must not be treated as a calibrated loss adjustment. Dataset-specific release attribution and source rights must be checked before commercial model input.

## Hazard Plain 2026-10 aggregate NFIP repetitive-loss property classes by county

**Candidate ID:** `us.hazardplain.nfip-repetitive-county.2026-10`  
**Provider:** Hazard Plain (derived from OpenFEMA NfipMultipleLossProperties v1)  
**Categories:** `united_states`, `flood`, `repeat_flood`, `insurance`, `county`, `aggregates`, `vulnerability_context`  
**Spatial scope:** United States 3232 county areas, but NFIP reporting, eligibility and community-to-county assignment differ from the physical building stock  
**Temporal scope:** Hazard Plain release 2026-10, data as of 2026-09-30, underlying OpenFEMA NfipMultipleLossProperties v1 refreshed 2026-08-04  
**Resolution / granularity:** National CSV `b2c_county.csv`: publisher manifest reports 3232 rows, 352674 bytes, SHA-256 4d891f4fce8b0f5ae1c4d6119be74b217e302e5cd8f17e3a6b8e43c2c0c7ffc5; counts by NFIP repetitive-loss class and occupancy group, not addresses or individual policies  
**Potential roles:** `county_repetitive_flood_context`, `insured_flood_sampling_bias_challenge`, `occupancy_loss_repetition_prior`, `community_to_county_crosswalk_review`  
**Access hint:** `public_2026_10_aggregate_csv_manifest_sha256_claim_source_openfema_terms_and_suppression_review_required`  
**Authoritative source:** <https://hazardplain.org/downloads/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher manifest https://files.hazardplain.org/r/2026-10/bulk/manifest.json describes `national/b2c_county.csv` and these size/hash/count values, now independently verified from original CSV bytes in GitHub Actions run 42529431183 on 2026-11-08 (352,674 bytes, SHA-256 4d891f4fce8b0f5ae1c4d6119be74b217e302e5cd8f17e3a6b8e43c2c0c7ffc5, 3,232 parsed records and exact original column names). See docs/research/hazardplain-202610-original-csv-exact-byte-receipt-20261108.md. Hazard Plain states its tables CC BY 4.0; OpenFEMA upstream and aggregation/suppression conditions have not passed source-specific rights/science review. Aggregate NFIP repeated loss properties are not market-wide insured risks, annual claim frequencies, event losses, replacement values, or individual buildings. Distinguish all repetitive-loss classes/occupancies, community-to-county assignment, counting units, selection bias and possible suppression from actual vulnerability calibration; original source bytes acquired temporarily in bounded memory only, no row values emitted or retained.
