<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# New Zealand property–building chain and Manitoba valuation-source preflight (2026-11-05)

**Scope:** original publisher metadata, exact crosswalk identifiers, source-selection and reproducibility requirements. This is **research only**, not external data acquisition, model-input admission, a production importer, an insurer portfolio or a valuation accuracy claim. No original records are included.

## Official New Zealand product chain

| Official LINZ product (publisher version inspected) | Key(s) & format | Reported stock, not a measured join |
| --- | --- | --- |
| [Public National District Valuation Roll subset, table 114085](https://data.linz.govt.nz/table/114085-nz-properties-national-district-valuation-roll/) | `unit_of_property_id`, valuation and classification columns; **non-spatial table** | Earlier detailed source page reported **287,243** rows (2026-07-23); category catalogue 2026-10-29 reports approximately **288K**. Public authorities are a **subset**, while the full nationwide roll is restricted to authorized organizations. |
| [NZ Property Boundaries, layer 122657](https://data.linz.govt.nz/layer/122657-nz-property-boundaries/) | `unit_of_property_id` where available, `source`, `source_id`, `geom`; NZGD2000 / EPSG:4167 | **2,718,135** polygons on inspected product page (last-updated 2026-10-22); property polygons combine rating units, titles and parcel fallback; **null unit IDs occur** for fallback types. |
| [Property-Building Reference, table 119620](https://data.linz.govt.nz/table/119620-nz-properties-property-building-reference/) | `unit_of_property_id`, `building_id`, `id`; non-spatial PDMF relationship | **5,029,306** reference rows (last updated 2026-09-24), not 5 million distinct buildings. May encode one-to-many and many-to-one relationships. |
| [NZ Building Outlines (current), layer 101290](https://data.linz.govt.nz/layer/101290-nz-building-outlines/) | `building_id`, roof polygon, `capture_source_from`, `capture_source_to`; EPSG:2193 | **3,236,141** footprints (last updated 2026-05-18); imagery spans different vintages, excludes some regions, includes garages/sheds >=10 m². |
| [NZ Building Outlines (All Sources), layer 101292](https://data.linz.govt.nz/layer/101292-nz-building-outlines-all-sources/) | `building_outline_id`, `building_id`, `begin_lifespan`, `end_lifespan`, capture dates | **6,634,223** multi-vintage outlines, not 6.6 million current buildings; a historical validation candidate, not a replacement for the current layer. |

**Join plan:** public DVR `unit_of_property_id` -> Property Boundaries `unit_of_property_id` for rateable-property position, separately -> Property-Building Reference `unit_of_property_id` -> current Building Outlines `building_id` for roof geometry. Build relationships are **not 1:1**. The boundary layer's title/parcel fallback means many spatial polygons have no `unit_of_property_id`. An attribute may refer to an assessed rating unit even when several physical roofs are linked; a tax roll amount must not be copied to every building. Use the building-outline chronology and the version/capture-date fields to prevent post-event look-ahead when evaluating past CAT events.

**Unresolved before even a pilot join:** select exactly the same or explicitly reconciled product releases; verify terms and user-rights for public versus restricted DVR; audit null-key, duplicate, many-to-many and unmatched rates; confirm property classification vs building use and CRS transformation; compare aerial-image age against modeled event date. No source rows downloaded or numerical join-rate asserted in this note. LINZ individual public pages show CC BY 4.0; each intended asset/reuse scope still needs project-specific rights and scientific review.

## Manitoba ROLL ENTRY

- Official [Canada portal listing](https://open.canada.ca/data/dataset/1cf8672a-2258-2917-0c8e-4cb8eb6401d9) identifies Government of Manitoba as publisher and **OpenMB Information and Data Use License**. The [official licence](https://www.gov.mb.ca/asset_library/en/legal/OpenMB-Information-Data-Use-Licence.pdf) permits commercial reuse and adaptation with attribution, but excludes personal information and third-party material not licensed by the government; the named licence is **not** a project admission decision.
- Its [ArcGIS FeatureServer](https://services.arcgis.com/mMUesHYPkXjaFGfS/arcgis/rest/services/ROLL_ENTRY/FeatureServer/0) describes `MG_ROLL_ENTRY_POLY` and includes summary fields `ASMT_ROLL`, `DWELLING_UNITS`, `TOTAL_VALUE`, `PROPERTY_ADDRESS` and property roll identifiers. The service spatial reference is EPSG:26914, distinct from WGS84 and New Zealand EPSG:2193/4167.
- `TOTAL_VALUE` represents **assessed tax value**, not current rebuild value, insured sum, TIV or market value. Tax-year and roll version are part of the row semantics. A roll entry or parcel is not one structure. Because `PROPERTY_ADDRESS` may reveal a civic address, no address values or individual source records should be copied into public Git; privacy must be reviewed before any row-level processing.
- **Execution boundary:** official metadata and stated output formats were examined; a successful live record-count or feature-body API query was **not established** in this investigation. Do not misreport a metadata check as a proven acquisition or ingest. Any future live probe should request count/field descriptors only, use bounded requests, pin response receipts, preserve attribution and stay outside Git.

## Next evidence gates

1. Use public LINZ **product-specific release IDs** and terms to fetch a *bounded, rights-cleared* test window outside Git, then run an aggregate-only ID/link QA. Report denominators, unmatched keys, duplicate and multi-geometry rates, type classifications and **source vintage differences**, not copied records.
2. For Manitoba, verify a bounded ArcGIS count-only query and schema with the original provider, then check geometry validity and temporal assessment-roll versions without processing the `PROPERTY_ADDRESS` field or any owner-related information.
3. Only after the above, use hazard overlays and **independently derived replacement-cost priors**. Insurer policy selection, insurance-to-value, deductible/limit and catastrophe vulnerability remain separate uncertainty layers.

**Status:** `non_admission`; commercial redistributability and scientific/model suitability for exact source/release/processing scope **not reviewed**. No insurer location, replacement value, synthetic portfolio or CAT loss has been inferred from these records.

## Executed original LINZ ArcGIS public aggregate canary (2026-11-05T07:48Z)

This adds real **original publisher-hosted live reads**, without an LDS API key or any row-level feature download. Read-only official Esri ArcGIS REST layers use `https://services.arcgis.com/xdsHIIxuCWByZiCB/ArcGIS/rest/services/` and `f=json`:

- Property polygons: [LINZ_NZ_Property_Boundaries/FeatureServer/0](https://services.arcgis.com/xdsHIIxuCWByZiCB/ArcGIS/rest/services/LINZ_NZ_Property_Boundaries/FeatureServer/0). The `returnCountOnly=true` endpoint returned **2,759,078** features, of which **2,305,863** had a nonnull `unit_of_property_id` and **453,215** had null `unit_of_property_id`. The partition conserves exactly.
- ArcGIS `groupByFieldsForStatistics=source`, `outStatistics=COUNT(OBJECTID)`, `returnGeometry=false`: **2,305,863 NZ Unit of Property**, **47,754 NZ Property Titles**, **66,606 NZ Primary Parcels**, **314,407 NZ Primary Parcels - Road**, and **24,448 NZ Primary Parcels - Hydro**. These sum to **2,759,078**; the four fallback strata sum to **453,215** missing rating-unit IDs. The ArcGIS service documents a display filter that hides road/hydro parcels in certain map views; a count-only all-source query is not necessarily the displayed map population.
- Building outlines: [LINZ_NZ_Building_Outlines/FeatureServer/0](https://services.arcgis.com/xdsHIIxuCWByZiCB/ArcGIS/rest/services/LINZ_NZ_Building_Outlines/FeatureServer/0). `returnCountOnly=true` returned **3,268,141** current footprints, all with nonnull `building_id` in this query (null count **0**). This provider ArcGIS service count and the LDS website's separate vintage count are not interchangeable.
- One explicitly fixed, independently reproducible **EPSG:2193 1-km-square envelope** `xmin=1749000,ymin=5427000,xmax=1750000,ymax=5428000`, query `geometryType=esriGeometryEnvelope`, `spatialRel=esriSpatialRelIntersects`: **2,966** property polygon intersections, **2,818** `NZ Unit of Property` polygon intersections and **546** building footprint intersections. The 2,966 and 546 populations are **not linked pairs or a join rate**. Intersections include geometries crossing the test envelope.
- Provider layer metadata explicitly declares spatial reference EPSG:2193, `unit_of_property_id` on the property layer and `building_id` plus aerial-image capture fields on the buildings layer. The property source category names were observed from original aggregate source records, not guessed.

The service names, query parameters, source category counts and query population are preserved here so an independent operator can reproduce the check. Results are **time-varying**: do not compare these directly to the 2026-10-22 LINZ webpage's 2,718,135 count without reconciling ArcGIS refresh date, display filter, inclusion of roads/hydro and source vintage. The official LINZ LDS WFS/API normally requires an API key even for many public products; a separate public ArcGIS replica is not a substitute for validating the exact version of `Property-Building Reference` table 119620 and the *partial public* National DVR.

### Executable bounded public-source checker

`scripts/nz_linz_public_arcgis_aggregate_canary_v0.py --live` makes only direct official HTTPS requests for layer metadata, count-only query results and aggregated source-category totals. It fails closed on changed provider fields/CRS, unknown source categories, inconsistent partitions, malformed/oversized responses or off-host redirects. It prints byte lengths/SHA-256 for each bounded original provider response and aggregate statistics; **no IDs, addresses, raw geometries, tax values or source rows are printed or saved**. The accompanying `tests/test_nz_linz_public_arcgis_aggregate_canary_v0.py` is synthetic-only and is run under the repository test discovery; no network requests run in CI.

**Critical unresolved boundary:** Neither an official source-key `unit_of_property_id → building_id` **data join** nor an actual valuation-to-roof allocation was executed. The original `Property-Building Reference` table is still required for a defensible physical-asset bridge, and the public DVR is a non-comprehensive council subset. The original ArcGIS same-box counts are merely metadata/data-access proofs, **not** a matched portfolio, model calibration, policy dataset, valuation estimate or source/model-admission decision.

## Additional structural join safeguards (2026-11-05)

The offline `nz_linz_property_building_join_preflight_v0.py` now differentiates original **NZ Unit of Property** rating-unit boundaries from title/parcel fallback boundaries, even if a fallback input unexpectedly carries a nonnull `unit_of_property_id`. The existing `valuation_units_with_boundary_in_sample` diagnostic is now rated-source-only; the report separately counts non-rated fallback rows with a key, duplicate rated boundaries and original reference buildings shared by multiple properties.

A deliberately conservative `conservative_one_to_one_join_candidates_in_sample` counter requires exactly one valuation row, one rated boundary, one unique linked building, one current-outline row and no other referenced property claiming that building. Such a count is **a structural key-reconciliation diagnostic**, not a validated actual valuation-to-roof join, a full nationwide completeness estimate, a verified building or a source/model-admitted exposure. It cannot resolve mismatched source releases, time-specific ownership, historic imagery, geographic coverage, tax-assessed value versus replacement cost, insurer selection or building TIV. Its entire input remains bounded local CSV keys and no source IDs or valuations appear in stdout.

Synthetic-only tests now challenge fallback parcels with an identifier, a many-properties-to-one-roof relationship, duplicate boundaries and duplicate roof rows. Exact-head CI must be rechecked after this change.

### Strict privacy projection for local CSV preflight

The join-key QA now accepts **exactly** the approved CSV columns for each input, in any order: valuations `unit_of_property_id`, rated/other boundaries `source,unit_of_property_id`, references `unit_of_property_id,building_id`, current outlines `building_id`. Inputs containing `PROPERTY_ADDRESS`, assessment `TOTAL_VALUE`, geometry or any other extra columns are rejected *before CSV data rows are parsed*. Incomplete rows, keys longer than 128 characters and files over 12 MB also fail closed; the existing 100,000-row absolute maximum remains. Rights-cleared, externally stripped key-only extracts are therefore a prerequisite, not merely a suggested CLI convention. This checker does not save raw keys, names, addresses or valuations, and outputs only aggregate counts.

Regression tests add synthetically invented forbidden fields, oversize and truncated CSV rows. This is a privacy/source-schema improvement, not evidence of a new authenticated LINZ source extract or of data-admission approval. Recheck exact-head CI before merge.
