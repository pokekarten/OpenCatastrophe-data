<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# First official PLATEAU original CityGML test asset: Hokota 2020 (2026-11-01)

## Exact primary source, not a guessed Shinjuku ZIP

The Japanese ministry's **Project-PLATEAU/SkylinesPLATEAU** repository explicitly includes an original CityGML sample ZIP, `SampleData/08234_hokota-shi_2020_citygml_4_op_sample_area.zip`. Its accompanying official [SampleData readme](https://github.com/Project-PLATEAU/SkylinesPLATEAU/blob/main/SampleData/readme.md) says it represents a **subset of the real 3D Hokota city model**, provides a test centre `36.152783, 140.520347`, Japanese local plane coordinate system **zone 9**, and enumerates mesh areas, with land-use gaps because of Git size limits. These are **publisher claims** requiring validation against original bytes; they do not prove full municipality coverage, a surveyed building footprint, or any particular insured risk.

The exact pin is:
- Repository: `Project-PLATEAU/SkylinesPLATEAU`, commit `1f58887e1aaf050ac824b7fec55235550d0db1a7` (2024-03-29).
- Path: `SampleData/08234_hokota-shi_2020_citygml_4_op_sample_area.zip`.
- Git tree blob SHA-1: `27be2d62ae68e3bae552c00f7635bbe47e871ea2`.
- Git tree original size: `40,347,627` bytes.
- Fixed HTTPS original transport, pinned to commit rather than mutable `main`: `https://raw.githubusercontent.com/Project-PLATEAU/SkylinesPLATEAU/1f58887e1aaf050ac824b7fec55235550d0db1a7/SampleData/08234_hokota-shi_2020_citygml_4_op_sample_area.zip`.
- License nuance: The public **software repository** declares Apache-2.0; this does **not** independently establish the municipality-owned CityGML data's individual license. MLIT's open PLATEAU data policy is documented separately in `docs/research/plateau-citygml-original-zip-preflight-20261101.md`. Before publication, derivative redistribution or CAT use, review the exact municipality's rights, source attribution, modification and Survey Act conditions. The test pipeline does not imply that review is complete.

**Hokota is not Shinjuku.** The ZIP inspector formerly stamped hard-coded Shinjuku `13104`/2024 even on arbitrary inputs; this change removes those false assertions entirely. The ZIP content's actual municipal identity/vintage is *not* independently verified by a filename.

## Bounded original source receipt execution

`.github/workflows/plateau-hokota-original-sample.yml` fetches **only** that public, pinned GitHub object on a temporary GitHub Actions runner, with HTTPS restrictions, 180-second request budget and 45,000,000-byte transfer limit; checks the exact 40,347,627-byte count; invokes `research_runners/plateau_hokota_official_sample_receipt_v0.py`; deletes the ZIP at the end; **never uploads any data artifact or commits original bytes**. It is triggered by its own PR paths or an explicit manual dispatch.

The Python runner:
1. Computes the Git binary **blob** identity including `blob {size}\0` header and compares with the pinned Git tree SHA-1. This only checks consistency with a public Git object, not cryptographic publisher signatures or independent cadastral validity.
2. Validates local ZIP structure and computes actual ZIP SHA-256 via the existing size/path/compression/security gate.
3. Counts building `udx/bldg/*.gml` members. Selects up to **three** small (at most 4 MiB uncompressed) members, sorted deterministically; reads each through Python's ZIP CRC-checked member interface and passes exact XML bytes to the previously tested CityGML envelope/height/LOD0 structural preflight. XML may fail structural screening; the source remains quarantined. If all candidate GML files are larger than 4 MiB, the output explicitly reports **zero GML samples examined**.
4. Prints a nonidentifying receipt containing only whole-file and chosen-small-member hashes, byte counts and structural pass/blocked flags. It never prints per-building IDs, coordinates, original member names, source GML text, full filenames or individual measurements.

The outcome is **observed original-source QA**, not data admission. The ZIP central-directory scan alone does not validate all member CRCs, municipality 08234 vintage, precise polygon topology, 3D source vertical datum, model completeness, licensability or loss-model use.

## Observed original-byte evidence (GitHub Actions, 2026-11-01)

This is a real public GitHub-source receipt, **not** a synthetic fixture or a downloaded asset committed to our repository. The [exact original-source Actions run](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41330508159/job/124919409502) fetched the pinned 40,347,627-byte official Hokota sample, verified the pinned Git blob SHA-1 above and independently calculated original ZIP SHA-256 **`d8e3423388b41a639e9f814cdfbff090bd5c0bb5a99083f97d143fdd6ff56151`**. The ZIP had **233 entries**, **9 building GML** members, **5** under the 4-MiB small-file inspection limit, and **3** deterministically sampled GML members; the other 6 building GML files were not XML-screened.

| Selected original GML (content SHA-256 prefix) | Byte count | Building elements | Measured-height fields | LOD0 footprint rings screened | Unresolved LOD0 cases | Outcome |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `b36a08bf5bb7` | 636,070 | 107 | 83 | 107 | 0 | Structural screen pass |
| `1ee3d4de8ccd` | 2,376,027 | 346 | 239 | 346 | 0 | Structural screen pass |
| `eb923f034182` | 3,244,963 | 474 | 373 | 399 | 75 | **Partial** (74 beyond explicit 400-polygon budget; one additional unresolved case) |

Across the three *distinct* sampled GML members, the results total **927 parsed building elements**, **695 present measured-height fields**, **852 screened LOD0 footprint rings**, and **75 unresolved LOD0 cases**. These counts are restricted to **three of nine building GML files in a deliberately limited regional subset**, not Hokota-wide building totals, unique across all other source releases, insured buildings, or valid footprints. The 400-polygon screening budget is unchanged: a large authentic file is reported **partial** with every overflowed polygon explicitly unresolved, not silently upgraded to a fully validated GML or discarded as corrupt. This diagnostic reveals the *limitation of our preflight policy*, rather than evidence of invalid original geometry.

The two earliest sample members passed their **limited XML/CRS/ring structure** screens; none have passed independent polygon topology, source completeness, vertical-datum, provenance beyond the Git pin, data-specific rights review, municipal registration or CAT model admission. Member reads exercised the ZIP CRC verification for these three chosen GML members **only**. The remaining archive entries' CRCs and all building-geometry comprehensiveness remain unverified. No original bytes or confidential assets were published or stored in Git.

## Independent scientific follow-up

First use the exact-source receipt to determine whether the historic sample can actually be screened with the modern CityGML validator. The sample is a different municipality/year from the frozen Shinjuku 2024 GraphQL metadata contract. Any CRS differences, legacy schema or geometry encoding differences must be reported rather than reinterpreted silently. An appropriate next independent scientific test is a bounded geometry/CRS verification against a separately sourced reference with clearly disjoint provenance and matching vintage. No provider-service API requests are authorized by the public GitHub sample workflow.
