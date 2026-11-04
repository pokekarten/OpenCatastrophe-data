<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-cadastral-land-register-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-cadastral-land-register-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission discovery of official cadastral parcel, land-register geometry and public property-sale sources for synthetic CAT exposures, with strict field-level property title and personal-data restrictions.

**Entries:** 13

## NRW INSPIRE ALKIS cadastral parcels WFS

**Candidate ID:** `de.nrw.inspire-alkis-parcels.2026`  
**Provider:** Geobasis NRW  
**Categories:** `cadastral_parcels`, `parcel_geometry`, `land_use_context`, `germany`  
**Spatial scope:** North Rhine-Westphalia, Germany  
**Temporal scope:** Geoportal metadata records 2026-09-01; GovData current listing cites 2026-10-01. Actual mutable WFS vintage unresolved pending original data receipt.  
**Resolution / granularity:** INSPIRE polygon geometry for parcels, cadastral units and districts via WFS; EPSG:25832 and EPSG:4258 supported  
**Potential roles:** `parcel_building_geometry_join`, `spatial_hazard_overlay`, `urban_property_exposure_validation`  
**Access hint:** `public_wfs_dl_de_zero_2_0_catalogue_provenance_and_bounded_probes`  
**Authoritative source:** <https://www.geoportal.de/info/6ee0316c-fff3-4c04-89c1-3aa2b453f95a>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official listing states free DL-DE-Zero 2.0 terms, no access restriction and maximum 100000 objects per response; choose bounded spatial query or recommended stored dataset query. Parcel shape is not a building footprint, ownership record, dwelling count or insured value. Preserve ALKIS version, CRS and compound/split parcel identities. Original provider GetCapabilities URL probed twice on 2026-11-04 (with and without VERSION=2.0.0); both returned HTTP 500 OGC Proxy Internal Server Error through the research fetch path. Do not claim usable original feature bytes or a working download until independent retry/alternate official access succeeds. Source vintage differs between Geoportal (Sep) and GovData (Oct).

## NRW Grundsteuerdaten Flurstuecke 2026 CSV

**Candidate ID:** `de.nrw.grundsteuer-flurstuecke.2026`  
**Provider:** Finanzverwaltung Nordrhein-Westfalen / Open.NRW  
**Categories:** `cadastral_parcels`, `land_use_context`, `tax_assessment`, `germany`  
**Spatial scope:** North Rhine-Westphalia, Germany  
**Temporal scope:** 2022, 2023 and 2026 tax-year catalogue versions; 2026 resource metadata updated 2026-10-28  
**Resolution / granularity:** Land-parcel tax context CSV with parcel ID, area and land use; 2023 format notes circa nine million parcels; includes restricted Grundbuchblattnummer field  
**Potential roles:** `land_area_exposure_priors`, `parcel_alkis_id_crosswalk`, `tax_landuse_context`  
**Access hint:** `mixed_field_terms_strip_restricted_grundbuchblattnummer_before_ingestion`  
**Authoritative source:** <https://data.gov.de/suche/daten/grundsteuerdaten-nrw-flurstucke06c57>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** CRITICAL FIELD-LEVEL EXCEPTION: NRW finance administration says Grundbuchblattnummer (title-register sheet identifier) may be used exclusively for Grundsteuererhebung, despite broad DL-DE-Zero rights for the downloadable CSV. Reject/drop this field at source-admission boundary for CAT purposes; do not persist it to public analytics or insurer models. Verify whether other fields have privacy/licence limits and snapshot individual year before any access. No owner or policy inference.

## Luxembourg official Plan cadastral numerise PCN

**Candidate ID:** `lu.act.pcn-cadastral-parcels-buildings.2026`  
**Provider:** Administration du cadastre et de la topographie (ACT)  
**Categories:** `cadastral_parcels`, `building_geometry`, `parcel_ids`, `luxembourg`  
**Spatial scope:** Grand Duchy of Luxembourg  
**Temporal scope:** Official resource updated 2026-11-02; immutable resource permalink and MD5 listed  
**Resolution / granularity:** Cadastral parcels, buildings, topographic objects and toponyms; circa 180.6 MB SHP ZIP and circa 612 MB GeoJSON at listed vintage  
**Potential roles:** `parcel_building_overlay`, `luxembourg_building_crosswalk`, `official_parcel_geometry_holdout`  
**Access hint:** `cc_by_4_0_catalogue_original_bytes_hash_and_granularity_review`  
**Authoritative source:** <https://data.public.lu/en/datasets/plan-cadastral-numerise-pcn/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher declares CC BY 4.0, but exact original asset/version, CRS, geometry accuracy and attribution must be reviewed before admission. Distinct from ACT BD-Adresses and Geoportail INSPIRE CP derivative: INSPIRE snapshots may lag source PCN and historic parcels have heterogeneous accuracy. Cadastral geometry neither establishes owners nor insured properties.

