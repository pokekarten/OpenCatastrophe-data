<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GRWL 2018 ↔ 2026: original ZIP member-byte diff (research only)

Reviewed: 2026-11-04. This is the next causal step after the merged original ZIP structural preflight in PR #1258. The original source ZIPs **were not fetched or analyzed** in this change. No actual river-width or geometry differences are claimed.

## Original records and unresolved question

The original Zenodo records publish different simplified ZIPs despite both records displaying version V01.01:

| Provider record | Simplified original ZIP | Provider-reported ZIP size | Provider MD5 |
| --- | --- | ---: | --- |
| [1297434 (2018)](https://zenodo.org/records/1297434) | `GRWL_summaryStats_V01.01.zip` | 43,194,162 bytes | `c37021e144fbff19ae3fc4e701d85d38` |
| [18624542 (2026)](https://zenodo.org/records/18624542) | `GRWL_summaryStats_V01.02.zip` | 43,282,861 bytes | `cac403c1a59bce7a74432085d3f5bd3a` |

The provider's ZIP preview pages for both versions show eight common member names: `.cpg`, `.dbf`, `.prj`, `.sbn`, `.sbx`, `.shp`, `.shp.xml`, `.shx`. Rounded displayed sizes are not sufficient to establish which exact member bytes differ. The 88,699-byte ZIP-size difference could involve compression, XML metadata, shape records, attributes, or multiple changes. We must not guess.

## New executable member-byte proof

`research_runners/grwl_original_member_digest_compare_v0.py` reuses the previously merged `inspect_original_zip` source gate, requiring exact provider file names, sizes, provider MD5 matches, source-ZIP SHA-256 and SHP/SHX/DBF/PRJ structure.

With both source files **lawfully downloaded and placed outside the public Git repository**, run:

```bash
python research_runners/grwl_original_member_digest_compare_v0.py \
  --2018-zip /private/data/GRWL_summaryStats_V01.01.zip \
  --2026-zip /private/data/GRWL_summaryStats_V01.02.zip \
  > /private/evidence/grwl_member_digest_diff.json
```

The script does not perform any network request or extract member payloads to disk. It re-hashes the original ZIP file descriptor to detect changes between structural preflight and analysis. It streams each bounded member through SHA-256 while enforcing decompressed length and ZIP CRC; the output contains only file names, byte counts, SHA-256 digests, and categorical booleans. No raw third-party geometry, DBF rows, maps, customer data or insured records appear in output.

**Interpretation is deliberately narrow.** If all *uncompressed* member hashes are equal, ZIP container bytes may still differ, but the tested member contents are identical. If the core `.shp/.shx/.dbf/.prj` members are unchanged, the shapefile core is byte-identical; modified `.shp.xml` or index helper files do not prove a changed river width. If `.shp` or `.dbf` differs, the tool only reports which member changed; it does not identify river features, quantify width changes, compare topology or assert model significance.

The changed/identical filename inventory is deterministically sorted; non-unique, traversing, unsupported or overexpanded members are rejected through the existing ZIP safety gate. All model, flood calibration, licensing-admission and production database booleans remain false even when an original-byte difference is found.

## Verification

Synthetic-only unit tests:

```bash
python -m unittest discover -s tests -p 'test_grwl_original_member_digest_compare_v0.py' -v
```

13 synthetic tests passed in ChatGPT Linux against a test-only equivalent of the existing bounded ZIP member safety gate; exact-repository GitHub CI must independently verify integration against the actual merged preflight module. Tests cover identical uncompressed data in differently compressed ZIPs, XML-only differences, SHP/DBF/SHX differences, CRC corruption, path traversal, missing PRJ, deterministic ordering and non-admission outputs.

**Not yet done:** actual source download, independent SHA-256 original ZIP receipts, member-level original SHA-256 comparison, GRWL record-by-record semantic comparison, width uncertainty assessment, spatial join to RiverATLAS, scientific license/redistribution approval, flood hazard computation, NextGen integration.

## Practical next action

Use an execution environment that can resolve Zenodo and can keep approximately 90 MB of original ZIP downloads plus private scratch space outside Git. Run the source ZIP gate and then the member digest comparator, retain only the JSON receipt in a restricted research workspace until source-use authorization is confirmed. If `.shp` or `.dbf` hashes differ, implement a bounded per-feature semantic comparator after pinning full file SHA-256 and verifying stable record identity; if the core member hashes match, document that the archive update does **not** change the core shapefile bytes and avoid needless river-conflation work.
