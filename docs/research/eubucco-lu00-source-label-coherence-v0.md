<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Real EUBUCCO LU00 source-label cross-attribute audit

**Date:** 2026-11-01. **Scientific role:** isolated research validation of source provenance; **not** CAT model input, building admission, licensed commercial or redistributable data.

## Why: a missing scientific distinction

The real-source `EUBUCCO v0.2 LU00` analysis from PR #919 proved one original Parquet file is accessible and parsable (186,171 records; original 29,053,909 bytes, SHA-256 below). The previous analysis counted marginal `geometry_source` and `*_source` families independently. It cannot tell whether a supposedly governmental height/type came from the *same label* as the government footprint or a different source, or whether an OSM/MSFT footprint uses estimated attributes. These distinctions are essential before rating two datasets as independent evidence in the Luxembourg ACT2023v2 comparison.

**Previously observed original file:** https://s3.eubucco.com/eubucco/v0.2/buildings/parquet/nuts_id=LU00/LU00.parquet

**Previous source receipt SHA-256:** `d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c`.

The receipt was first observed from the public HTTPS object and is not an independent publisher-signed hash. The new workflow repeats the retrieval and requires **exact byte equality** with that earlier observation. The source file is temporary, **not** committed, uploaded, or written to Neon.

## New bounded diagnostic

`research_runners/eubucco_lu00_source_coherence_v0.py` loads the already-downloaded original, limited to 256 MiB, 2 million rows and 10,000 row groups, and cross-tabulates:

- `geometry_source` class (government-labelled, OSM, Microsoft, other or missing) against `type_source`, `subtype_source`, `height_source`, `floors_source`, and `construction_year_source`;
- apparent **same literal source label** vs different label vs `estimated` vs `missing`, each count constrained to sum to the original record count;
- original source SHA, count, source partition and explicit scientific/non-admission flags.

A matching source label does **not** prove equal upstream asset or independent ground truth; different labels do **not** prove scientific independence. In particular two government-labelled building records might both originate from an ACT or common cadastral source. The source workbook `input-datasets-metadata.xlsx` listed in the EUBUCCO documentation must still be inspected to resolve original Luxembourg government data name, access date, original licence and source crosswalk.

Official docs: https://docs.eubucco.com/v0.2/data-format/metadata/ and https://docs.eubucco.com/v0.2/data-format/schema/ .

### Reproduction

```bash
python -m pip install pyarrow==20.0.0
python -m unittest tests.test_eubucco_lu00_source_coherence_v0 -v
python research_runners/eubucco_lu00_source_coherence_v0.py \
  --original /path/to/previously-acquired-LU00.parquet \
  --sha256 d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c
```

The dedicated GitHub workflow runs both synthetic cases and one narrowly bounded **re-download of the exact previously observed object**, then prints only aggregate diagnostic counts. Abort if the exact SHA changes; do not silently accept new data as the same version.

## Still missing for scientifically valid insured CAT exposure

- EUBUCCO Luxembourg government original source identity + rights + vintage and ACT source lineage relationship.
- Independent native ACT EPSG:2169 axis validation (separate PR #918) and exact EUBUCCO EPSG:3035 semantics.
- A stratified, manually checked one-to-one/split/merge geometry comparison. ACT 2023 rooftop extents and EUBUCCO ground footprints have different geometric definitions.
- Independent survey-based building age, repair/replacement value, occupancy, insurer coverage/insurance sums, vulnerability and hazard depth. None is inferred from the source-label coherence matrix.
