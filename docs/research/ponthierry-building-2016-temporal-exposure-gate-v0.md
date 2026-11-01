<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ponthierry building vintage: reproducible 2016 flood exposure gate

Review date: **2026-11-01**. This is a source-specific scientific diagnostic in the CAT-only Neon `insurance-risk-core` **main** branch, not an admitted 2016 flood or insurer CAT loss model.

## Live original-source observations

`research.fr_ponthierry_rnb_ign_building_v0` has **two** current buildings, exact RNB/IGN identifiers, source response hashes, present-day footprints, IGN heights and reference metadata. The matching QA view reports two nearly identical geometries (IoU **0.999915** / **0.999935**); **both share upstream BD TOPO geometry lineage**. High geometric similarity between these data is **not independent spatial validation**.

`research.fr_ponthierry_current_buildings_2016_q_context_v0` produces **20** contextual rows: two unique buildings × **ten distinct 2016 historical gauge days**. It is a *time-context association*, not 20 insured buildings, proof of flood extent, event linkage, or building-level flood water depth.

The two current IGN records were modified after 2016 (2021 and 2024). **A modification date is not the construction date or proof that the original structure did not exist in 2016.** Conversely, a current building polygon is not a verified *historic* polygon.

`research_runners/sql/fr_ponthierry_building_2016_exposure_gate_v0.sql` is the new data-layer answer: one row per current building with independently named QA and 2016 station-time context counters and explicit separate gates for historical building state, independent geometric evidence, licensed inundation polygon/depth and insured value. The view always returns `model_input_approved=false`.

Executed live against CAT-only Neon main on 2026-11-01:

| Evidence | Observed |
| --- | ---: |
| Current buildings / historic time-context rows | 2 / 20 |
| Historic gauge dates per building | 10 |
| Source-independent geometry proven | 0 of 2 |
| Validated 2016 building geometry | 0 of 2 |
| Verified 2016 building inundation and depth | 0 of 2 |
| Verified insured replacement values | 0 of 2 |
| CAT model input admitted | 0 of 2 |
| First blocker for both | `BLOCKED_UNVERIFIED_2016_BUILDING_STATE` |
| SQL consistency assertions | 14 of 14 passed |

`research_runners/sql/fr_ponthierry_exposure_vintage_invariants_v0.sql` checks building count conservation, unique IDs, no hydrology multiplication, 2016 date scope, nonadmission, current-source SHA format and source geometry bounds. Passing **does not** prove the original HTTP source bytes were independently recaptured and verified.

## Primary sources, provenance and an important archival trap

- Official [RNB FAQ](https://rnb.beta.gouv.fr/faq) explicitly says the RNB building geometry draws mainly from **BD TOPO and BDNB**, and that RNB geometry is primarily for building identity rather than a unique physical geometry truth. Do not count RNB and IGN agreement as independent measurements.
- Official [BD TOPO product description](https://www.data.gouv.fr/datasets/bd-topo-r) documents metric 3D buildings, heights, edition updates and historical-change products. An **edition date** or an IGN **database creation / last-modified timestamp** is not necessarily the physical building's construction or earliest presence date.
- Official [BD TOPO Historique](https://www.data.gouv.fr/datasets/bd-topo-r-historique) is advertised as 1993–1996, 1994–2002 and 2002–2009 historical seasons. **This product alone is NOT evidence for a 2016 historical building snapshot.** We must find the actual versioned **2015/2016 edition** for the area, and verify its existence, geographic coverage, licence, exact provider bytes/sha, layer/schema and as-of methodology before any 2016 geometry claim.
- The [RNB API](https://www.data.gouv.fr/dataservices/api-rnb) can provide *current* records and history/differences. A retrospective edit trail alone cannot prove complete reconstruction of 2016 building stock.
- A building's `date_d_apparition` or first attested year (when available in a properly reviewed BD TOPO vintage) may support temporal evidence but does not by itself prove 2016 polygon geometry, condition, flood extent, occupancy or insured TIV.

## Next reproducible data-source work

1. Retrieve **official period-correct** Seine-et-Marne (department 77) BD TOPO 2015/2016 edition *outside Git*, preserving exactly selected area, edition, access URL, retrieval time, byte length, SHA-256, CRS, licence and all building creation/appearance/confirmation field definitions. If unavailable, explicitly label historic state unknown.
2. Build a one-to-one/split-merge-aware historical-to-current footprint matching QA. Compare each **2016** polygon to current RNB/IGN with geometry/ID lineage and independent source uncertainty; re-use `scripts/building_footprint_overlap_v0.py` (candidate matching only), never infer an insured building from high IoU alone.
3. Obtain exact licensed **2016** Copernicus/official flood inundation geometry with event date, depth and coordinate/reference evidence. Station discharge **does not** supply parcel water depth.
4. Only separately infer or estimate financial values with labelled **synthetic assumptions**, independently admissible occupancy/cost sources and insurer-specific coverage terms, preserving observed building stock versus hypothetical insurance coverage; run validated holdouts prior to CAT model promotion.
5. Keep the 2016 hydrological event research and current building register separate until all temporal, spatial, provenance, rights and insured-value gates pass.

No external source raw bytes or private insurance information are committed, and no model simulation, original event footprint or insured risk is created by this diagnostic.
