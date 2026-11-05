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
**Resolution / granularity:** Original single XLSX 292136 bytes; complete response reassembled via 8 verified HTTP byte-range reads; source-published MD5 0a523543adf76003916186623812ab74 independently matched; computed SHA256 c2fe636c9e7a1e601d64f00f5bdef8fdf9aaa854060f4d5edcd02e1405140944; spreadsheet preview exposes 20 event/country/geographic/loss/source fields.  
**Potential roles:** `country_storm_date_event_crosswalk`, `economic_loss_scale_historical_challenge`, `separate_modelled_vs_reported_origin_label_review`  
**Access hint:** `zenodo_open_record_cc_by_4_0_declared_product_and_upstream_rights_not_reviewed`  
**Authoritative source:** <https://zenodo.org/records/15266959>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** 2026-11-05 ORIGINAL XLSX BYTE IDENTITY: all 292136 original bytes were reconstructed in memory using 8 server range reads; ZIP header present; MD5 independently recomputed exactly matched Zenodo's published 0a523543adf76003916186623812ab74; independent full-source SHA256 c2fe636c9e7a1e601d64f00f5bdef8fdf9aaa854060f4d5edcd02e1405140944. Raw workbook not placed in Git. Only a truncated parsed workbook view and country-specific Kyrill examples were reviewed, not full column/row scientific validation. Official Zenodo API metadata declares CC BY 4.0 and open access, but companion site states research purposes only and material derives partly from EM-DAT, Copernicus and national/insurance sources; redistribution and upstream rights still need review. Some Kyrill country rows explicitly state modelled economic loss from CDS, therefore NOT an independent C3S/CLIMK validation holdout. Country rows for one named storm are not independent physical occurrences; null monetary fields are not zero. 2020 EUR millions means economic impacts, NOT insurer claims, property rebuild cost, real insurer gross/net or AEP/OEP.

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
