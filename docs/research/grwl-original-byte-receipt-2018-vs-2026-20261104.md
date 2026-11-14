<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GRWL: original ZIP and member byte receipts, 2018 versus 2026

**Evidence date:** 2026-11-04 11:39:12 UTC.

**Observed in a completed successful trusted-main original byte workflow**, not inferred from provider-preview strings or synthetic fixtures:
- [GitHub run 41822336297](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41822336297)
- Workflow head `45f4e136d3b5600aad41dbe20b4146266e4dc843` on `main`
- Executable: `python -m research_runners.grwl_trusted_original_byte_proof_v0 --live`
- Receipt schema: `opencatastrophe-grwl-trusted-original-byte-evidence-v0`
- Original-member diff schema: `opencatastrophe-grwl-member-digest-difference-v0`
- Separate historical provider originals: [2018 record 1297434](https://zenodo.org/records/1297434) and [2026 record 18624542](https://zenodo.org/records/18624542).

Both exact provider files downloaded successfully into runner-local temporary storage, passed pinned provider byte-size and independently measured MD5, generated independent original ZIP SHA-256, passed original SHP/SHX/DBF/PRJ structural preflight, and passed streamed uncompressed member SHA-256/CRC checks. No source ZIP, geometry or DBF row bytes were committed, uploaded as artifacts, or placed in the public data register.

## Original archive receipts

| Identity | 2018 | 2026 |
| --- | --- | --- |
| File | `GRWL_summaryStats_V01.01.zip` | `GRWL_summaryStats_V01.02.zip` |
| Exact original bytes | 43,194,162 | 43,282,861 |
| Independently measured MD5 (matches original Zenodo) | `c37021e144fbff19ae3fc4e701d85d38` | `cac403c1a59bce7a74432085d3f5bd3a` |
| **Independently measured ZIP SHA-256** | `16830e5444d47d6ba74790613533b6a81b4036a15f3ad7a7066241da28f95306` | `78aa43a7104d24b1696e9b1547347eec13ba5d660aa990c1e7cea98e7ae70e4a` |

The original ZIPs differ in byte length by 88,699 bytes. The separate Zenodo records both display `metadata.version=V01.01`; source identification must use **record ID + actual filename + original ZIP SHA-256**, not a displayed product version alone.

## Independent uncompressed member evidence

All eight member filenames exist in both archives. Four member contents have **different SHA-256 digests** across versions:

| Member | 2018 uncompressed bytes | 2026 uncompressed bytes | SHA-256 equal? |
| --- | ---: | ---: | --- |
| `GRWL_summaryStats.shp` | 52,433,708 | 52,433,708 | **No** |
| `GRWL_summaryStats.dbf` | 6,143,596 | 6,143,596 | **No** |
| `GRWL_summaryStats.shx` | 336,716 | 336,716 | **No** |
| `GRWL_summaryStats.shp.xml` | 7,225 | 7,899 | **No** |
| `GRWL_summaryStats.prj` | 145 | 145 | **Yes** |
| `GRWL_summaryStats.cpg` | 5 | 5 | **Yes** |
| `GRWL_summaryStats.sbn` | 416,628 | 416,628 | **Yes** |
| `GRWL_summaryStats.sbx` | 18,676 | 18,676 | **Yes** |

Selected exact uncompressed member SHA-256 pairs, copied from completed hosted run logs:

| Changed core member | 2018 SHA-256 | 2026 SHA-256 |
| --- | --- | --- |
| `.shp` | `2757f3aaf753b01e859e610083b173a295f17a72034cd207efa41ef1fc830eba` | `121b1537050f26fff555478f608821980e188787a5f31c18ead2f24fd18dd7fa` |
| `.dbf` | `f6269cc06fc4562b8a5947a8233350e6666e1d3de07dc1b1501e2f705403a6b6` | `f5990abfb9f0f168847ad7d72ddbaa0b6f1e047d07a3c538e18feaf44acc6d43` |
| `.shx` | `e3b9b7eb8486ff2dc0c94fea6f2cfde608be30cdf38cb273af104428050d3d0e` | `378b08c50e5f879b4d095a86890991145980340a96b547feaec7059fdfd4588e` |

The `.shx` member length (336,716 bytes) corresponds to **42,077 index entries** per archive: (336,716 − 100-byte SHX header) / 8-byte index entry. The original ZIP preflight required the `.shx` index entry count to equal each matching `.dbf` header record count. Thus the two original releases have the **same header-validated number of indexed features (42,077)**, despite changed core member bytes. This is an archive-structural count, not an assertion that they are the same river features or have the same measured widths.

## Scientific status: byte changes confirmed, semantic changes not yet interpreted

**Confirmed:** original ZIP hashes, ZIP-member content differences in SHP/DBF/SHX/XML, identical PRJ/CPG/SBN/SBX member bytes, byte-length equality of core SHP/DBF/SHX, and header-validated index record count.

**Not established:** changes in specific river IDs, widths, coordinates, segment connectivity, channel classification, causes of differences, coordinate-wise deltas, uncertainty, or flood impacts. A different `.dbf` byte hash may reflect metadata/record-order/serialization changes rather than width-measurement changes. A different `.shp` byte hash may reflect ordering or geometry changes. Neither implication is assumed.

**Next causal experiment:** a controlled, bounded per-feature comparison of the two exact SHA-256-pinned original `.dbf` and `.shp` members in ephemeral trusted-main storage, with explicit record identity and field-level reports; distinguish reordering from changed attributes and true geometries. Use holdout and spatial-topology checks before any RiverATLAS join. Do not treat GRWL mean-discharge width as flood-stage geometry.

Rights: both Zenodo records report CC BY 4.0; original attribution and use-specific data/scientific assessment remain separate. This research receipt does not admit these data into models, synthetic insurer portfolios or production databases.

**Authority ceilings:** `any_real_width_change_verified=false`, `any_real_geometry_change_interpreted=false`, `flood_hazard_calibrated=false`, `source_data_admitted=false`, `production_database_modified=false`.