## France Cadastre Etalab parcel and building vectors

**Candidate ID:** `fr.etalab.cadastre-parcels-buildings.2026`  
**Provider:** DINUM / Etalab from DGFiP PCI cadastral data  
**Categories:** `cadastral_parcels`, `building_geometry`, `parcel_ids`, `france`  
**Spatial scope:** France including Strasbourg cadastral lineage  
**Temporal scope:** October 2026 publication with September 2026 PCI source vintage  
**Resolution / granularity:** Country/department/municipality GeoJSON and Shapefile parcels, buildings and other administrative parcel layers  
**Potential roles:** `parcel_rnb_building_crosswalk`, `cadastral_footprint_validation`, `dvfplus_spatial_join`  
**Access hint:** `open_vector_derivative_exact_original_licence_and_shared_lineage_review`  
**Authoritative source:** <https://cadastre.data.gouv.fr/datasets/cadastre-etalab>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Derived from PCI and Strasbourg source, not an independent ground truth or new building survey. ETALAB polygons are assembled without topological repair. France open cadastral maps exclude ownership/property files; any real-estate transaction join should respect event-to-parcel multiplicity and spatial/temporal vintage. Verify original licence and downstream anti-reidentification rules.

## France DVF+ open-data geolocated property transactions 2026.2

**Candidate ID:** `fr.cerema.dvfplus-open-transactions.2026`  
**Provider:** Cerema / DGFiP / DGALN  
**Categories:** `real_estate_transactions`, `valuation_proxy`, `cadastral_parcels`, `france`  
**Spatial scope:** France, with exclusions and vintage-specific coverage  
**Temporal scope:** 2026.2 published 2026-10-15, published transaction coverage 2014-01-01 to 2026-06-30  
**Resolution / granularity:** Geolocated real estate transactions in PostgreSQL/PostGIS, GeoPackage, CSV and GeoParquet; parcel-derived geolocation  
**Potential roles:** `regional_sale_price_prior`, `residential_market_value_challenge`, `parcel_sale_temporal_crosswalk`  
**Access hint:** `open_dvfplus_with_express_no_reidentification_and_no_indexing_limits`  
**Authoritative source:** <https://datafoncier.cerema.fr/actualites/la-nouvelle-version-dvf-open-data-20262-disponible>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Sale consideration is NOT building reinstatement cost, sum insured or land-free insured TIV. DVF+ geolocation is derived from PCI so is not an independent cadastral geometry validation. DGFiP anti-reidentification and search-indexing restrictions apply even where files are openly downloadable; aggregation and privacy review required; newest quarters incomplete.

## HM Land Registry INSPIRE Index Polygons for freehold titles

**Candidate ID:** `uk.hmlr.inspire-freehold-polygons.2026`  
**Provider:** HM Land Registry  
**Categories:** `cadastral_titles`, `freehold_polygons`, `land_registry`, `england_wales`  
**Spatial scope:** England and Wales, registered freehold only  
**Temporal scope:** Monthly publication; 2026-11-01 release available by local authority  
**Resolution / granularity:** Indicative polygon extents in GML, unique INSPIRE ID per polygon, often many polygons per legal title  
**Potential roles:** `title_geometry_reference`, `flood_overlay_property_matching`, `registered_freehold_exposure_proxy`  
**Access hint:** `uk_ogl_conditions_with_hmlr_and_os_attribution_exact_terms_review`  
**Authoritative source:** <https://use-land-property-data.service.gov.uk/datasets/inspire>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Freehold index polygons are not precise legal boundaries, all buildings, nor leasehold inventory. Multiple polygons per title, duplicated area authority boundaries and unregistered land must be handled. OGL attribution and separate OS geometry attribution required; terms not independently approved in CAT.

## HM Land Registry Price Paid Data residential sales

**Candidate ID:** `uk.hmlr.price-paid-data.2026`  
**Provider:** HM Land Registry  
**Categories:** `real_estate_transactions`, `valuation_proxy`, `england_wales`  
**Spatial scope:** England and Wales  
**Temporal scope:** Monthly publication; September 2026 first release updated 2026-10-28  
**Resolution / granularity:** Transaction unique IDs, reported sale prices, property type, dates and address components for eligible sales  
**Potential roles:** `regional_sales_price_prior`, `transaction_join_via_tuid`, `residential_type_distribution_proxy`  
**Access hint:** `uk_ogl_with_third_party_address_rights_review`  
**Authoritative source:** <https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Price Paid Data covers registered eligible value sales, not a census of all dwellings or current valuations. Ordnance Survey and Royal Mail PAF-derived address data may carry separate rights. Transactions cannot be equated to building reinstatement cost, sum insured or insurer policy locations; deduplicate revision and lag.

