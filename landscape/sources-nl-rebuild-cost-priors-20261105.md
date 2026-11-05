<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-nl-rebuild-cost-priors-20261105.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-nl-rebuild-cost-priors-20261105.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-05`  
**Purpose:** Non-admission Dutch replacement-cost index and insurer method discovery for research-only building exposure valuation. Preserve separate entity grain and forbid conversion from cadastral, sale or address data into insured TIV without independent proof.

**Entries:** 3

## Netherlands CBS new residential construction input-cost index 2021=100

**Candidate ID:** `nl.cbs.new-build-input-cost-index.85728ned`  
**Provider:** Centraal Bureau voor de Statistiek (CBS)  
**Categories:** `residential_construction`, `cost_index`, `labor_materials`, `netherlands`, `temporal_rebasing`  
**Spatial scope:** Netherlands aggregate; not a postcode or building-class price survey  
**Temporal scope:** Monthly provisional observations through September 2026; table metadata changed 2026-10-30  
**Resolution / granularity:** 2021=100 index, components total/labour/materials by month and year; dimensionless time escalation, no €/m² or €/m³ base price  
**Potential roles:** `temporal_cost_index_challenge`, `scenario_escalation_of_independently_licensed_rebuild_cost_base`, `construction_cost_inflation_uncertainty`  
**Access hint:** `cbs_statline_open_catalogue_terms_and_series_revision_review`  
**Authoritative source:** <https://www.cbs.nl/nl-nl/cijfers/detail/85728NED>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** CBS 2026 September provisional total input-cost index is 129.5 (2021=100); it is NOT a reconstruction value or independently measured building-specific replacement cost. Revisions and different source-series definitions must be versioned. Do not use to uplift an insurer's 2026 table if that table already incorporates CBS escalation.

## Netherlands CBS new residential construction output-price index 2021=100

**Candidate ID:** `nl.cbs.new-build-output-cost-index.85772ned`  
**Provider:** Centraal Bureau voor de Statistiek (CBS)  
**Categories:** `residential_construction`, `output_price_index`, `new_housing`, `netherlands`, `temporal_rebasing`  
**Spatial scope:** Netherlands aggregate new housing, including contractor overhead/profit, excluding land and project developer or broker costs  
**Temporal scope:** Quarterly observations through provisional 2026 Q2; table metadata changed 2026-09-30  
**Resolution / granularity:** 2021=100 index of new-residential-build construction output price incl/excl VAT, not physical house reconstruction amount  
**Potential roles:** `construction_cost_time_trend_reference`, `alternative_to_input_cost_index_sensitivity`, `rebuild_cost_index_external_challenge`  
**Access hint:** `cbs_statline_open_catalogue_terms_and_series_revision_review`  
**Authoritative source:** <https://www.cbs.nl/nl-nl/cijfers/detail/85772NED>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** 2026 Q2 provisional output price index is 133.4 (2021=100), not €/m² or €/m³. The output and input series are related signals, NOT independent price observations for an individual building and cannot be multiplied together. Their vintages and index bases must align before ratio-based escalation.

## AnsvarIdéa / Turien &amp; Co Netherlands residential rebuilding-value meter 2026

**Candidate ID:** `nl.ansvaridea.turien-residential-rebuild-meter.2026`  
**Provider:** AnsvarIdéa Verzekeringen / Turien &amp; Co Assuradeuren; derivative of Verbond van Verzekeraars 2025 method  
**Categories:** `residential_rebuilding_cost`, `insurer_method`, `volume_pricing`, `netherlands`, `rights_sensitive`  
**Spatial scope:** Netherlands, conventional residential housing categories; atypical historic, monumental, luxury and very large houses explicitly excluded  
**Temporal scope:** 2026-01 edition, valid through 2027-01-31 according to document  
**Resolution / granularity:** Residential reconstruction €/m³ typology guide with corrections for building attributes and volume, intended for insurer/insurance-adviser context; not BAG gross floor m² and not a binding insurance policy  
**Potential roles:** `housing_rebuild_value_method_review`, `sensitivity_pricing_typology_research`, `historical_replacement_value_baseline_rights_pending`  
**Access hint:** `provider_public_pdf_not_open_license_rights_use_and_reproduction_blocked_pending_approval`  
**Authoritative source:** <https://ansvar-idea.nl/media/0t1e1ifn/herbouwwaardemeter-2026-1.pdf>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Private insurer/adviser 2026 method is based on 2025 Verbond van Verzekeraars meter and indexed using CBS inputs. It is NOT a continuing 2026 sector-wide Verband publication: sector association's central meter stopped in 2026. Its own 2026 prices must not be inflated again by the same cost-index period. Needs building external volume in m³, not a dwelling's BAG area in m² or a cadastral parcel area. Provider copyright/redistribution/commercial modelling terms not established. Do not embed price tables in public code, import raw insurer rates into CAT, or claim automatic reconstruction cost/TIV.
