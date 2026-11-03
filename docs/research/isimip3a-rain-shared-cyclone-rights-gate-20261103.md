<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ISIMIP3a cyclone rain: rights gate and shared-physical-event modelling handoff — 2026-11-03

## What is verified

- ISIMIP officially lists historical **1950–2021** tropical cyclone observations and modelled wind/rain impact fields, based on IBTrACS tracks and ERA5. The gridded product family is around 300 arc seconds. See [official input specification](https://www.isimip.org/gettingstarted/input-data-bias-adjustment/details/182/).
- Public dataset filelist under fixed ISIMIP dataset ID `f08ab32e-b3ad-4984-81d1-495235765b6c` contains 72 annual `er11-wind_obsclim_historical_maxrain_YYYY.nc` **names**, from 1950 through 2021. The enclosing `ER11-wind` path is a *model/variant directory*, not evidence that `maxrain` represents a wind variable.
- The [ISIMIP public repository terms](https://www.isimip.org/gettingstarted/terms-of-use/terms-use-publicly-available-isimip-data-after-embargo-period/) expressly state that **sale of data is forbidden** and use is governed by the **assigned dataset/file licence**. The [ISIMIP licensing guidance](https://www.isimip.org/gettingstarted/terms-of-use/licenses-publicly-available-isimip-data/) encourages CC0 for **model output** but makes no general input-data licence guarantee. Therefore product-specific commercial insurer reuse is `unknown`, **not approved**. Data sale prohibition is not automatically a comprehensive ban on every downstream commercial derivative; the exact licence must be reviewed.
- The proposed canonical entry `isimip3a.tc.er11-wind.historical.maxrain.1950-2021` is for **non-admitted research only**. The previously merged `research_runners/isimip3a_er11_maxrain_filelist_preflight_v0.py` uses this exact identity. That runner never downloads external data.

## Physical cyclone versus peril / event lineage

**One physical tropical cyclone should not be transformed into three independent random event occurrences merely because separate wind, rain and surge sources are used.** Build the following logical relationships, after legal access and exact variable semantics have been reviewed:

| Concept | Identity and model role | Fail-closed rule |
| --- | --- | --- |
| `physical_event_id` | Observed cyclone identifier (prefer verified canonical IBTrACS SID after original file review), start time, basin and source-vintage mapping | No automatic fuzzy joining by storm name or calendar year alone |
| `hazard_component_id` | Distinct component from same physical event, e.g. `wind`, `tc_rain`, `storm_surge` | Preserve distinct units, grids, timestamps, aggregation, forcings and original file IDs |
| `realization_id` | Stochastic simulation year and synthetic event occurrence (separate from 1950–2021 observation years) | Do not treat 72 historic files as 72 IID stochastic years or create independent Poisson counts per linked component |
| `exposure_id` | Insured or synthetic building / location identity and peril-specific susceptibility | Building geometry or occupancy proxy is not insured TIV |
| `loss_component_id` | Peril-specific event damage component, vulnerability and financial loss | Do not sum wind/rain/surge losses for the same property unless overlap/double-counting and financial terms are explicitly addressed |

The common synthetic occurrence process should drive a *shared cyclone parent event* and its dependent hazard components. Vendor loss tables (ELTs), occurrence/annual loss tables (YLTs), inward and outward treaties can then retain a traceable event relationship; independent event IDs across vendor catalogues must be mapped **only after evidence-based crosswalk**, not inferred by numerical similarity. Primary loss and secondary uncertainty, hours clauses, sublimits and annual aggregates belong to the later NextGen financial model and are not computed by this data discovery PR.

## Model handoff / acceptance gates

1. **Filelist identity**: exact 72-year URI inventory, independent pinned filelist SHA-256, expected dataset UUID, correct ER11-wind/maxrain pathway. Current offline runner covers syntax and completeness when given a verified local list.
2. **Rights**: source-specific assigned file licence, IBM/ERA5/IBTrACS provenance and attribution, commercial modelling and derivative rules, redistribution, ISIMIP terms. Until these are checked, do not automate downloads or promote to model inputs.
3. **One bounded NetCDF**: only when authorised, validate original bytes, SHA-256, variable names/units/time coords/CRS/fill, event IDs, no-data, grid and true interpretation of maximum 24-h rainfall. This metadata is currently **unverified**.
4. **Hazard independence**: modelled ISIMIP rain is not independent observational truth relative to its IBTrACS parent. Never count two hazard reconstructions as two historic cyclones.
5. **Reproducibility**: pin provider dataset ID, exact file version and checksums; source identity must survive downstream in NextGen/OED/vulnerability mappings and capital/reinsurance treaty analysis.

**Status: documentation and canonical *non-admission* catalogue only; no NetCDF bytes, Neon records, insurer financial data, admission decision, or commercial permission.**