## HM Land Registry Transaction UID to INSPIRE ID lookup

**Candidate ID:** `uk.hmlr.tuid-inspireid-lookup.2026`  
**Provider:** HM Land Registry  
**Categories:** `parcel_transaction_crosswalk`, `freehold_title_ids`, `england_wales`  
**Spatial scope:** England and Wales, matched freehold sales only  
**Temporal scope:** New dataset launched 2026-08-28; latest page updated 2026-10-28  
**Resolution / granularity:** CSV links Price Paid transaction UID to unique INSPIRE polygon IDs, with possible one-to-many sale/polygon relations  
**Potential roles:** `transaction_to_freehold_polygon_join`, `value_proxy_spatial_crosswalk`, `linkage_coverage_audit`  
**Access hint:** `uk_ogl_related_but_separate_lookup_licence_and_exact_month_review`  
**Authoritative source:** <https://www.gov.uk/government/statistical-data-sets/transaction-unique-identifier-and-inspire-id-look-up-table-dataset>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** CRITICAL: technical specification states lookup is NOT back-dated and covers only new price-paid records with an available freehold INSPIRE polygon. Leasehold sales absent, some properties have multiple IDs; verify lookup-specific terms independently instead of inheriting Price Paid OGL. This is the strongest UK parcel-to-price join but suffers coverage and temporal selection bias.

## Dutch Kadaster BRK Kadastrale Kaart parcel OGC API

**Candidate ID:** `nl.kadaster.brk-kadastrale-kaart-perceel.2026`  
**Provider:** Kadaster / PDOK  
**Categories:** `cadastral_parcels`, `parcel_geometry`, `national_registry`, `netherlands`  
**Spatial scope:** The Netherlands  
**Temporal scope:** Live API catalogue updated 2026-11-04; mutable original geometry  
**Resolution / granularity:** OGC API Features 'perceel' provides parcel polygons, identifiers and per-feature GeoJSON or JSON-FG; nationwide spatial bounds  
**Potential roles:** `bag_building_to_parcel_join`, `parcel_geometry_hazard_overlay`, `property_exposure_spatial_validation`  
**Access hint:** `public_ogc_api_rights_rate_and_original_feature_test_required`  
**Authoritative source:** <https://api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1/collections/perceel?f=html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Not the existing BAG building register candidate: BRK Perceel is a distinct cadastral parcel identity layer. PDOK descriptions do not imply owner names, replacement value or insured coverage. Pin access date and exact feature geometry, avoid treating one parcel as one BAG pand/verblijfsobject. Bounded original OGC API test on 2026-11-04: GET collections/perceel/items?f=json&amp;limit=1 returned HTTP 200 application/geo+json with exactly one MultiPolygon feature, parcel identifier, municipality, area and validity metadata. Feature bytes and any person-level fields were not committed. This establishes one machine-readable response, not field rights/admission or BAG crosswalk quality.

## Geneva SITG CAD_PARCELLE_MENSU cadastral polygons and EGRID

**Candidate ID:** `ch.geneva.sitg-cad-parcelle-mensu.egrid.2026`  
**Provider:** SITG / Canton de Geneve  
**Categories:** `cadastral_parcels`, `parcel_ids`, `land_registry_crosswalk`, `switzerland`  
**Spatial scope:** Canton of Geneva, Switzerland  
**Temporal scope:** Current published ArcGIS feature service; original feature date varies  
**Resolution / granularity:** ArcGIS polygon features, Swiss EGRID parcel ID, geometry area and mutation/source attributes in EPSG:2056  
**Potential roles:** `parcel_stable_egrid_crosswalk`, `building_geometry_relation`, `swiss_hazard_exposure_overlay`  
**Access hint:** `public_service_metadata_queryable_license_and_field_reuse_not_reviewed`  
**Authoritative source:** <https://vector.sitg.ge.ch/arcgis/rest/services/CAD_PARCELLE_MENSU/FeatureServer/0>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Service supports query/GeoJSON and EGRID identifiers but is NOT a public owner/land-registry contents dump. Confirm SITG data licence, terms and non-sensitive permitted fields before actual downloads. Separate land/parcel from building/ownership identity; data may be historic or topologically split.

## Spain Catastro public cartography and non-protected alphanumeric data

