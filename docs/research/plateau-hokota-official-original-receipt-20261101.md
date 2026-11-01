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

## Independent scientific follow-up

First use the exact-source receipt to determine whether the historic sample can actually be screened with the modern CityGML validator. The sample is a different municipality/year from the frozen Shinjuku 2024 GraphQL metadata contract. Any CRS differences, legacy schema or geometry encoding differences must be reported rather than reinterpreted silently. An appropriate next independent scientific test is a bounded geometry/CRS verification against a separately sourced reference with clearly disjoint provenance and matching vintage. No provider-service API requests are authorized by the public GitHub sample workflow.
