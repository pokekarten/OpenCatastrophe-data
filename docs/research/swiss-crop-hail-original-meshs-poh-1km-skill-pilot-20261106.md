<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Swiss crop hail: first original MESHS / POH 1 km binary skill pilot

Research-only prototype, 2026-11-06. **Not** a production CAT-loss model or a replication of every figure in Portmann et al., *NHESS* 24, 2541–2558:
https://doi.org/10.5194/nhess-24-2541-2024

## Exactly what this pilot computes

On the **four checksum-pinned original release files** (MESHS, POH, 2021 crop exposure ZIP and observed historical damage ZIP), use only the **1 km** members of the six crop families, including the combined field-crop category.

1. Validate 12 unique original MESHS and POH event ordinal dates, identical source radar centroid axes (454,400 centroids), finite nonnegative sparse intensities, and version-specific publisher MD5.
2. Select each published 1 km crop HDF5 point with actual \`n_fields >= 1\`, not an arbitrary geographical footprint. Join positive sparse observed impact cells by an exact 5-decimal source latitude/longitude key. Fail rather than silently omit any observed positive not in the 2021 exposure (the previous original-source receipt showed full coordinate coverage for **all six 1 km pairs**).
3. Associate exposure centroid to **nearest source radar centroid in EPSG:2056**, using a strict upper bound **800 metres**, because latitude/longitude decimal-degree distances are not metric. This is a reproducible, explicit approximation to the CLIMADA centroid assignment, **not** evidence of bitwise parity with its implementation. Any out-of-range point blocks the score.
4. For each crop and *its selected observed event dates only* (10–12 days by crop), read original per-event sparse MESHS/POH intensities and make binary forecasts according to the paper's step function: \`forecast = (n_fields >= 1) AND (intensity >= s)\`. MESHS thresholds 20, 30, 40 and 60 **mm** and POH thresholds 40, 60, 80 and 90 **percent** are research-grid settings rather than an optimized production policy.
5. Over *each selected observed event day × each present 1 km exposure cell*, count hit, false alarm, miss and correct negative and derive POD, FAR, frequency bias, CSI and HSS. Undefined denominator produces JSON null. Save **aggregate-only summaries** to ephemeral GitHub runner logs; never print original coordinates, claim values, raw original bytes or a list of individual policies.

Execution (isolated GitHub Actions environment with pinned h5py, numpy, scipy and pyproj):

    python -m unittest -v tests.test_swiss_crop_hail_original_1km_skill_pilot_v0
    python -m research_runners.swiss_crop_hail_original_1km_skill_pilot_v0

Workflow: \`.github/workflows/swiss-crop-hail-original-1km-skill-pilot.yml\`.

## Limits and next validation

- This 1 km pilot is **in-sample**, using selected historically damaging events. Do not annualize the 12 dates or apply selection-biased event frequencies.
- Other original publication resolutions (2, 4 and 8 km) **require the published Swiss LV95 spatial-grid aggregation with maximum radar intensity**. Simply joining coarser crop-grid points to unaggregated 1 km pixels is mathematically incorrect. The original research helper \`aggregate_hazard\` uses EPSG:2056 and \`max\` aggregation; match that separately before comparing HSS for 8 km field crops.
- The published authors' CLIMADA version, selected-event harvest filters, nearest-centroid tie rules and per-crop aggregation may differ from this independent pilot; do not claim numeric paper-figure parity before reference comparison. The original paper reports MESHS thresholds with detection/false-alarm trade-offs and best field-crop performance around 8 km vs grapevine around 1 km. This pilot estimates only 1 km figures.
- Source **damage-grid values are indicators/counts**, not verified insured monetary losses. This is not a synthetic insurer exposure valuation, a vulnerability-to-currency relation, a Monte Carlo event-year simulation, or a valid OEP/AEP net or gross.
- Public Zenodo record licences do not by themselves complete underlying data-origin or insurer-contribution reuse clearance. No original raw values are checked into GitHub or Neon.

Scientific release gate: expose source receipts, check event support integrity, confirm radar centroid coverage and match numerical results to published reference (including authors' sample, threshold and resolution), then tackle 2/4/8 km spatial aggregation. Keep PR #1396 draft until source and scientific reviews are complete.