**Candidate ID:** `es.catastro.nonprotected-parcels-attributes.2026`  
**Provider:** Direccion General del Catastro  
**Categories:** `cadastral_parcels`, `cadastral_attributes`, `property_use`, `spain`  
**Spatial scope:** Spain under national Catastro jurisdiction; region-specific exceptions must be checked  
**Temporal scope:** Rolling online cadastral services and provincial download vintages  
**Resolution / granularity:** Vector cadastral parcels and non-protected cadastral alphanumeric data via downloads and WMS/INSPIRE web services  
**Potential roles:** `parcel_building_unit_crosswalk`, `use_and_area_exposure_enrichment`, `cadastral_hazard_overlay`  
**Access hint:** `public_nonprotected_fields_only_protected_owner_and_cadastral_values_blocked`  
**Authoritative source:** <https://www.catastro.hacienda.gob.es/es-ES/acceso_infocat.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct from already catalogued Spanish INSPIRE Buildings. Do not use protected owner/co-owner names or protected cadastral values from authenticated services; provider explicitly gates these to authorised users. No individual insurance cover or replacement value; exact national and local terms, attribute cardinality and approved raw fields require review.

## HM Land Registry Price Paid transaction UID to UPRN lookup

**Candidate ID:** `uk.hmlr.transaction-uid-uprn-lookup.2026`  
**Provider:** HM Land Registry / Ordnance Survey  
**Categories:** `transaction_address_crosswalk`, `uprn_property_reference`, `england_wales`  
**Spatial scope:** England and Wales, addressable registered sale properties only  
**Temporal scope:** Published 2026-08-28 and updated monthly; September 2026 first releases, without backdating  
**Resolution / granularity:** Two-column CSV with Price Paid transaction unique identifier and UPRN (addressable-property reference, not cadastral polygon or building ID); one-to-many per sale possible  
**Potential roles:** `price_paid_to_addressable_unit_bridge`, `uk_building_vs_dwelling_crosswalk_research`, `freehold_leasehold_match_coverage_challenge`  
**Access hint:** `uk_ogl_hmlr_plus_ordnance_survey_attribution_addressbase_paf_source_terms_review`  
**Authoritative source:** <https://www.gov.uk/government/statistical-data-sets/transaction-unique-identifier-and-uprn-look-up-table-dataset>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Published with OGL statements for both HM Land Registry and OS; any join with Price Paid address components remains subject to separate third-party address terms. Official technical spec says non-backdated, postcode address file-dependent, often absent for land-only sales and newly built or unmatched addresses; a single sale can have several UPRNs e.g. flats. UPRN is an addressable location, not a freehold polygon, building, owner, policy record, reinstatement cost or TIV. Distinct from transaction UID to INSPIRE ID lookup which excludes leaseholds.

## Dutch Kadastrale Kaart Bebouwing BGT-derived building footprint and BAG pand-ID linkage

**Candidate ID:** `nl.kadaster.bgt-bebouwing-bagid.2026`  
**Provider:** Kadaster / PDOK, derived from Basisregistratie Grootschalige Topografie (BGT)  
**Categories:** `building_geometry`, `official_building_id_crosswalk`, `bgt`, `bag`, `netherlands`  
**Spatial scope:** Netherlands; BGT-derived subset of building geometries shown in Kadastrale Kaart, not the full BAG inventory  
**Temporal scope:** Mutable daily PDOK OGC API; source test 2026-11-04, per-feature source dates vary  
**Resolution / granularity:** Bebouwing feature MultiPolygon with identification_local_id, identificatie_bag_pnd direct BAG pand ID, bgt_status and publishing dates; one BAG building can potentially have multiple BGT geometries  
**Potential roles:** `official_bgt_to_bag_id_crosswalk`, `parcel_to_bgt_geometry_to_bag_attribute_join`, `building_geometry_lineage_quality_challenge`  
**Access hint:** `pdok_public_ogc_collection_cc_by_4_0_bgt_origin_and_per_feature_rights_review`  
**Authoritative source:** <https://api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1/collections/bebouwing?f=html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is NOT an independent building register: Bebouwing is BGT-derived and only a subset of buildings, accessed through the same Kadaster Kadastrale Kaart OGC service as the separate Perceel parcel collection. Original tiny CRS84 bbox probe 2026-11-04 returned 9 Bebouwing features, 9 populated BAG pand IDs, 9/9 exact ID matches against 21 BAG pand features (all 9 linked BAG objects Pand in gebruik); 9/9 BGT centroid parcel candidates in 19 parcel polygons. No pagination in those bounded calls. These are spatial/entity linkage hypotheses, not property-owner records, legal parcel/footprint intersections, dwelling counts, insurer membership, insured sums, commercial model admission or independent source validation. Keep official source timestamps and multiple-geometry-per-BAG diagnostics.
