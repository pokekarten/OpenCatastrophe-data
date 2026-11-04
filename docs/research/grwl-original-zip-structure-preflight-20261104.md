<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GRWL original simplified ZIP versions: local offline structure proof

Reviewed 2026-11-04. This is an **original-archive preflight** supporting the upstream GRWL 2018/2026 metadata work merged from PR #1243. It does not establish that river reaches, width measurements, geometries or flood risk changed.

## Independent primary-source identities

Zenodo original records:
- 2018 https://zenodo.org/records/1297434 — `GRWL_summaryStats_V01.01.zip`, **43,194,162 bytes**, listed MD5 `c37021e144fbff19ae3fc4e701d85d38`.
- 2026 https://zenodo.org/records/18624542 — `GRWL_summaryStats_V01.02.zip`, **43,282,861 bytes**, listed MD5 `cac403c1a59bce7a74432085d3f5bd3a`.

The 2026 record retains the `metadata.version=V01.01` label despite shipping V01.02 for the summary ZIP. The file-size difference of 88,699 bytes and distinct provider MD5 values **do not** establish which geometry, DBF row values or attributes changed. The published full-vector and mask ZIP metadata remain identical across the two records.

## Exact-source verification operation

After a reviewed/authorized independent download of both published GRWL summary ZIPs to a **private directory outside this repository**:

```bash
python research_runners/grwl_original_zip_structure_preflight_v0.py \
  --2018-zip /private/data/GRWL_summaryStats_V01.01.zip \
  --2026-zip /private/data/GRWL_summaryStats_V01.02.zip \
  > /private/evidence/grwl_source_structure_receipt.json
```

The script runs **offline**: no network request, no ZIP extraction, no complete member decompression, no DBF attribute records or shapefile geometries read, and no production data access.

For each exact original ZIP it enforces:
- Frozen provider filename, source-listed byte length and **independently calculated original ZIP MD5**, while separately calculating a fresh **SHA-256 of the exact local ZIP**.
- Archive path/symlink/duplicate-entry rejection, caps on member count, claimed uncompressed size and expansion ratio. No ZIP members are extracted.
- One internally consistent `.shp/.shx/.dbf/.prj` set; compatible SHP/SHX shape header, geographic bounding box and SHX index count.
- DBF header schema including `width_mean` and `lakeflag`, basic DBF length validity, and a count that agrees with the SHX index.
- Geographic WGS84 projection declaration rather than projected WGS84/UTM units.

The structured JSON receipt reports original ZIP MD5/SHA-256, **header-declared** feature counts, field names, nominal bbox, and whether the two vintages have the same header counts, columns and bbox. It always explicitly marks row values and geometry changes as **unknown**. For now all scientific admission, actual spatial joining, risk modelling and production DB mutation remain false.

Synthetic-only negative tests:
```bash
python -m unittest discover -s tests -p 'test_grwl_original_zip_structure_preflight_v0.py' -v
```

22 tests passed in the isolated ChatGPT Linux environment when the script was prepared. Exact PR-head repository-wide GitHub CI results are a separate check, and **real GRWL ZIP content tests remain unexecuted**, because attempts to download original ZIPs from the available runtime did not succeed. The user's connected Desktop Commander Mac was offline at the time of this review.

## Scientific boundary and next step

A successful structural receipt would establish **actual, pinned source ZIP bytes and header metadata**, not actual scientific river-width comparability. It must be followed by (1) ZIP-member and record-level content comparison in a separately authorized private workspace, (2) key/geometry lineage analysis, (3) accurate reprojection and hydrographic one-to-many topology handling, and (4) holdout evaluation against independent real-world water observations. GRWL width at selected mean discharge is not flood-stage width, depth, discharge, return period, loss, or insured value.

No original dataset bytes, ZIPs, shapefiles, customer data or private file paths are stored in Git. The result is not authorized for OpenCatastrophe production or NextGen portfolio valuation without a later explicit use-specific evidence review.
