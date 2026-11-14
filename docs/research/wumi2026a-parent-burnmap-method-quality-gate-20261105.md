<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WUMI2026a: per-event burn-map *method* and exposure-footprint readiness

**5 November 2026 — original publisher algorithm reviewed; actual Dryad data ZIP still blocked.**

Original source: [author Zenodo v2 software](https://zenodo.org/records/21988057), `code_wumi2026a.zip` 157,599 bytes, actually downloaded and hashed SHA-256 `193ca68590e230dc855a41212729a420c7a85f1b46ef733537a7efe9eeae3845`; [original Dryad v458442 seven-file inventory](https://datadryad.org/api/v2/versions/458442/files). Read the [existing SHA-audited source and genealogy review](wumi2026a-author-code-parent-subfire-partition-20261104.md). This source contains a **method selection algorithm**; this repository does **not** possess original per-fire raster or ZIP bytes.

## Why this matters for real CAT loss simulation

The author MATLAB `19_make_final_lists_of_wildfires.m`, lines 565–580, branches in order: `dataset=mtbs` → `burnarea_mtbs.nc`; `dataset=calfire` → `burnarea_calfire.nc`; `dataset=wfigs` → `burnarea_wfigs.nc`; then non-empty `object_ID_wfigs` → WFIGS; `object_ID_usgs` → USGS; `object_ID_iafph` → IAFPH; otherwise `burnarea_circle.nc`.

This source selection is not uniform in scientific quality:

| Publisher method label | Source method | Risk when over-interpreted |
| --- | --- | --- |
| `MTBS_LANDSAT_CLASSIFICATION_METHOD` | MTBS 30-m satellite-derived burn-severity classification | Publisher method attribution **does not validate any actual original Landsat raster or per-event mask** |
| `AGENCY_PERIMETER_UNIFORM_BURN_ASSUMPTION` | CalFire / WFIGS / USGS / IAFPH source perimeter, with uniform-burned-area assumption in publisher code | Agency boundary ≠ verified internal burned pixels or individual building loss |
| `HYPOTHETICAL_CIRCLE_UNIFORM_BURN_ASSUMPTION` | Estimated circular perimeter around original reported ignition location | Geometry is explicitly modelled; neither original observed perimeter nor observed burn severity |

The publisher's [README and original field descriptions](https://datadryad.org/dataset/doi:10.5061/dryad.63xsj3vd4) describe the source files and methods. Do **not** turn the above labels into independently measured hazard, insurer inventory, insured loss or model events without original bytes, source rights, map validity, resolution and scientific review. The parent-only `no_subfires` view is used here. Child-only adjustments **must not** be added to its occurrence population.

## Executable original-byte-bound method audit

```sh
python -m research_runners.wumi2026a_parent_burnmap_method_v0 \
  --original-zip /private/WUMI2026a_final_wildfire_lists.zip
python -m unittest tests.test_wumi2026a_parent_burnmap_method_v0 -v
```

Requires exact [Dryad version 458442](https://datadryad.org/api/v2/versions/458442/files) file `WUMI2026a_final_wildfire_lists.zip` (publisher file ID 4917545, 4,683,571 bytes, SHA-256 `8d8a59588935b832bf8e382a0c94b8a6705e6a8fa2bed161bacf1d9fe78726d0`) and its original ZIP CRC. After SHA/CRC validation, only the original `no_subfires` list is inspected *in memory*. It validates original row syntax and IDs with the existing event-list gate and computes only **aggregate** per-year source-method counts, original source-ID missingness, and numbers with unavailable burn-area metadata. No fire IDs, geometries, individual area or mapped raster bytes are emitted.

Actual `/api/v2/files/4917545/download` and `/api/v2/files/4917560/download` returned HTTP **401 Unauthorized** on 5 November 2026 from the read-only execution environment, while the metadata API returned 200. Therefore **no real WUMI archive, maps, original event counts, spatial overlay or model-ready hazard** has been verified in this work. A later authorized download is required; do not weaken the SHA and license gates or confuse source provenance with science admission.

## Next scientific acceptance gate

For each actual event, reconcile the publisher map-choice labels with the corresponding **original source-perimeter or original raster member**, independently verify CRS/time/burned-area semantics, and spatially overlay an eligible synthetic exposure portfolio. Run sensitivity analyses by map-method tier: MTBS observed-severity *claim*, agency perimeter uniform-burn approximation, hypothetical circle. Only then consider frequency, severity, net treaties or OEP/AEP use.
