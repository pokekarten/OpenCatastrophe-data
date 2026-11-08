<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-hail-stormobject-research-20261108.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-hail-stormobject-research-20261108.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-08`  
**Purpose:** Non-admission discovery of published Swiss radar hail storm-object predictors and crowdsourced label benchmark; no original source bytes, model admission, or insurer data.

**Entries:** 1

## Swiss Storm-Object Radar Predictors and Crowdsourced Hail Labels v1

**Candidate ID:** `ch.aregger.hail-stormobjects.2020-2024.v1`  
**Provider:** Martin Aregger / University of Bern / MeteoSwiss research / Zenodo  
**Categories:** `hail`, `convective_storm`, `radar`, `crowdsourcing`, `machine_learning`, `observation_labels`, `switzerland`  
**Spatial scope:** Switzerland and approximate 50 km buffer around the national border  
**Temporal scope:** Convective storms 2020-2024; deposited public v1 2026-01-02; companion 2026 peer-reviewed hail detection publication  
**Resolution / granularity:** One ~3.7 GB ZIP 'radar_predictors.zip', publisher MD5 d461e6dd7a606a1cd1933da49f774d3a; object-based polarimetric C-band radar predictors with matched crowdsourced hail labels for tracked Thunderstorms Radar Tracking (TRT) cells; original internal row schema and counts unverified  
**Potential roles:** `hail_detection_probability_benchmark`, `hail_size_classification_hazard_training`, `radar_observation_crowdreport_holdout`, `crossborder_hail_model_intercomparison`  
**Access hint:** `public_zenodo_v1_cc_by_4_reported_original_zip_hash_metadata_only_not_admitted`  
**Authoritative source:** <https://zenodo.org/records/18128983>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original publisher Zenodo v1 declares CC BY 4.0; this is not a separate blanket permission for upstream raw MeteoSwiss radar observations or original crowdsourced reports. Paper 'Hail Detection and Sizing for Storm Objects: A Random Forest Framework Using Swiss C-Band Radar and Crowdsourced Reports' (online 2026-08-04): https://journals.ametsoc.org/view/journals/aies/5/3/AIES-D-26-0001.1.xml . Reproduction code: https://github.com/MartinAregger/HailForest_publication. Publisher file name and MD5 are recorded from Zenodo, but no ZIP bytes downloaded and no SHA-256 independently observed. Label occurrence, report completeness, temporal leakage and same-storm train/holdout grouping must be checked. This is a hazard observation/classification benchmark, not hailstone diameter ground truth for every cell, an insurer claims database, vulnerability curve or stochastic year catalogue.
