<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-global-insurer-registers-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-global-insurer-registers-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission discovery of official insurance regulatory registers to expand worldwide insurance and reinsurance group, legal-entity and jurisdiction coverage without importing third-party raw records.

**Entries:** 13

## IAIS register of Internationally Active Insurance Groups

**Candidate ID:** `iais.iaig-register.20261014`  
**Provider:** International Association of Insurance Supervisors (IAIS)  
**Categories:** `insurance`, `insurer_group`, `regulation`, `global`  
**Spatial scope:** Global; 61 internationally active insurance groups as at 14 October 2026, 19 group-wide supervisor jurisdictions  
**Temporal scope:** Snapshot dated 2026-10-14, subject to updates  
**Resolution / granularity:** Group name; group-wide supervisor; supervisor jurisdiction  
**Potential roles:** `international_group_seed`, `group_supervisor_crosswalk`, `legal_parent_review_queue`  
**Access hint:** `public_provider_registry_discovery_rights_and_machine_access_review_pending`  
**Authoritative source:** <https://www.iais.org/register-of-iaigs/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Group subset, not all insurers; group name is not necessarily legal parent or LEI. Preserve supervisor jurisdiction and group vs entity grain.

## SUSEP supervised-company OData cadastral records

**Candidate ID:** `br.susep.dadoscadastrais.odata`  
**Provider:** Superintendência de Seguros Privados (SUSEP)  
**Categories:** `insurance`, `reinsurance`, `insurer_entity_registry`, `regulation`  
**Spatial scope:** Brazil: supervised insurance/reinsurance and pension institutions  
**Temporal scope:** Live source, freeze acquisition date before use  
**Resolution / granularity:** OData company names, SUSEP code, Brazilian CNPJ, authorisation dates and contacts  
**Potential roles:** `insurer_legal_entity_discovery`, `national_regulator_crosscheck`, `group_subsidiary_crosswalk`  
**Access hint:** `public_provider_registry_discovery_rights_and_machine_access_review_pending`  
**Authoritative source:** <https://dados.susep.gov.br/olinda/servico/empresas/versao/v1/odata/DadosCadastrais>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** SUSEP official API was discovered but direct retrieval timed out in this pass; active-license semantics and pagination not checked. CNPJ is not an LEI; pension entities need classification.

## CIMA reinsurance companies and offices directory

**Candidate ID:** `cima.reinsurance-establishments`  
**Provider:** Conférence Interafricaine des Marchés d'Assurances (CIMA)  
**Categories:** `insurance`, `reinsurance`, `regulation`, `establishment_directory`  
**Spatial scope:** Central and West Africa CIMA member markets  
**Temporal scope:** Live web directory; no pinned snapshot  
**Resolution / granularity:** Name, territory, headquarters/subsidiary/branch/representative-office type, contact  
**Potential roles:** `insurer_legal_entity_discovery`, `national_regulator_crosscheck`, `group_subsidiary_crosswalk`  
**Access hint:** `public_provider_registry_discovery_rights_and_machine_access_review_pending`  
**Authoritative source:** <https://cima-afrique.org/les-etats-membres/?item=REASS&lang=en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Mixed establishment types are not unique carrier legal entities. Regional and representative offices must not be counted as separate insurers; licensing and corporate parents require separate evidence.

## South African Prudential Authority insurers list

**Candidate ID:** `za.sarb.insurer-register`  
**Provider:** South African Reserve Bank Prudential Authority  
**Categories:** `insurance`, `reinsurance`, `insurer_entity_registry`, `regulation`  
**Spatial scope:** South Africa  
**Temporal scope:** Current web register; freeze snapshot on import  
**Resolution / granularity:** Insurer name, class, type and insurer number  
**Potential roles:** `insurer_legal_entity_discovery`, `national_regulator_crosscheck`, `group_subsidiary_crosswalk`  
**Access hint:** `public_provider_registry_discovery_rights_and_machine_access_review_pending`  
**Authoritative source:** <https://www.resbank.co.za/en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Check insurer number, class and type; distinguish primary insurer, reinsurer, subsidiary and group. No property CAT exposure or TIV in this register. The official current Insurers List can be found through the regulator portal's Prudential Regulation navigation. The portal URL is used in this metadata because the full page link triggers the repository's home-path hygiene detector; direct page identity must be pinned in any later acquisition receipt.

## OSFI Who We Regulate institution open data

