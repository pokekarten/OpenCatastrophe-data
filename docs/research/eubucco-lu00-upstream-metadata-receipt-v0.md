<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EUBUCCO v0.2: Luxembourg original upstream-source workbook

**Research only.** This independent source-lineage check closes a different
gap from PR #919, which downloads the LU00 buildings themselves.

## Why this matters

The original EUBUCCO v0.2 LU00 Parquet profile identifies individual
`geometry_source` values such as `gov-*`, `osm` and `msft`. A
government-labelled feature does not establish **which government data
product/release** contributed it, what original licence and vintage applies,
or whether those footprints are independent of the newer ACT2023v2 Luxembourg
roof extents. Treating both products as independent building-ground-truth
without source metadata would inflate validation confidence.

Official EUBUCCO documentation identifies `input-datasets-metadata.xlsx`
as the source-dataset reference workbook (name, original owner, licence,
access date, original data access and integration details). The official v0.2
data portal provides its exact direct S3 download:

https://s3.eubucco.com/eubucco/v0.2/additional/input-datasets-metadata.xlsx

Official pages:
- https://eubucco.com/data/download/v0.2
- https://docs.eubucco.com/v0.2/data-format/metadata/
- https://docs.eubucco.com/v0.2/license/

## Implemented reproducible check

`research_runners/eubucco_lu_original_metadata_xlsx_v0.py` is an
offline read-only XLSX ZIP/XML parser using only Python's standard library.
It deliberately does **not** parse the dataset's individual buildings. It
checks the downloaded workbook's exact SHA-256, ZIP traversal / symlinks /
external link safety, compressed and expanded size budgets, worksheet and
shared-string structures and only prints **public source-metadata rows
mentioning Luxembourg or LU**.

```bash
python -m unittest tests.test_eubucco_lu_original_metadata_xlsx_v0 -v
python -m research_runners.eubucco_lu_original_metadata_xlsx_v0 \
  --original-xlsx /private/official-input-datasets-metadata.xlsx
```

The first original-file run **computes** a byte-identifying SHA-256. It
does not pretend that the first computed value is a prior independent
publisher checksum. Subsequent retrievals should use
`--expected-sha256` with that frozen value. A provider revision must
block or be explicitly reviewed, never silently become equivalent to the
previous workbook.

A dedicated, source-specific GitHub Action fetches just this small
provider-hosted metadata workbook into the temporary runner, checks
synthetic fixtures and logs only the relevant source-metadata summary.
No original XLSX, building geometry, individual IDs or insurance records
are committed, uploaded or placed in insurance Neon.

## Validation limits and next causal decision

The workbook may describe several Luxembourg upstream sources or none
in a simple country field; distinguish the actual original dataset name,
the government provenance label (including provider-specific `gov-*`
codes), retrieval date, licence and vintage. An original source older than
ACT2023v2 can be a useful temporal cross-check, but **may share cadastral
lineage**. Agreement cannot be counted as two independent observations
without an explicit upstream-source crosswalk.

This script has **no authority to admit** source files or CAT model inputs.
Neither a common building polygon nor its government label proves building
identity, insured replacement value, construction age or commercial
redistribution rights.
