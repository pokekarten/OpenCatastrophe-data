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