**Candidate ID:** `ca.osfi.federally-regulated-institutions.csv`  
**Provider:** Office of the Superintendent of Financial Institutions Canada (OSFI)  
**Categories:** `insurance`, `reinsurance`, `insurer_entity_registry`, `regulation`  
**Spatial scope:** Canada federally regulated financial institutions; province-only insurers outside coverage  
**Temporal scope:** Official government CSV metadata updated October 2026  
**Resolution / granularity:** CSV identity register; insurer classification; companion life and P&amp;C financial CSV datasets  
**Potential roles:** `insurer_legal_entity_discovery`, `national_regulator_crosscheck`, `group_subsidiary_crosswalk`  
**Access hint:** `public_provider_registry_discovery_rights_and_machine_access_review_pending`  
**Authoritative source:** <https://open.canada.ca/data/en/dataset/b27ec3ef-7338-4e76-a6fd-128339a92df5>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Cross-sector list contains banks too, requiring insurer filter. Federal vs provincial and branch vs subsidiary must be distinguished. Browser read produced 403; direct CSV and rights need separate test.

## APRA registered general insurers

**Candidate ID:** `au.apra.general-insurers-register`  
**Provider:** Australian Prudential Regulation Authority (APRA)  
**Categories:** `insurance`, `reinsurance`, `insurer_entity_registry`, `regulation`  
**Spatial scope:** Australia  
**Temporal scope:** Register updated 2026-09-23  
**Resolution / granularity:** Authorised general insurer names, permission categories and licence conditions  
**Potential roles:** `insurer_legal_entity_discovery`, `national_regulator_crosscheck`, `group_subsidiary_crosswalk`  
**Access hint:** `public_provider_registry_discovery_rights_and_machine_access_review_pending`  
**Authoritative source:** <https://www.apra.gov.au/registers/list-registered-general-insurers>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Current vs former/limited authority must be separated. Life insurer register is distinct. Local and foreign companies may be members of the same ultimate group.

## Hong Kong Insurance Authority authorised insurer register

**Candidate ID:** `hk.ia.authorised-insurers`  
**Provider:** Insurance Authority (Hong Kong)  
**Categories:** `insurance`, `reinsurance`, `insurer_entity_registry`, `regulation`  
**Spatial scope:** Hong Kong  
**Temporal scope:** Register updated 2026-10-17  
**Resolution / granularity:** Names, authorisation and insurer business classes, jurisdiction of incorporation  
**Potential roles:** `insurer_legal_entity_discovery`, `national_regulator_crosscheck`, `group_subsidiary_crosswalk`  
**Access hint:** `public_provider_registry_discovery_rights_and_machine_access_review_pending`  
**Authoritative source:** <https://www.ia.org.hk/en/supervision/reg_insurers_lloyd/register_of_authorized_insurers.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Includes entities authorised at the last update that may have ceased writing business; do not infer current new-business permission. Operations in HK do not prove group domicile.

## Bermuda BMA regulated entities directory

**Candidate ID:** `bm.bma.regulated-entities`  
**Provider:** Bermuda Monetary Authority (BMA)  
**Categories:** `insurance`, `reinsurance`, `insurer_entity_registry`, `regulation`  
**Spatial scope:** Bermuda  
**Temporal scope:** Live web directory; freeze extraction timestamp  
**Resolution / granularity:** Company name, insurance sector and licence/registration class  
**Potential roles:** `insurer_legal_entity_discovery`, `national_regulator_crosscheck`, `group_subsidiary_crosswalk`  
**Access hint:** `public_provider_registry_discovery_rights_and_machine_access_review_pending`  
**Authoritative source:** <https://www.bma.bm/regulated-entities>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Mixed captive, SPI, reinsurer, agent and manager classes; potentially multiple entries per firm. Do not count every registered entity as an insurer parent group.

## New Zealand licensed insurers register

**Candidate ID:** `nz.rbnz.licensed-insurers`  
**Provider:** Reserve Bank of New Zealand (RBNZ)  
**Categories:** `insurance`, `reinsurance`, `insurer_entity_registry`, `regulation`  
**Spatial scope:** New Zealand  
**Temporal scope:** Register last updated 2026-08-26 per provider metadata  
**Resolution / granularity:** Legal insurer name, licence date, financial strength rating and exemptions  
**Potential roles:** `insurer_legal_entity_discovery`, `national_regulator_crosscheck`, `group_subsidiary_crosswalk`  
**Access hint:** `public_provider_registry_discovery_rights_and_machine_access_review_pending`  
**Authoritative source:** <https://www.rbnz.govt.nz/regulation-and-supervision/cross-sector-oversight/registers-of-entities-we-regulate/register-of-licensed-insurers>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Rating and its agency/date must remain distinct; missing or exempt ratings are not evidence of strength or weakness. Separate legal entity and ultimate group.

## NAIC Insurance Group Lead State Report (2026 Q2)

