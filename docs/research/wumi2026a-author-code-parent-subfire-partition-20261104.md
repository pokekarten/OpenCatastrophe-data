<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WUMI2026a original author-code identity and parent/subfire event semantics

**4 November 2026 — public original software directly fetched and SHA-256 computed.** The published [Zenodo code WUMI2026a v2](https://zenodo.org/records/21988057) contains the original authors' `code_wumi2026a.zip`, 157,599 bytes. An actual read-only download succeeded, hash: `193ca68590e230dc855a41212729a420c7a85f1b46ef733537a7efe9eeae3845`; 46 ZIP members (including `__MACOSX` metadata). The specific author code `19_make_final_lists_of_wildfires.m` was inspected in memory, 27,320 bytes, SHA-256: `6c207a3d31c61954e17d75191ad20dfd058361814909617cc4e5f8e58c5d1547`. **The author source code is referenced, not copied into this public repository.** This is separate from [Dryad dataset version 458442](https://datadryad.org/api/v2/versions/458442/files): its `WUMI2026a_final_wildfire_lists.zip` is still **not actually downloaded or SHA-verified** due the 401 access result in the prior work.

## Confirmed from the original 2026 author MATLAB algorithm

In `19_make_final_lists_of_wildfires.m`:

- Lines 14–85 read merged agency events and write `WUMI2026a_wildfires_1984_2026_no_subfires.txt`. Agency-specific events linked to parent MTBS/CalFire perimeters are first suppressed; another pass handles common WFIGS IDs.
- Lines 136–193 identify parent-fires with multiple associated subfires via MTBS, CalFire or WFIGS references.
- Lines 198–520 build `subfires/<parent-fireid>.txt` genealogical notes. Some files contain **nested sub-sub-fires**; blank lines denote top-level subfire separation.
- Lines 565–580 choose the parent's burn-area map provenance: MTBS (Landsat-derived within-perimeter), CalFire, WFIGS, USGS, IAFPH or fallback `burnarea_circle.nc`. **Some maps are assumed circular or uniformly burned rather than directly observed.**
- Lines 648–685 adjust sub-sub-fire contributions, rescale child **polygon area** to the parent `poly_area_ha` and discard candidate children below 100 ha after size adjustment. If there are not multiple surviving subfires, the source code keeps the parent (lines 755–762).
- Lines 689–729 separately scale child **satellite burned area** if available and snap coordinates to the nearest burned parent-map cell. The writer retains `code_new{j}` from the original child `fireid` (lines 700–750): **never recompute original fireid from adjusted lat/lon**.
- Lines 738–773 replace eligible parent rows in the `with_subfires` view and write `WUMI2026a_wildfires_1984_2026_with_subfires.txt`. The two final lists are different *alternative* views of overlapping event sources, **not additive datasets**.
- The writer uses raw comma-separated text (`fprintf(fid,'%c',lab)`; then rows) instead of exporting an independent event-ID mapping contract. Both file headers come from the same previously merged source list. The original [Dryad README](https://datadryad.org/dataset/doi:10.5061/dryad.63xsj3vd4) lists `fireid`, `dataset`, `year`, `poly_area_ha`, `burn_area_ha` and the partner-source IDs. There is a naming inconsistency around `FOA_ID` vs `FPA_ID` in the displayed README/code. Do not assume these are independently verified stable insurer event IDs.

The author code can be downloaded independently, but **its public availability does not admit or license the original Dryad dataset assets**, the publisher's upstream CalFire/FPA/WFIGS material or any commercial CAT application.

## Prepared executable alternate-list count audit

Once the exactly pinned original 4.68 MB dataset ZIP is accessible, the [prior byte/CRC gate](../../research_runners/wumi2026a_dryad_original_asset_receipt_v0.py) validates it first. This additional runner reads only the two exact named original list members in memory (no extraction), validates aligned typed CSV headers/rows and duplicate `fireid` identifiers, and counts shared/replaced/added IDs separately without printing original identifiers or coordinates. It records year-by-year view counts, missing publisher polygon/satellite area values and identity-date disagreements for review.

```sh
python -m research_runners.wumi2026a_parent_subfire_partition_v0 \
  --original-zip /private/WUMI2026a_final_wildfire_lists.zip
python -m unittest tests.test_wumi2026a_parent_subfire_partition_v0 -v
```

**Not claimed:** exact parent-child genealogy from `subfires/`, conservation of child polygons/burn areas against parent maps, statistically independent observations, native geocoded insurance occurrences, all-fire or national frequency, ground-up or insured losses, or data reuse permissions. Only validated 2026 original ZIP bytes plus a future separate genealogy and science review can support those stronger claims. Code/test fixtures use **synthetic-only events** and deliberately do not contain the author original data.

## Fix to existing ZIP preflight

The first ZIP validator had an unjustifiably low ceiling of **40 ZIP entries**, while the source code generates one `subfires/<parent-fireid>.txt` file per eligible parent and many real archives will have more. This revision allows up to **20,000 checked entries**, still imposing compressed input size 5 MB, per-entry decompressed bytes 30 MB, combined uncompressed bytes 80 MB, absolute/path traversal/symlink/encryption checks and ZIP CRC validation. The author source ZIP itself has **46** members and provides a clear demonstration why the old 40-member heuristic was not generally safe as a source-archive assumption. This is a bounded *compatibility correction*, not a relaxation of source rights, byte identity or scientific admission.
