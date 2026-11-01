<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EUBUCCO Luxembourg LU00 v0.2: first original Parquet receipt

**Date:** 2026-11-01. **Status:** experimental original-byte read; NOT an
admitted CAT model input, building exposure import or ownership/address join.

## Original source target and lineage

- Producer: EUBUCCO / TU Berlin and partners.
- Original v0.2 NUTS2 partition candidate (official documented path template):
  <https://s3.eubucco.com/eubucco/v0.2/buildings/parquet/nuts_id=LU00/LU00.parquet>.
- Documentation: <https://docs.eubucco.com/v0.2/data-access/cli/>,
  <https://docs.eubucco.com/v0.2/data-format/schema/>,
  <https://docs.eubucco.com/v0.2/license/>.
- Luxembourg NUTS2 partition: `LU00`, NUTS3 region: `LU000` under the
  provider's adapted 2016 geography. Do not silently join to later NUTS
  releases.
- EUBUCCO dataset licence is generally **ODbL v1.0**, with explicitly listed
  regional source exceptions (Abruzzo, Prague). Confirm Luxembourg provider
  source lineage and any upstream rights/ODbL obligations *before* any
  redistribution, combined source release or commercial model ingestion.
- Original footprint geometry is documented as **EPSG:3035 WKB**; EUBUCCO
  `geometry_source`, `geometry_source_id` and per-attribute source metadata
  must be preserved for any scientific independence claim.
- Luxembourg ACT2023v2 official `238189` roof-derived MultiPolygon features
  in **EPSG:2169** are a DIFFERENT source, geometry definition and observation
  period; `ACT` counts must not be substituted for EUBUCCO building counts.

## Actual next execution

The new `.github/workflows/eubucco-lu00-original-source-receipt.yml`
workflow requests **one exact** public Luxembourg Parquet partition over
HTTPS, with no wildcard/pagination, an 256 MiB source byte cap, request timeout
and read-only GitHub permissions. It runs previously merged 10 synthetic
Parquet tests under pinned PyArrow 20.0.0, then uses
`research_runners/eubucco_lu00_lineage_preflight_v0.py` (merged via #915)
to validate the source object and return aggregate counts only.

It should emit:
- Exact original file SHA-256 and file size; a first observed digest is
  **not** prior independent authenticity verification. Freeze it only if
  the source filename, original provider HTTPS URL and parsing all succeed.
- Original EUBUCCO LU00 count and NUTS3 region count, unique building ID check,
  `geometry_source` families (government-labelled, OSM, Microsoft or other)
  and attribute-source family counts; never original per-building values.
- Explicit `false` values for scientific independence from ACT2023v2,
  licence approval, valid building geometry or CAT model input admission.

**Fail-closed outcomes**: missing object/HTTP error, oversized file, wrong
Parquet header, incorrect geometry data type, duplicate IDs, unexpected
regional values or more than 2 million rows stop the experiment. No fallback
to a different release or a guessed NUTS code.

The original Parquet remains only on the temporary workflow runner and is
deleted by a shell trap. No raw source bytes, geometry, individual IDs or
insurer records are uploaded, merged into Git or written into the independent
`insurance-risk-core` Neon metadata registry.

## Measured original-byte receipt (GitHub Actions, 2026-11-01)

The **actual**, not synthetic, EUBUCCO v0.2 `LU00` public original
Parquet was successfully retrieved and analysed in
<https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41307603134>.

| Observed source property | Measured value |
| --- | ---: |
| Original exact Parquet bytes | **29,053,909** |
| Original Parquet SHA-256 | `d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c` |
| Parquet row groups | **19** |
| Verified distinct EUBUCCO `id` rows in LU000 | **186,171** |
| `geometry_source`: government-labelled, upstream not checked | **144,088** |
| `geometry_source`: OSM | **23,928** |
| `geometry_source`: Microsoft | **18,155** |
| Construction-year source: no provenance supplied | **186,097** |
| Construction-year source: OSM | **74** |
| Floors source: model-estimated | **181,134** |
| Floors source: OSM | **5,037** |
| Height source: government-labelled (not independent evidence) | **144,088** |
| Height source: model-estimated | **40,519** |
| Height source: Microsoft | **1,504** |
| Height source: OSM | **60** |
| Type source: model-estimated / OSM | **109,847 / 76,324** |
| Subtype source: model-estimated / OSM | **161,439 / 24,732** |

These numbers are **provenance field counts**, not proof that all values
are accurate, not direct counts of measured physical heights, not the
population of insured property, and not the count of missing Luxembourg
buildings. A source provenance cell marked `missing` is not a general
assertion about every related value. 144,088 records with government-
labelled geometry **may already originate from older ACT or other related
national sources**; independent source validation must not count their
spatial coincidence as two observations.

The newly observed SHA-256 is now a pre-existing, exact byte pin in the
GitHub workflow; subsequent retrieval must match. The initial observation
was tied to the documented original HTTPS source URL but **was not signed
by EUBUCCO**, and the next run verifies reproducibility only, not a
publisher-signed authenticity statement.

**Second exact-byte retrieval and measurable attribute coverage**
succeeded in [GitHub Actions run 41307901686](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41307901686).
It independently checked the **pre-existing** 29,053,909-byte source SHA-256
listed above. Original file and provider source identity are reproducible
across both retrievals. The script now distinguishes the **presence** of
actual attribute values from the provenance labels:

| Building attribute value field | Non-null / nonblank / finite | Null | Blank | Nonfinite |
| --- | ---: | ---: | ---: | ---: |
| `construction_year` | **74** | **186,097** | 0 | 0 |
| `height` | **186,171** | 0 | 0 | 0 |
| `floors` | **186,171** | 0 | 0 | 0 |
| `type` | **186,171** | 0 | 0 | 0 |
| `subtype` | **186,171** | 0 | 0 | 0 |

**Important distinction:** complete `height`, `floors`, `type` and
`subtype` fields reflect significant provider modelling and imputation.
The completeness of height and floor values does **not** demonstrate
measured completeness or physical accuracy. The extremely limited
construction-year availability is now established from the **actual
values**, not merely missing `construction_year_source` provenance.
This is a concrete reason to prioritise original documented construction
years and independently observed building material/floor data when
researching national registries; ACT rooftop footprint area, `zmin`
or 2023 observation date are NOT substitutes for construction year.

**Still not done:** country coverage adequacy, actual geometry CRS/axis
accuracy, polygon IoU, ACT2023v2 ↔ EUBUCCO identity crosswalk,
EUBUCCO Luxembourg original-cadastre metadata, attribute validity,
source-specific commercial right-to-use, and insurance loss admission.

## Next matching evidence gate, not yet completed

1. Independently confirm exact LU00 original Parquet checksum and actual
   producer metadata for Luxembourg source geometry. Establish whether the
   upstream source overlaps ACT2023v2 or shares official cadastre lineage.
2. Audit the unusual **EPSG:2169 axis order** (X = northing,
   Y = easting) using known ground control and actual geometry coordinates,
   not just the declared EPSG code.
3. Select same geographic area and validated survey vintages; only then
   compare bounded EUBUCCO 3035 footprints to ACT 2169 rooftop extents.
   Use stratified manual review and retain unresolved 1:n/n:1 splits.
4. Before any source-to-source attribute enrichment, require provenance
   checks, geometry-match acceptance criteria, explicit commercial rights
   review and scientific admission. Do not treat high IoU or coincident
   addresses as a valid insurer exposure ID.
