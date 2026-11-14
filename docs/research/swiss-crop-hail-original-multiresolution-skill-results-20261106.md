<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# First independent real-source Swiss crop-hail binary footprint skill across 1/2/4/8 km

Research-only replay dated 2026-11-06. **NOT** actuarial annual CAT-loss calibration, and **NOT** proven numerical/bitwise parity with all original study figures.

Primary published formulation: Portmann et al., *NHESS* 24, 2541–2558 (2024), https://doi.org/10.5194/nhess-24-2541-2024, equations 1–3 and verification section 2.5.

## Verifiable original run receipts

- Exact, publisher-MD5-checked 1 km MESHS and POH hail hazard + exposure + observed historical damage: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42250217277
- Independent **original** max-hazard re-aggregation to 2, 4 and 8 km, Swiss projection EPSG:2056 and origin E=2,255,000 / N=840,000 m, plus real crop damage binary-scoring: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42251687616
- Source data identities pinned in research/observations/swiss_crop_hail_zenodo_original_eight_file_receipts_v0.toml
- All **48** crop×hazard×resolution binary source-score families with **192** contingency-metric receipts are preserved in the aggregate-only research/observations/swiss_crop_hail_original_1_2_4_8km_binary_skill_v0.jsonc.
- Independent offline tests/test_swiss_crop_hail_real_skill_receipts_v0.py re-computes HSS/POD/FAR/FB/CSI from all 192 source counts, checks population conservation and verifies that crop damage outside source-exposure geometry has not been silently reclassified as correctly forecast.

No original source arrays, confidential claim values, individual coordinates, or executed published third-party code have been persisted. The original author's GPL code was consulted only for scientific methodology and Swiss spatial grid parameters, not copied as source code.

## Model and evaluation population

The binary damage-footprint model is \`I(n_fields >= 1) * I(hail radar intensity >= threshold)\`; scores are pooled across *crop-specific* selected original historical damage dates (10 for barley, 11 for wheat and rapeseed, 12 for the other categories) and the exposed 2021 source grid cells. This is a historical *in-sample* benchmark of a simple threshold policy, not annual frequency or a loss-to-currency function.

1 km crop-to-radar nearest-centroid positional offset was at most **3.794 m** in metric EPSG:2056. In the coarse grids, the source crop-centroid offset to independently reconstructed exact grid cell centres was at most **0.001 m**. This supports correct **source-grid** alignment but does not establish all proprietary CLIMADA/author numerical conventions match identically.

The coarse radar aggregation uses **maximum of 1 km original radar intensities** for each 2, 4, and 8 km LV95 projected grid cell. **Do not** substitute nearest 1 km sampling or average radar intensity for the paper's coarse-grid method.

## Comparable MESHS 30 mm threshold: field crops versus grapevine

| Source grid | HSS: field crops aggregate | HSS: grapevine |
|---|---:|---:|
| 1 km | 0.3360 | 0.3158 |
| 2 km | 0.3983 | 0.2959 |
| 4 km | 0.4279 | 0.2771 |
| 8 km | **0.4526** | 0.2613 |

The trend closely matches the paper's reported **qualitative** scale effect: improvement for aggregated field crops at 8 km, and deterioration for spatially clustered grapevines as resolution becomes coarser. These are *our own source-replay scores* under a prespecified 30 mm threshold, not verbatim published benchmark numbers. Do not call the best threshold picked in-sample an out-of-sample calibrated optimum.

At 1 km, the MESHS 30 mm aggregate-field-crop contingency is TP=2,830, FP=7,540, FN=2,276, TN=140,258, with HSS=0.3360. At 8 km under the same 30 mm threshold, field-crop HSS=0.4526 (see the machine-readable source proof for full contingency and other choices).

POH was also independently replayed at 40, 60, 80 and 90 percent. As in the study, POH tends to detect more positive crop damage at low thresholds but generates many more false alarms than MESHS. Do not compare POH at its best tested 90% threshold with MESHS at 30 mm and claim intrinsic sensor superiority; comparable forecast operating costs / POD–FAR trade-offs are needed.

## Explicit omitted-positive observation boundary

The independent earlier original n_fields>=1 audit finds **550 positive sparse damage event-grid entries** with no matching 2021 source exposure coordinate, in three 2 km crop comparisons: maize 247, rapeseed 133, wheat 170. These do not become false alarms or insured claims. The paper-style 2 km contingency conditions on **existing exposure support** and excludes them, as documented. Both the source-skill pilot and the machine-readable research receipt carry their excluded-positive counts. A separate sensitivity count can add these positive observations as misses without inventing true negatives beyond the exposure domain. Do not silently drop them from completeness reporting.

## Remaining research blockers and next gates

1. **Exact numerical reference comparison:** Review the published authors' figure tables at exactly the same threshold and sample selection, including harvest-day filters, individual crop weighting, no-exposure treatment, and HSS reference. Do not claim full scientific parity yet.
2. **Unseen-event validation:** Hold out one of the 10–12 original selected event days when choosing MESHS/POH threshold; report event-fold score stability rather than using the same data for tuning and evaluation. The existing 192 threshold scores alone do not provide per-day fold variance.
3. **Source rights and geographic history:** Audit source-level MeteoSwiss radar/insurer derived data permissions and original 2017–2021 farmland geography, including canton-specific terms.
4. **Insurer CAT bridge:** Independently construct a dated synthetic agricultural policy portfolio with explicit crop hectares/insured crop value, loss function, and separate financial contract layers. No monetary severity, covered insured loss, real insurer portfolio, occurrence-year process or annual OEP/AEP has been validated here.

These are **model research outputs only**. A successful HSS test does not imply a reliable insured monetary catastrophe risk model or legal admission of the underlying claims.