**Candidate ID:** `us.naic.insurance-group-lead-state.2026q2`  
**Provider:** National Association of Insurance Commissioners (NAIC)  
**Categories:** `insurance`, `insurer_group`, `regulation`, `group_code`, `united_states`  
**Spatial scope:** United States insurance groups assigned NAIC group codes and supervisory lead states  
**Temporal scope:** Published 2026 Quarter 2; freeze the quarter and capture date  
**Resolution / granularity:** Group-name / NAIC numeric group-code / lead-state register, including smaller US groups outside IAIS international group cohort  
**Potential roles:** `us_insurer_group_seed`, `naic_group_code_crosswalk`, `lead_state_supervisor_join`  
**Access hint:** `public_naic_html_group_table_rights_and_automation_review_pending`  
**Authoritative source:** <https://isiteplus.naic.org/lead-state/publeadstate/pubLSHtml>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** An NAIC group code is not a legal-company NAIC code or LEI and group name may differ from ultimate international parent. A lead state denotes insurance group supervision, not domicile of every subsidiary, underwriting risk location or market share. The official page identifies its reporting period as 2026 Q2. Check terms before any extraction.

## FINMA authorised insurance groups and conglomerates

**Candidate ID:** `ch.finma.authorised-insurance-groups.20261102`  
**Provider:** Swiss Financial Market Supervisory Authority (FINMA)  
**Categories:** `insurance`, `insurer_group`, `regulation`, `switzerland`, `conglomerate`  
**Spatial scope:** Swiss-regulated insurance groups and insurance conglomerates; additional solo entities supervised separately  
**Temporal scope:** FINMA published an updated linked list with date 2026-11-02 on its groups-and-conglomerates page  
**Resolution / granularity:** Versioned official group list linked as a downloadable document; group regulation and consolidated supervision, not ultimate global ownership topology  
**Potential roles:** `switzerland_insurer_group_seed`, `supervisory_group_crosswalk`, `legal_parent_review_queue`  
**Access hint:** `public_html_with_linked_official_list_rights_review_pending`  
**Authoritative source:** <https://www.finma.ch/en/supervision/insurers/groups-and-conglomerates/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Regulatory group designation differs from GLEIF direct/ultimate accounting consolidation and from independently authorised insurer legal entities. List version is 2026-11-02; acquire the exact linked original file, verify licence and cryptographic digest before using any rows. No group members inferred.

## Japan FSA licensed insurance holding companies and insurers

**Candidate ID:** `jp.fsa.insurance-holding-companies.20260601`  
**Provider:** Financial Services Agency (Japan FSA)  
**Categories:** `insurance`, `insurer_group`, `regulation`, `japan`, `holding_company`  
**Spatial scope:** Japan licensed insurance holding companies with separate lists of life, nonlife, small-amount short-term insurers and related institutions  
**Temporal scope:** Insurance holding company official list dated 2026-06-01 in this discovery pass; other classes may have independent versions  
**Resolution / granularity:** Official multi-product register landing page with dedicated Excel/PDF holding-company list and separate direct insurer lists  
**Potential roles:** `japan_insurance_holding_group_seed`, `life_nonlife_entity_discovery`, `group_legal_entity_crosswalk`  
**Access hint:** `public_html_index_official_excel_pdf_rights_review_pending`  
**Authoritative source:** <https://www.fsa.go.jp/en/regulated/licensed/index.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** 15 insurance holding companies reported in the dated holding-company PDF; verify exact original version separately. Do not treat the holding company list as all licensed insurer companies or all foreign groups operating in Japan. Subsidiary identity and shareholder control require independent LEI/corporate evidence.

## Mexico CNSF supervised insurance institutions open dataset

**Candidate ID:** `mx.cnsf.insurer-institutions.2026q1`  
**Provider:** Comisión Nacional de Seguros y Fianzas (CNSF), datos.gob.mx  
**Categories:** `insurance`, `insurer_entity_registry`, `regulation`, `mexico`, `public_csv`, `financial_statements`  
**Spatial scope:** Mexico insurers and insurance mutuals supervised by CNSF, including insurance business classes  
**Temporal scope:** Open government index shows 2026 Q1 lists and 2025 annual data; catalog last updated 2026-07-15 in discovery  
**Resolution / granularity:** Public CSV downloads covering institution names and company types, authorised operations/lines and separate financial statements/statutory indicators  
**Potential roles:** `mexico_insurer_registry`, `latam_legal_entity_crosswalk`, `financial_market_calibration`  
**Access hint:** `public_catalogue_csv_downloads_website_403_observed_rights_review_pending`  
**Authoritative source:** <https://www.datos.gob.mx/dataset/instituciones_sociedades_mutualistas>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Government portal source was found by search but direct browser returned HTTP 403. No official CSV downloaded or hashed in this pass. Preserve separate dataset vintage, insurer legal identity, licensed operation/branch and period; a financial statement row is not geolocated CAT exposure. Rights/automated extraction remain unreviewed.
