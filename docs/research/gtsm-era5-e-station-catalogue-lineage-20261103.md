<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GTSM-ERA5-E v2 — original station-ID selection and parent-catalogue QA (2026-11-03)

## Why this is needed

The actual pinned original statistics NetCDF `ds_GTSM-ERA5-E_1950-2024_stats.nc` contains **38,957** station rows with validated latitude/longitude coordinates and a separate native `stations` variable stored as uint16. Its 9,652,424 bytes and source SHA-256 `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767` are verified with the fixed original-source workflow.

The peer-reviewed [Aleksandrova et al. 2026 ESSD paper, section 2.1](https://essd.copernicus.org/articles/18/5759/2026/) states that the **GTSMv3 simulation uses 44,734 output locations**: approximately **18,000 coastal points** spaced roughly 10–50 km along coasts and additional offshore/ocean points on a semiregular grid. **44,734 − 38,957 = 5,777** is a numerical difference between a paper's simulation-location count and a specific statistical asset's row count, **not** proof of 5,777 missing insured/coastal sites or misprocessed data.

The original statistical asset does not include the `station_name` or original coast/ocean category in its validated native schema. A raw global spatial bounding check cannot classify a hydrodynamic point as relevant to a coastal asset.

## New deterministic source-size-bounded station-ID audit

`scripts/gtsm_era5_e_station_id_qa_v0.py` reads **only** the source-native `stations` uint16 coordinate vector in an isolated, ephemeral file **after** exact original byte size/MD5/SHA-256 and native NetCDF-header checks. The workflow's new `--audit-station-ids` flag emits only aggregated diagnostics:

- native station-ID rows, missing/fill records, distinct IDs, duplicate ID records, adjacent index-order violations, the width of the occupied native-ID span and count of *internal* gaps inside that span;
- counts outside a **hypothetical** zero-based `0..44,733` and one-based `1..44,734` parent catalogue index;
- explicit `parent_catalogue_index_identity_proven=false`, `paper_output_location_count_same_release_proven=false` and `coastal_vs_ocean_station_membership_proven=false`.

It never logs individual station IDs, positions, coordinates, loss samples, source arrays or model event-level input. The source is removed after the isolated GitHub run; no data are ingested into Neon.

The exact-head original workflow must complete before reporting actual ID counts, spans or whether the original statistical IDs appear to match either indexing scheme. Even if all numerical IDs fall within the expected published range, **index-range compatibility is not a confirmed mapping to the publisher's 44,734 output locations**.

## Scientific gap: a reproducible station-index lineage join

To establish true parent-index coverage, obtain the *same-release* GTSM v3 original output-location catalogue and the exact postprocessing selection/filter code or name/index mapping used to generate this original statistical NetCDF. Validate its source hash, author, version, CRS, coordinate packing, station-name conventions, output order and the coast-versus-ocean distinction. Some GTSM tooling, such as [Deltares dfm_tools, SSH catalogue subsetting](https://deltares.github.io/dfm_tools/notebooks/subset_retrieve_sealevel_observations.html), splits GTSM `grid` versus `coast` classes by station-name convention, but that is **external catalogue-dependent logic**, not proof of corresponding classification in our Zenodo statistics version.

Only a properly versioned catalogue-to-statistics join can explain how 44,734 paper model points became 38,957 statistical entries, prove which are coastal, and support an exposure proximity/model-support challenge. Full raw catalogue and provider data rights, spatial validation and independent tide-gauge holdouts must precede any worldwide building join, exposure-to-hazard mapping, insured loss calculations or stochastic YLT/ELT production.

**All model admission and commercial-rights flags remain false.**

## Observed original native station-ID receipt (2026-11-03)

The successful, exact-head GitHub [original-source run 41703953665](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41703953665), job `126154214817`, passed **74 offline/synthetic tests** before reading the fixed original 9,652,424-byte NetCDF. Publisher MD5 and independently pinned original SHA-256 `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767` match. The native `stations` variable (uint16) yields the following **original aggregate-only** evidence, without publishing any IDs or coordinate pairs:

| Exact original native station-ID QA | Observed |
| --- | ---: |
| Rows | 38,957 |
| Distinct IDs | **38,957** |
| Duplicate IDs | **0** |
| Native fill-ID records | **0** |
| Adjacent non-increasing ID pairs | **0** |
| Width of occupied native-ID span | **43,734** |
| Unrepresented integer IDs *within* observed span | **4,777** |
| IDs outside a candidate zero-based 44,734-item parent index | **0** |
| IDs outside a candidate one-based 44,734-item parent index | **1** |
| Paper model locations − statistics rows (arithmetic only) | **5,777** |

The observed IDs are strictly increasing, distinct and compatible with the **numerical range** of a hypothetical zero-based parent catalogue. The one-based indexing hypothesis fails one range comparison. If and **only if** this paper's 44,734 model-point catalogue uses the same original zero-based indexing as the statistics file, the 5,777 unrepresented integer labels decompose into **4,777 within the native occupied span** and **1,000 beyond its upper end**. This is *conditional arithmetic*, not a confirmed physical dropout mechanism, missing coastal sites, a file error or confirmed parent catalogue identity.

The next version of this audit adds further aggregate-only diagnostics of contiguous ID-gap runs and validates their reconciliation to the reported count of 4,777. Do not prestate those run counts before a successful exact-head source workflow.

The original author [ESSD study](https://essd.copernicus.org/articles/18/5759/2026/) differentiates about 18,000 coastal locations from offshore ocean output stations; nothing in an unsigned uint16 ID range alone supplies this membership. The source index mapping, point-name/coast-class catalogue version and any omitted-domain reasons remain outstanding.
