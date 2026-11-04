<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WUMI2026a: publisher parent/subfire genealogy preflight (2026-11-04)

## Source, scope and exact assumptions

This extends the [original author MATLAB-code audit](wumi2026a-author-code-parent-subfire-partition-20261104.md) and the [pinned Dryad ZIP byte gate](wumi2026a-dryad-v458442-original-asset-preflight-20261104.md). The official author [Zenodo WUMI2026a code ZIP](https://zenodo.org/records/21988057) was previously actually downloaded as 157,599 bytes, SHA-256 `193ca68590e230dc855a41212729a420c7a85f1b46ef733537a7efe9eeae3845`. Publisher `19_make_final_lists_of_wildfires.m` has original SHA-256 `6c207a3d31c61954e17d75191ad20dfd058361814909617cc4e5f8e58c5d1547`.

In that author's script, lines 334–354, 424–445 and 473–487 write `subfires/<parent-fireid>.txt` files containing an identical native header, parent row, a blank separator, and source candidate children grouped using blank lines. **Nested sub-sub-fires** are represented as consecutive rows following a top-level child without an intervening blank line. Later, lines 648–686 can adjust nested children, drop recalibrated candidates below **100 hectares**, and **retain** some parents when fewer than two children remain. At lines 667–676 the child polygon areas are re-normalized to the parent polygon area; at lines 689–729 satellite burned-area values and coordinates have a distinct adjustment process.

**Therefore raw `subfires` note counts must never be treated as final independent event counts.** A candidate child might not survive. Parent/child final identity is assessed only by comparing both actual final-list ID sets *and* candidate notes; the first view and the second view must not be added.

## New fail-closed offline command

```sh
python -m research_runners.wumi2026a_original_subfires_genealogy_v0 \
  --original-zip /private/WUMI2026a_final_wildfire_lists.zip
python -m unittest tests.test_wumi2026a_original_subfires_genealogy_v0 -v
```

Only the **exact** publisher original version 458442 ZIP, byte length **4,683,571** and original SHA-256 `8d8a59588935b832bf8e382a0c94b8a6705e6a8fa2bed161bacf1d9fe78726d0` can pass the already-merged upstream byte/ZIP/CRC validator. There is **no** online source download or write to NextGen/Neon. This new runner then reads both final-list members and `subfires/<parent-fireid>.txt` candidate notes *in memory*. It checks native field schema, uniqueness and parent metadata consistency, catches duplicate cross-parent candidate identities, and aggregates parent replacements, untraced final children, nested candidate counts and only **bounded polygon-area metadata summation** with a 4-decimal rounding tolerance.

**Scientific limits:** a publisher genealogy note does not prove physical independent wildfire events or different loss footprints. A summed publisher polygon area does not confirm burned pixels, building damage or insured losses. The source code can apply inferred circles to unmapped fires. Do not use the parent and subfire views together for CAT simulation frequency, event-level XL, inward treaty recovery, retrocession or reinsurance optimization. All rights, ingestion, scientific approval and frequency/insured-loss admission remain blocked pending evidence.

## Exact remaining acquisition blocker

The official original [Dryad v458442 file listing](https://datadryad.org/api/v2/versions/458442/files) advertises the 4.68-MB ZIP and its hash, but the previous read-only actual download received HTTP `401 Unauthorized`. **No original Dryad event ZIP bytes have yet been audited**. The new code and synthetic tests prove only readiness to recognize structural source genealogy and red-flag coverage/area gaps once a permitted original archive becomes locally accessible.

If the original 4.68-MB ZIP contains only the two final lists and not the genealogy notes, this checker returns `BLOCKED` rather than inventing an event genealogy; the notes must then be acquired separately as a vetted original publisher asset.
