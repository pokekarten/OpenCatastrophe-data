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

A matching source label does **not** prove equal upstream asset or independent ground truth; different labels do **not** prove scientific independence. In particular two government-labelled building records might both originate from an ACT or common cadastral source. The official `input-datasets-metadata.xlsx` has now been inspected independently in merged #920: source `gov-luxembourg` points to ACT's **2013 Bâtiments 3D LoD1** dataset, CC0 (catalogue label), EPSG:2169. This is an older version of the same Luxembourg governmental source family as the separate **ACT2023v2** rooftop product, not source-independent validation. See the distinct scientific evidence guard in PR #923. Exact original per-feature reuse, geometry methodology, rights and survey-date equivalence are not proven.

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


## Verified original-file run (2026-11-01)

Actual source-only GitHub Actions run: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41308236889 . The temporary original Luxembourg LU00 Parquet was retrieved a second time over HTTPS, exactly **29,053,909 bytes** and exactly the earlier SHA-256
`d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c`. The specialized synthetic tests and original-file cross-tab both passed. There are **186,171** unique decoded source IDs in the LU000 partition.

Source-label relations in the exact original, one mutually exclusive category per attribute per building:

| Attribute source column | Same literal label as geometry | Different label (not proven independent) | Estimated | Missing | Row sum |
| --- | ---: | ---: | ---: | ---: | ---: |
| height_source | 145,652 | 0 | 40,519 | 0 | 186,171 |
| floors_source | 639 | 4,398 | 181,134 | 0 | 186,171 |
| type_source | 9,333 | 66,991 | 109,847 | 0 | 186,171 |
| subtype_source | 5,450 | 19,282 | 161,439 | 0 | 186,171 |
| construction_year_source | 20 | 54 | 0 | 186,097 | 186,171 |

The source geometry-family margins were **144,088 government-labelled, 23,928 OSM and 18,155 Microsoft**. Every attribute row adds up to exactly 186,171; these are **provenance-label counts, not verified non-null values, surveyed heights, usable replacement values or new independent buildings**.

One important cross-tab detail: all **144,088** government-labelled geometries also use a government-labelled **height** source within the original LU00 file. This is not evidence that the height comes from a different measured dataset or that ACT2023v2 independently corroborates it. The original source workbook, metadata version, height datum and ACT-vs-EUBUCCO lineage are still needed.

**No individual building records, coordinates, source geometries, insurance sums or raw provider files** were published. Source rights and commercial-use suitability remain unreviewed, and `model_input_admitted=false`.

## Original source identity update after merged #920

The original EUBUCCO v0.2 source metadata (official provider workbook at https://s3.eubucco.com/eubucco/v0.2/additional/input-datasets-metadata.xlsx, SHA-256 `c505cdaa04a296a057f046ccc95c5cfdff277f6fb847f8b725fd85007cff2e0e`) identifies `gov-luxembourg` as **Administration du cadastre et de la topographie / Bâtiments 3D (LoD1), 2013**, catalogued CC0-1.0, EPSG:2169. The **2023** ACT2023v2 data are rooftop polygons; same producer does not imply that any specific two footprints are equal. Cross-label counts therefore must not be marketed as independent validation or as a same-year change detection result without source-version and manual geometry checks. Distinct PR #923 owns the canonical source-linkage rule; this document records only the consequence for the current cross-tab. Licence approval remains separate.
