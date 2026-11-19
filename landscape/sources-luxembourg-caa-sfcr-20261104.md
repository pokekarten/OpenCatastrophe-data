<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-luxembourg-caa-sfcr-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-luxembourg-caa-sfcr-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission discovery of Luxembourg regulator SFCR report directories for life and non-life insurers, with legal entity and solo solvency ratio context complementary to Irish public QRT data; no automated acquisition or model use authorised.

**Entries:** 2

## Luxembourg CAA public non-life SFCR directory and solo solvency ratios

**Candidate ID:** `lu.caa.sfcr.nonlife.directory`  
**Provider:** Commissariat aux Assurances (CAA), Luxembourg  
**Categories:** `insurance`, `solvency`, `regulatory_disclosure`, `legal_entity`, `sfcr`, `nonlife`, `reinsurance`  
**Spatial scope:** Luxembourg-authorised regulated undertaking population; domicile is not the location of underlying insured risks  
**Temporal scope:** Live regulator listing observed 2026-11-04, solvency ratio is latest solo annual ratio communicated; actual report year varies by company  
**Resolution / granularity:** Undertaking name, LEI in parentheses, latest public solo Solvency II ratio, company-specific PDF or SFCR page link where offered  
**Potential roles:** `luxembourg_carrier_lei_resolution`, `published_solo_solvency_ratio_prior`, `insurer_public_sfcr_discovery`, `legal_entity_reinsurance_context`  
**Access hint:** `official_public_html_directory_and_company_pdf_links_no_bulk_csv_confirmed_exact_vintage_and_terms_review_pending`  
**Authoritative source:** <https://www.caa.lu/en/information/solvency-and-financial-condition-reports-sfcr-of-non-life-insurance-undertakings>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The CAA provider page says its visible population covers direct professional non-life undertakings, explicitly excluding captives and undertakings with a comparable portfolio. Named rows include LEI and latest communicated solo solvency ratio; the ratio is not a published catastrophe AEL/PML, insured TIV or investment/business perimeter, and ratio vintage may differ by carrier. Do not claim this list covers all Luxembourg licensed insurers/reinsurers or all groups. Links may be PDF or company pages; record exact report date, source licence and document rights before acquisition. This is distinct from an EIOPA aggregate or national legal entity register.

## Luxembourg CAA public life SFCR directory and solo solvency ratios

**Candidate ID:** `lu.caa.sfcr.life.directory`  
**Provider:** Commissariat aux Assurances (CAA), Luxembourg  
**Categories:** `insurance`, `solvency`, `regulatory_disclosure`, `legal_entity`, `sfcr`, `life`  
**Spatial scope:** Luxembourg-authorised regulated undertaking population; domicile is not the location of underlying insured risks  
**Temporal scope:** Live regulator listing observed 2026-11-04, solvency ratio is latest solo annual ratio communicated; actual report year varies by company  
**Resolution / granularity:** Undertaking name, LEI in parentheses, latest public solo Solvency II ratio, company-specific PDF or SFCR page link where offered  
**Potential roles:** `luxembourg_life_carrier_lei_resolution`, `published_solo_solvency_ratio_prior`, `life_company_reporting_perimeter`, `public_qrt_document_discovery`  
**Access hint:** `official_public_html_directory_and_company_pdf_links_no_bulk_csv_confirmed_exact_vintage_and_terms_review_pending`  
**Authoritative source:** <https://www.caa.lu/en/information/solvency-and-financial-condition-reports-sfcr-of-life-insurance-undertakings>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The official CAA life directory exposes named undertakings and LEIs with latest solo solvency ratios and report links where available. Some companies provide only website links or a contact address rather than a PDF. Do not infer general/non-life insurance or catastrophe property exposures from life company financial ratios; membership and reports have changing dates and potential non-contemporaneous ratios. Raw PDFs, terms, entity/group relationships and reporting vintages require separate verification, and the directory is not a complete actuarial dataset.
