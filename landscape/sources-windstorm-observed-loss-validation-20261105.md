<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-windstorm-observed-loss-validation-20261105.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-windstorm-observed-loss-validation-20261105.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-05`  
**Purpose:** Non-admission source candidates for independent European windstorm event-loss and damage-function validation, with strict observational versus modelled and licensing boundaries.

**Entries:** 2

## HANZE European Windstorm Impact Database v1.0 (1950-2020)

**Candidate ID:** `hanze.european-windstorm-impact.v1-0`  
**Provider:** University of Szczecin researchers for European Commission JRC; Zenodo record 15266959  
**Categories:** `windstorm`, `historical_event_catalogue`, `economic_impact`, `nonindependent_modelled_loss_flags`  
**Spatial scope:** Europe, country-identified records with NUTS2 and occasional NUTS3 affected-region strings; affected regions are not asset coordinates or insured exposure footprints  
**Temporal scope:** 1950-2020, publication 2025-04-23, explicit Zenodo record version 1.0  
**Resolution / granularity:** Original 292136-byte SHA256 c2fe636c9e7a1e601d64f00f5bdef8fdf9aaa854060f4d5edcd02e1405140944 XLSX; actual GitHub-runner original-byte and full workbook replay successfully executed 2026-11-05. 1358 country-report rows in 33 countries for 1950–2020, 815 publisher source-reference rows; 687 numeric 2020-EUR-million economic values, 33 nonnumeric nonempty values and 638 blanks; 299 entries explicitly CDS-modelled (278 numeric, 21 nonnumeric).  
**Potential roles:** `country_storm_date_event_crosswalk`, `economic_loss_scale_historical_challenge`, `separate_modelled_vs_reported_origin_label_review`  
**Access hint:** `zenodo_open_record_cc_by_4_0_declared_product_and_upstream_rights_not_reviewed`  
**Authoritative source:** <https://zenodo.org/records/15266959>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** 2026-11-05 COMPLETE ORIGINAL XLSX STRUCTURAL AUDIT (source SHA256 c2fe636c9e7a1e601d64f00f5bdef8fdf9aaa854060f4d5edcd02e1405140944, 8 exact HTTP ranges, MD5 matched original publisher): 1358 country-level event records and 1358 distinct publisher IDs across 33 country codes, 1950–2020; 815 bibliographic reference rows on a separate sheet; original 2020 EUR millions economic-loss field has exactly 720 nonempty cells and 638 BLANK/UNKNOWN cells. The original CDS field (column S) flags exactly 299 country-event losses 'Modelled economic loss from CDS', categorically NOT independent observed C3S/CLIMK loss holdouts. Named Kyrill has 12 country rows and 4 CDS-modelled (AT, IE, LU, PL); never treat them as 12 independent physical storms. The source stores mixed ISO and numeric Excel 1900-serial dates: three preliminary apparent inverted ranges resolved after legitimate serial conversion; one suspect ES row 21072 remains with 2017-02-02 start and 2014-02-02 end. Reproducible bounded stdlib parsing code and offline synthetic tests reside in research_runners/hanze_windstorm_original_workbook_audit_v0.py and tests. These source-row/schema counts do NOT clear upstream rights, observed-vs-derived status of the other rows, completeness, storm parent-ID/annual frequency, geospatial asset mapping, insurer contract semantics or admission. No original XLSX bytes committed. Source metadata advertises CC BY 4.0; third-party conditions and website research-only statement still require separate human review. All review statuses explicitly remain not_admitted/not_reviewed. Original-source replay on public GitHub Actions 42092286511 and original source-origin matrix replay 42092640290 both passed; the exact 2x3 source matrix is: CDS-explicit numeric 278, nonnumeric 21, blank 0; other (not flagged CDS but independence UNVERIFIED) numeric 409, nonnumeric 12, blank 638. The 409 numeric non-CDS-flagged rows are only candidates for primary-source, completeness, source-rights and independent observation review, not 409 independent claims or calibrated losses. No original bytes stored in Git, and no real insurer, annual event frequency, AAL, AEP or OEP promoted.

## Norwegian 1985-2020 municipality-level insured wind-damage study

**Candidate ID:** `norway.wind-damage-municipality-claims.jaison-2024`  
**Provider:** Jaison, Sorteberg, Michel and Breivik; Norwegian Natural Perils Pool; NHESS 2024  
**Categories:** `windstorm`, `observed_insurance_loss_research`, `municipality`, `restricted_claims`, `vulnerability_validation`  
**Spatial scope:** Norway, 356 municipalities in the authors' harmonized study; not individual geocoded insured properties  
**Temporal scope:** 1985-2020 daily insurance counts and amounts, paper published 2024-04-23  
**Resolution / granularity:** Published study compares daily municipality claims and losses with NORA3 winds and four damage functions; article, figures and supplements publicly accessible, but original daily insurance claim dataset is explicitly proprietary and unavailable for download  
**Potential roles:** `independent_norway_wind_damage_methodology`, `zero_inflation_and_event_holdout_design`, `public_aggregate_statistics_screen_if_licensed`  
**Access hint:** `paper_cc_by_4_0_underlying_claims_proprietary_unavailable_some_nask_public_aggregates`  
**Authoritative source:** <https://nhess.copernicus.org/articles/24/1341/2024/nhess-24-1341-2024.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Article data-availability paragraph explicitly says the daily insurance data cannot be shared; the paper CC BY 4.0 is NOT a licence to reproduce proprietary Norwegian claims. NORA3 winds are publicly available and Finance Norway NASK provides some public statistics, but neither automatically recreates the 356-municipality daily 36-year time series. Strong independent published validation methodology and zero-inflation finding only until a separately authorized source-level aggregate or data-use agreement is verified.
