<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-german-public-housing-insurance-20261105.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-german-public-housing-insurance-20261105.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-05`  
**Purpose:** Non-admission cross-insurer discovery of source products surfaced by R+V 2025 research: observed public-sector insurance account relationships, independent housing geography and parcels, insurance procurement discovery, and indirect cooperative-bank distribution prior.

**Entries:** 5

## Berlin Senate 2025 insurer relationships of six state-owned housing companies

**Candidate ID:** `de.berlin.senate.housing-insurer-relations.2025`  
**Provider:** Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin  
**Categories:** `insurance`, `corporate_account`, `public_housing`, `named_insurer`, `property`, `primary_government_evidence`  
**Spatial scope:** Berlin, Germany, six public housing companies; corporate account relationships only  
**Temporal scope:** Official reply dated 2025-04-01; 2026 coverage or renewal not established  
**Resolution / granularity:** Named corporate housing company and named building-insurance provider or consortium; source answers questions 2-4 on contracts and general perils  
**Potential roles:** `carrier_to_corporate_account_evidence`, `insurer_named_client_discovery`, `public_housing_property_book_prior`, `cross_insurer_negative_control`  
**Access hint:** `official_parliamentary_pdf_public_fact_research_only_rights_and_original_hash_review_pending`  
**Authoritative source:** <https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-22033.pdf>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original Berlin Senate answer 19/22033 names R+V Allgemeine for GESOBAU and WBM, R+V together with Allianz in degewo consortium, ERGO/Generali for Gewobag, Provinzial for HOWOGE and Allianz for STADT UND LAND. Master/blanket corporate building insurance is not one individual home-building policy per dwelling. No geocoded insured property list, carrier share of the degewo consortium, insured TIV, insurer CAT loss, claims or 2026 renewal. Existing typed research observation: research/observations/rva_berlin_senate_housing_insurer_relations_2025_v0.toml. Parliamentary PDF original-byte checksum not pinned. Do not infer 2025 physical location risk or treaty terms.

## Berlin Senate 2025 borough by public housing company dwelling inventory

**Candidate ID:** `de.berlin.senate.housing-borough-inventory.2025`  
**Provider:** Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin  
**Categories:** `residential_property`, `housing`, `borough`, `geography`, `corporate_account`, `exposure_opportunity`  
**Spatial scope:** Berlin's twelve boroughs, seven state-owned housing companies; separate additional other-stock row  
**Temporal scope:** Official reply 2025-11-11, main six companies as of 2025-06-30, Berlinovo as of 2025-09-30  
**Resolution / granularity:** Twelve boroughs by seven public housing operators, unit is dwellings, including documented non-borough or other stock  
**Potential roles:** `named_corporate_account_spatial_opportunity`, `public_housing_borough_inventory`, `insurer_client_geography_challenge`, `physical_stock_validation_prior`  
**Access hint:** `official_parliamentary_pdf_bounded_numeric_research_rights_and_original_hash_review_pending`  
**Authoritative source:** <https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-24229.pdf>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original Berlin Senate reply 19/24229 reports 376278 dwellings for the six principal operators plus 18666 Berlinovo dwellings on different reference dates. The linked typed research/observations/rva_berlin_senate_housing_borough_stock_2025_v0.toml records the original table's 12 borough rows. This is corporate dwelling stock, not physical insured building units or risk addresses. A separate earlier Senate reply identifies some insurers but does not establish that all corporate dwellings are covered or the identity of insured premises, TIV or coinsurance fraction. Never add these dwellings to an insurer's count of individual building policies.

## Berlin Open Data state-owned housing property parcels WFS

**Candidate ID:** `de.berlin.open-data.public-housing-property-wfs.2026`  
**Provider:** Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin  
**Categories:** `buildings`, `housing`, `gis`, `wfs`, `parcels`, `exposure_opportunity`  
**Spatial scope:** Berlin, Germany, land-owned housing company properties with at least four dwellings per reported address  
**Temporal scope:** Public dataset dated 2025-12-31, metadata updated 2026-04-07; dataset vintage must be independently pinned  
**Resolution / granularity:** Public cadastral parcel WFS geometry based on geocoded public housing stock; data layer schema and WFS original snapshot need explicit verification  
**Potential roles:** `public_housing_parcel_opportunity`, `building_footprint_geospatial_context`, `regional_residential_portfolio_spatial_validation`  
**Access hint:** `public_berlin_open_data_dl_de_zero_2_0_page_only_wfs_version_and_scientific_review_pending`  
**Authoritative source:** <https://daten.berlin.de/datensaetze/wohnungsbestand-der-landeseigenen-wohnungsunternehmen-wfs-4c4e0115>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher's catalog names Datenlizenz Deutschland Zero 2.0 and WFS resources for land-owned residential parcels with four or more dwellings per address. The separately reviewed published WFS codebook lists gisid and typ but no verified carrier or housing-company owner key. Thus this source does not establish which parcel belongs to R+V-insured WBM, GESOBAU or degewo; do not spatially join it to named insurer corporate accounts without an independent verified owner linkage. No WFS bytes or risk addresses admitted.

## TED European procurement notices for public-sector insurance contracts

**Candidate ID:** `eu.ted.insurance-public-procurement-notice-search`  
**Provider:** Publications Office of the European Union, Tenders Electronic Daily  
**Categories:** `insurance`, `procurement`, `corporate_account`, `public_sector`, `contract`, `international`  
**Spatial scope:** European public procurement notices, contracting-authority and performance-location scope vary by notice  
**Temporal scope:** Notice-specific publication and contract or award vintage; example 2023 and 2026 Berlin housing notices are not the same policy period  
**Resolution / granularity:** Individual notices by notice ID, authority, tender, contract type and potentially named awarded provider, lot and effective dates  
**Potential roles:** `named_insurer_corporate_account_discovery`, `municipal_property_insurance_award_evidence`, `carrier_contract_vintage_monitoring`, `public_procurement_research_prior`  
**Access hint:** `public_ted_search_interface_and_developer_resources_notice_specific_rights_and_content_review_pending`  
**Authoritative source:** <https://ted.europa.eu/en/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Reusable public insurance-contract discovery method; the R+V research identified Berlin WBM notice numbers 783307-2023 and 668506-2026, documented separately in research/observations/rva_distribution_bancassurance_public_awards_20261105_v0.toml. This generic catalogue entry DOES NOT independently verify awarded insurer share, all original notice fields, insured property schedule, current policy term or TIV. A notice or secondary award listing must not be transformed into geocoded insured risks. Verify exact official award and complete original record before carrier-specific assertion.

## BVR 2025 cooperative bank network and association regional statistics

**Candidate ID:** `de.bvr.cooperative-bank-network.2025`  
**Provider:** Bundesverband der Deutschen Volksbanken und Raiffeisenbanken (BVR)  
**Categories:** `insurance`, `banking`, `distribution`, `regional_statistics`, `financial_intermediaries`, `bancassurance`  
**Spatial scope:** Germany cooperative-bank reporting population and audit-association categories; not a unique 16-state insurer geography  
**Temporal scope:** Observed year-end 2024 and 2025 counts in the official BVR 2025 annual report  
**Resolution / granularity:** Bank institutions, branch offices and cooperative members by reporting association plus special Sparda/PSD/other national categories  
**Potential roles:** `bancassurance_channel_prior`, `insurance_distribution_network_context`, `branch_network_scenario_challenge`, `cooperative_bank_market_opportunity`  
**Access hint:** `public_bvr_html_aggregates_exact_html_bytes_not_pinned_reuse_terms_review_pending`  
**Authoritative source:** <https://berichte.bvr.de/jahresbericht-2025/ergebnisse/regionale-statistik/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official 2025 BVR panel gives 646 reporting banks, 6167 branch offices and 17542193 members, with 2024 comparison in research/observations/bvr_regional_association_counts_2024_2025_v0.toml. Audit associations are NOT the same as German Länder; counts of BVR institutions are not counts of R+V bank partners or R+V agencies. Bank branches and members cannot be treated as insurer policies, building locations, regional sales weights, insured TIV or evidence of the nearest building's insurance status.
