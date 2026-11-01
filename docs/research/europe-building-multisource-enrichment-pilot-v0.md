<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# European building enrichment: source search, crosswalk and acceptance pilot v0

**Date:** 2026-11-01  
**Status:** research design / no provider bytes acquired / no source admitted  
**Canonical discovery candidates:** `landscape/sources-europe-building-attribute-discovery.json`; pre-existing EU buildings, EUBUCCO, EFEHR and validation shards remain authoritative for their entries.

## Concrete modelling question

Starting from the existing `eubucco.buildings.v0.2` metadata-only source, how many *additional real building objects* and *verifiable missing attributes* can be recovered **with original record provenance**, as distinct from statistical guesses? We should not make a larger database merely by merging incompatible polygons.

Primary target properties: footprint polygon, original building ID, current demolition/construction status, ground elevation, building/roof height, above-ground floors, construction epoch, function/occupancy, roof type and roof equipment, wall structure/material, basement/floor elevation (where surveyed), estimated replacement value and uncertainty.

Existing EUBUCCO, DBSM R2025 (separate discovery PR #903), Overture, GHS-OBAT, national registers, WSF Evolution and current hazard data must not be re-registered as a new source to claim progress. In particular the repository already lists DLR WSF 2019, WSF Evolution 1985–2015 and WSF 3D.

## Use Search plugins as an evidence acquisition funnel

1. **Attribute-led searches in local provider language**: for height query `nuages de points LiDAR HD classe bâtiment`, `swissSURFACE3D`, `3D Messdaten NRW`; for walls/roofs `ehitisregister välisseina materjal katuse tüüp`, `Attestato Prestazione Energetica CENED edificio`; for changes `certificazione energetica catasto numero piano`, `building permit demolition open data`.
2. **Primary-provider source verification**: check original data catalogue/service documentation, publication and revision date, available machine files, geodetic CRS, entity granularity, and original rights. Search result summaries alone do not authorise downloads or promotion.
3. **Cross-source novelty**: search current GitHub `landscape/sources*.json`, open PRs and live insurance Neon registry for *both exact product and underlying source family*. Preserve version as one candidate or explicit separate rights component (as with GBA).
4. **Follow a join-chain, not just discover titles**: search primary schema docs for `building_id / RNB / EHR_code / EGID / BAG pand / cadastral reference / UPRN`; verify whether IDs relate to a **building**, an **address**, a **dwelling**, a **parcel**, or a **certificate**.
5. **Target independent validation**: locate original airborne LiDAR or authoritative cadastral polygons and temporal snapshots before adopting a second AI-estimated height/building footprint. Catalog shared upstream sources so agreement from two downstream models is not mistaken for independent corroboration.
6. **Prioritise by expected incremental lift**: sample missingness and conflicting values *before bulk import*. Freeze exact source release/file, terms and scope, and only then permit a bounded byte-level acquisition under source admission.

A search plugin is a **discovery and documentation tool**. It does not establish that an item exists in a source file, that a join is valid, or that legal redistribution is allowed.

## Pilot lanes (bounded; no personal/customer policy data)

| Lane | Candidate public references | Test | Expected measurable gain |
| --- | --- | --- | --- |
| Estonia building identity and wall/roof features | EHR public API + TalTech 1,868 labelled Soviet-era apartment buildings, plus existing EUBUCCO | Match registry building code where shared; then audited polygon joins against EUBUCCO; distinguish housing block from apartment records | Verified material/age/floor-field fill rates, confusion matrix for existing EUBUCCO use/height |
| France 3D reference + certificates | IGN LiDAR HD 1-km² tile + existing RNB/BD TOPO/BDNB/EUBUCCO + BAN addresses | Use official building IDs where documented, otherwise polygon IoU/unique proximity; sample points over roof and ground LiDAR classes | Independent roof/eave height differences, building geometry and missing-structure alerts |
| Europe geometry comparison | EUBUCCO + DBSM R2025 + 3D-GloBFP v1 + GBA ODbL polygon subset | Crosswalk in local projected CRS at a version-pinned NUTS2; investigate shared OSM/Microsoft origin and split/merge topology | Count true unmatched buildings, area/centroid shift and ML height agreement (not independent truth) |
| Italy/Spain EPC pilot | Lombardy CENED+2.0 / Madrid certificates + actual cadastral mapping | Distinguish dwelling/certificate from building; require strong validated ID or geographically unique one-to-many linkage | Fill measured certified attributes *for certificate coverage only*, quantify selection bias |
| Germany PV equipment | MaStR public installation extract vs building/region data | Use only permitted public location precision. <=30 kWp installations have redacted location fields; aggregate otherwise | Regional equipment class/penetration priors, **not** installation-to-home disaggregation |
| Pan-Europe crosswalk contract | GeoE3 2D OGC API metadata and provider-specific source collections | Compare country collection schema, stable identifiers, CRS, pagination, update date and service restrictions | Repeatable source discovery + safe bounded metadata probe |
| Heat/floor-area consistency | Hotmaps 100m heat / gross-floor reference (2015) vs building census and modeled floors | Aggregate predictions to the SAME grid/time, flag age/context bias | Independent-ish urban floor area and heating demand *aggregate challenge* |

**Starting pilot recommendation:** Estonia EHR/TalTech sample for structural attribute evidence + one French LiDAR HD tile for a direct physical height check. Luxembourg CC0 2D polygon pilot from previously catalogued sources remains a good *geometry-only* control. Do not attempt a full pan-European or national LiDAR ingestion at this stage.

## Canonical *prospective* records (design only; do not create tables without migration review)

- `building_observation`: `building_ref`, `attribute_name`, `value`, `unit`, `source_id`, `upstream_source_family`, `provider_record_id`, `asset_sha256`, `release`, `observed_at`, `valid_from`, `valid_to`, `entity_granularity`, `observation_kind` (`measured|official_record|modelled|statistical_estimate`), `source_rights_state`, `confidence`.
- `building_crosswalk`: `left_id`, `right_id`, `id_type`, `match_method`, `match_score`, `geometry_iou`, `centroid_distance_m`, `version_left`, `version_right`, `review_state`, `cardinality` (`one_to_one|one_to_many|many_to_one|unknown`).
- `building_fused_attribute`: derived *candidate*, with `source_observation_ids[]`, `rule_version`, `uncertainty_interval`, `conflict_reason`, `final_status`; retain null for unresolved, restricted or unobserved.

These names are **proposed contracts**, not existing deployed Neon schema or completed imports.

## Matching logic

1. Normalize polygons into **a documented local metric CRS** (EUBUCCO polygons EPSG:3035; GBA source instructs EPSG:3857 regardless of some conflicting metadata; LiDAR vertical datum separate from horizontal CRS). Reject invalid, duplicate and empty geometries with reason codes; do not silently repair originals.
2. Prefer **documented original building-to-building IDs** and official crosswalks (e.g. EHR registration code, RNB and BD TOPO mapping, BAG and 3DBAG IDs). A shared certificate/address/parcel identifier is *not* guaranteed building identity.
3. Without stable IDs use a *candidate search* on bounding boxes / R-tree, then compute polygon intersection-over-union, overlap on each polygon, centroid distance in metres, area ratio and temporal compatibility. Retain plausible `one_to_many` and `many_to_one` building splits; do not greedily force one match.
4. Threshold values **are to be calibrated**, not arbitrarily fixed. Create a hand-adjudicated sample of matching/nonmatching buildings across dense cities, rural sites, rowhouses, historic cores, industrial compounds and cadastral vintages; report precision/recall and unresolved rate.
5. For height, compare actual ground-normalized roof LiDAR statistics and provider's 3D model definition; **roof altitude ≠ building height**. Require acquisition date, vertical datum and building spatial overlap. Never use a modeled height as a measured observation.
6. For construction year, resolve `year_of_construction` vs `permit_year` vs `renovation_year` vs `survey_year` vs `settlement_pixel_first_detection`; forbid collapsing them into one exact year.
7. Preserve *multiple source observations* in conflict; use source- and field-specific quality ranks rather than choosing whichever value is non-null/latest. Never replace an official observed material with a modelled guess without a formal rule and adverse-evidence review.
8. Log data-processing lineage so EUBUCCO/DBSM/GBA/Overture shared footprints cannot be counted as independent supporting votes; keep explicit model-vs-measurement distinctions.

## Pilot acceptance metrics

Report original **counts** and denominators, not only percentage lifts, by country, urban/rural, source and building class:

- Existing and newly verified unique buildings, missing footprint rates and false-positive/duplicate rates.
- Unique high-confidence matches, unresolved candidate matches, split/merge groups, and manually reviewed ambiguous examples.
- Attribute-specific observed **before/after** nonnull rate, separated by `measured`, `official_record`, `modelled`, `statistical_estimate`; do not inflate high-quality completeness by mixing imputed values.
- Height MAE, median absolute error and stratified residual bias **only against legitimately independent LiDAR holdout**, with building-class/age and observation-date controls.
- Geometry IoU distribution and commission/omission against official cadastre; differences in segmentation semantics explained.
- Rights gates per file, checksum, license/attribution, allowed commercial use, upload-back/redistribution decision, and provider byte count.
- Explicit source/attribute-specific temporal validity, coverage, model uncertainty and sampling bias.

For a reliable CAT model, the relevant success metric is not raw number of rows. It is the improvement in **verified exposure**, with usable construction/roof/floor attributes and traceable uncertainty that can correctly map into vulnerability functions.

## Scientific, commercial and operational blockers

- GBA.LoD1/GBA.Height and GBA.Polygon carry CC BY-NC rights; keep separately blocked. GBA.ODbLPolygon has attribution/ODbL requirements and shared-footprint lineage. Provider viewer explicitly forbids bulk automation.
- TalTech expert-validated subset is strongly sample-selected; its 1,868 apartment blocks are not representative of all Estonian buildings. The register's public data may include sensitive address/premise fields; do not process personal identifiers.
- MaStR intentionally suppresses exact location of <=30kWp solar units; no attempts to reverse geolocate redacted homes.
- For individual LiDAR tiles only, use permitted file-level downloads after scientific and legal checks; a 1km² French tile may be 0.5–2GB, too large for Neon registry storage. Keep bytes in authorised separate object storage.
- EPC certificates commonly describe a dwelling, not a whole building, and often encode renovation/certification rather than original construction.
- A research page, publicly accessible PDF or service API is not proof of open bulk rights, scientific admissibility, commercial rights or insurance policy exposure.
