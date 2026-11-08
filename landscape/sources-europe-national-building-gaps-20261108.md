<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-europe-national-building-gaps-20261108.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-europe-national-building-gaps-20261108.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-08`  
**Purpose:** Non-admission research discovery of differentiated original national European building register, footprint, INSPIRE service and viewer products for a 51-country coverage audit. These metadata leads do not admit data for commercial CAT model use.

**Entries:** 19

## Poland GUGiK EGiB official building geometries national GeoParquet / county GPKG

**Candidate ID:** `pl.gugik.egib-building-parcels.2026`  
**Provider:** Head Office of Geodesy and Cartography Poland (GUGiK)  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Poland; nationwide aggregate of registered county cadastral WFS services  
**Temporal scope:** New download offer announced 2026-02-04; federated WFS announced 2026-07-16; original asset release dates vary by county  
**Resolution / granularity:** Country and voivodeship GeoParquet, voivodeship and county GeoPackage, federated county WFS for EGiB building geometry  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_public_bulk_download_original_asset_licence_and_county_coverage_review`  
**Authoritative source:** <https://www.gov.pl/web/gugik/budynki-z-egib-dostepne-do-pobrania-w-serwisie-wwwgeoportalgovpl>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** EGiB cadastral building feature products are DISTINCT from the already catalogued BDOT10k generalized topographic buildings and 3D models. WFS is federated across county services and may have incomplete local availability. Neither geometry nor EGiB ID is evidence of actual policyholder, occupancy, construction quality or TIV. Freeze county/voivodeship release, CRS, IDs and official file conditions.

## Slovakia official HVD INSPIRE Buildings nationwide open downloads

**Candidate ID:** `sk.gku.inspire-hvd-buildings.2026`  
**Provider:** Geodetic and Cartographic Institute Bratislava (GKÚ) / ÚGKK Slovakia  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Slovakia nationwide  
**Temporal scope:** Official download list updated 2026-02-02; verify individual GML/GPKG/GDB vintage  
**Resolution / granularity:** Official INSPIRE HVD Buildings files in GML, GeoPackage, ESRI File Geodatabase; country download  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_public_bulk_data_cc_by_4_0_listed_exact_file_vintage_hash_not_audited`  
**Authoritative source:** <https://www.skgeodesy.sk/geoportal-en/inspire/download-data/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Source publicly lists CC BY 4.0 for the Buildings product and provides links incl. https://opendata.skgeodesy.sk/static/INSPIRE/Buildings/inspire_bu_gpkg.zip. Distinct from Slovakia WMTS base maps. Validate full national geometry/count, building vs building-part identifiers, height availability, and exact source attribution before adoption.

## Croatia DGU digital cadastral map building WFS and INSPIRE ATOM download

**Candidate ID:** `hr.dgu.inspire-buildings-wfs-atom.2026`  
**Provider:** Državna geodetska uprava (DGU), Croatia  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Croatia, nationwide INSPIRE cadastral buildings subject to actual coverage  
**Temporal scope:** Official portal inspected 2026-11-08; individual update vintage unknown  
**Resolution / granularity:** INSPIRE WFS for digital cadastral map Buildings; separate ATOM feed for INSPIRE BU-core2d  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_anonymous_wfs_and_atom_individual_dgu_terms_need_review`  
**Authoritative source:** <https://geoportal.dgu.hr/cms/en/data-and-services/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** DGU specifically identifies anonymous INSPIRE Buildings WFS https://api.uredjenazemlja.hr/services/inspire/bu/wfs and ATOM https://geoportal.dgu.hr/services/atom/bu-core2d/xml. Building geometries derive from cadastral maps and are not independent of the same official cadastre and EUBUCCO government input. Check WFS paging, GML schema, rights and cadastral completeness.

## Finland Ryhti completed building records and building INSPIRE OGC API

**Candidate ID:** `fi.syke.ryhti-completed-buildings.2026`  
**Provider:** Finnish Environment Institute (SYKE) / Ryhti built environment system  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Finland nationally, completed building records; separate still-progressing data products  
**Temporal scope:** Daily completed-building files per Ryhti 2026 provider page; content depends on ongoing deployment  
**Resolution / granularity:** Open completed-building CSV/JSON .gz packages updated daily plus OGC API Features and INSPIRE BU building WMS  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_open_daily_csv_json_and_ogc_api_feature_exact_schema_rights_review`  
**Authoritative source:** <https://ryhti.syke.fi/en/front-page/services/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** New national building-record feed is distinct from the existing National Land Survey Finland topographic INSPIRE buildings. Official package URLs include open_building.csv.gz and open_building.json.gz. Verify building ID join, completion status, geocodes, area/height fields, live coverage, source update date and legal open licence for downstream insurer modelling.

## Iceland official IS 50V buildings national vector base map layer

**Candidate ID:** `is.natt.is50v.buildings`  
**Provider:** Natural Science Institute of Iceland (Náttúrufræðistofnun Íslands)  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Iceland, national topographic coverage  
**Temporal scope:** Continuously maintained official IS50V; tile release dates vary  
**Resolution / granularity:** 1:50,000 vector base map includes buildings layer, coordinates ISN2004/Lambert EPSG:3057  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_public_vector_download_provided_generalized_topography_not_cadastral`  
**Authoritative source:** <https://www.natt.is/en/resources/geospatial-data/base-map-data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** IS50V is a generalized cartographic buildings layer not a complete cadastral inventory of every annex, unit or insurable asset. Confirm actual building polygon/point classes, edition, source licence and scale-related omissions. Distinct from private commercial Iceland addresses and EUBUCCO (which does not cover Iceland).

## Ireland Tailte Éireann High Value Dataset Buildings

**Candidate ID:** `ie.tailte.high-value-buildings`  
**Provider:** Tailte Éireann / Irish national open data catalogue  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Republic of Ireland; provider HVD scope and 26-county coverage to be checked  
**Temporal scope:** Public HVD catalogue current 2026; exact layer update not inspected  
**Resolution / granularity:** Official high-value INSPIRE Buildings dataset/service catalogue; vector distribution capabilities require validation  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_hvd_metadata_open_access_actual_download_and_licence_review`  
**Authoritative source:** <https://data.gov.ie/dataset/high-value-dataset-buildings1>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Do not confuse this product with commercial GeoDirectory address/point records or the linked Building Groups HVD. Inspect actual endpoint, geometry definitions, rights and nationwide completeness; not automatically all island of Ireland (Northern Ireland has separate OSNI sources).

## Latvia State Land Service INSPIRE Buildings open service

**Candidate ID:** `lv.vzd.inspire-buildings`  
**Provider:** Latvian State Land Service (Valsts zemes dienests, VZD)  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Latvia; INSPIRE cadastral building scope and completeness to validate  
**Temporal scope:** Official open-data portal catalogue 2026; per-feature dates not inspected  
**Resolution / granularity:** Buildings INSPIRE data and separate WFS dataset; download/OGC endpoints in dataset resources  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_public_insipre_catalogue_exact_original_wfs_and_licence_review`  
**Authoritative source:** <https://data.gov.lv/dati/dataset/ekas-inspire>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Separate this from the open Latvian cadastral *text* building attributes and Riga municipal buildings polygons; test exact geometry fields, building-vs-building-part, API limitations, availability and use conditions. Not independently surveyed against EUBUCCO if both reuse cadastre.

## Cyprus Department of Lands and Surveys INSPIRE buildings dataset

**Candidate ID:** `cy.dls.inspire-buildings`  
**Provider:** Cyprus Department of Lands and Surveys / national open data portal  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Republic of Cyprus; exact cadastral service geographical scope to review  
**Temporal scope:** Current INSPIRE public record; original feature update date unknown  
**Resolution / granularity:** Government INSPIRE Buildings metadata and DLS REST building layers  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_buildings_dataset_service_exact_download_licence_and_coverage_review`  
**Authoritative source:** <https://www.data.gov.cy/el/dataset/ktiria-inspire>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher provides cadastral buildings source, but review exact full-island coverage, INSPIRE 2D schema, DLS terms, and disputed areas before assuming nationwide completeness. A public web map is not itself proof of unrestricted original bulk geometry distribution.

## Portugal Base Geográfica de Edifícios (BGE) official building geographic base

**Candidate ID:** `pt.dgt.bge-buildings`  
**Provider:** Portuguese national open data portal / Direção-Geral do Território  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Portugal; mainland and island geographic coverage must be verified in chosen asset  
**Temporal scope:** Publisher resource current catalogue; vintage and maintenance frequency need review  
**Resolution / granularity:** Geographical buildings base; actual downloadable layers and polygon schema need original-file verification  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_public_dataset_catalogue_extract_and_product_terms_review`  
**Authoritative source:** <https://dados.gov.pt/pt/datasets/base-geografica-de-edificios/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct from DGT cadastral *parcels* and the Portuguese address/census building records. A cadastral parcel is NOT a building polygon and its market value is not TIV. Check exact building class, regional coverage including Madeira/Azores and file format before admission.

## Hungary Lechner National Spatial Data Ecosystem Buildings

**Candidate ID:** `hu.lechner.buildings`  
**Provider:** Lechner Knowledge Center (Lechner Tudásközpont)  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Hungary; national spatial-data source subject to access/licence checks  
**Temporal scope:** Catalogue current 2026; chosen product/release vintage not inspected  
**Resolution / granularity:** Official Buildings dataset metadata/service; possible Geoshop conditions  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_national_catalogue_access_terms_licence_bulk_availability_unverified`  
**Authoritative source:** <https://data.lechnerkozpont.hu/en/datasets/buildings>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The web catalogue describes a Buildings product but not automatically a freely redistributable national GeoPackage. Confirm map vs download, precise building feature schema, rights and INSPIRE transformations. This is not the same as Hungarian parcels or address registry.

## Albania ASIG/ASHK cadastral building geospatial layer

**Candidate ID:** `al.asig.cadastral-buildings`  
**Provider:** State Authority for Geospatial Information (ASIG) and State Cadastre Agency (ASHK)  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Albania; only cadastral zones or blocks processed in the relevant agency system  
**Temporal scope:** Publisher update announcement; date and coverage differ by cadastral zone  
**Resolution / granularity:** National Geoportal layer Cadastral Buildings (ALBSCAD), cadastral blocks and parcels  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_public_geoportal_building_layer_bulk_api_and_reuse_unverified`  
**Authoritative source:** <https://geoportal.asig.gov.al/en/node/3372>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher explicitly says building layer is updated for processed cadastral zones/blocks; NOT proof of nationwide completeness. Confirm public WFS/download, per-feature licence, state update and geometries. Use OSM/Overture in documented missing areas and do not mix cadastral parcels with buildings.

## North Macedonia INSPIRE Buildings OGC Features service

**Candidate ID:** `mk.arec.inspire-buildings-ogc`  
**Provider:** Agency for Real Estate Cadastre / national spatial data infrastructure North Macedonia  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** North Macedonia; exact geographic service coverage and object count to verify  
**Temporal scope:** OGC endpoint current 2026; data vintage not inspected  
**Resolution / granularity:** INSPIRE Buildings OGC Features service conformance endpoint  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_ogc_feature_service_metadata_original_collection_rights_unverified`  
**Authoritative source:** <https://gisserver.gdi.mk/arcgis/rest/services/INSPIRE/Buildings/OGCFeatureServer/conformance?f=html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** A conformance page does NOT prove anonymous data retrieval or rights. Inspect collections, /items paging and original INSPIRE provider licence, then characterize polygons, part IDs and country coverage. Avoid conflating parcel outlines or all building parts with unique insurable locations.

## Serbia GeoSrbija official INSPIRE Buildings WFS metadata

**Candidate ID:** `rs.rgz.inspire-buildings-wfs`  
**Provider:** Republic Geodetic Authority (RGZ) / GeoSrbija  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Serbia; national INSPIRE Buildings coverage to check  
**Temporal scope:** Official metadata available in 2026; original updates differ  
**Resolution / granularity:** INSPIRE Buildings WFS service metadata record, original endpoint must be followed  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_national_wfs_metadata_exact_endpoint_access_and_licence_review`  
**Authoritative source:** <https://metakatalog.geosrbija.rs/geonetwork/srv/api/records/a2d6936c-2b95-42cf-b55f-d5fbff7da19d>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Metadata record confirms an INSPIRE Buildings WFS source but does not establish unconditional nationwide polygon access or redistribution rights. Verify actual service capabilities, pagination, coordinate order, update vintage and compliance. Kosovo coverage is separate and must not be inferred here.

## Georgia NSDI national geoportal Registered Building layer

**Candidate ID:** `ge.napr.nsdi-registered-buildings`  
**Provider:** National Agency of Public Registry (NAPR) Georgia  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Georgia; registered buildings layer in official National Spatial Data Infrastructure  
**Temporal scope:** Official national geoportal presented 2025, expanded 2026; per-layer vintage unknown  
**Resolution / granularity:** Registered Building layer and cadastral services in NSDI, with separate discovery/download controls  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_building_layer_catalogue_public_view_download_and_licence_review`  
**Authoritative source:** <https://nsdi.gov.ge/en/geoportal>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NSDI geoportal lists Registered Building as land-cadastre dataset; this does not mean universal or free full-building polygon downloads. Check original distribution API, feature geometry, cadastre ID, jurisdiction (incl. contested territories), rights and missingness. Do not infer insurer ownership or TIV.

## Liechtenstein official Building and Dwelling Register public data

**Candidate ID:** `li.statistik.gwr-building-register`  
**Provider:** Amt für Statistik Liechtenstein / opendata.swiss  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Principality of Liechtenstein; national register scope  
**Temporal scope:** Public register current; exact time range and extract refresh need review  
**Resolution / granularity:** Official building/dwelling register open-data metadata, building characteristics/identity; geometry precision needs validation  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_public_register_scope_building_geometry_and_licence_review`  
**Authoritative source:** <https://opendata.swiss/en/dataset/gebaude-und-wohnungsregister-liechtenstein>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** A dwelling or address record does not necessarily correspond to one footprint; field-level public availability and Geocat coverage must be verified. Liechtenstein is NOT in EUBUCCO EU27+UK+NO+CH, and Swiss building registers cannot be treated as Liechtenstein coverage.

## Andorra historic building situation polygon inventory (1995 imagery)

**Candidate ID:** `ad.iea.buildings-historic.1995`  
**Provider:** Institut d'Estudis Andorrans / Government of Andorra environment/carto units  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Andorra nationwide, older 1:5000 building structures  
**Temporal scope:** Aerial imagery 1995, map prepared 2000; not current exposure  
**Resolution / granularity:** Topologically structured building polygons, types incl public, construction, ruins and shelter; ESRI Shapefile/MiraMon/DXF available  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `public_download_historic_shapefile_reuse_licence_and_original_dataset_integrity_unverified`  
**Authoritative source:** <https://www.iea.ad/situacio-d-edificis>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Strong historical reference, NOT a modern nationwide active-structure census. Source explicitly based on 1995 imagery; buildings may have changed drastically. Review datum NTF/Lambert Zone III, 1:5000 generalization and exact archive licence before use. Never map 'construction/ruin' to current insurable asset.

## Moldova Cadastral Agency WMS/WFS GeoServer building-layer candidate

**Candidate ID:** `md.ipcbi.geoserver-cadastral`  
**Provider:** Public Institution Cadastre of Immovable Property (IP CBI), Moldova  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Moldova; GeoServer workspaces, actual buildings geometry layer needs direct verification  
**Temporal scope:** Live public GeoServer page 2026, original dataset time unstated  
**Resolution / granularity:** National cadastral GeoServer with anonymous OGC WMS/WFS services and multiple workspaces/layers  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_anonymous_geoserver_buildings_layer_and_reuse_not_yet_demonstrated`  
**Authoritative source:** <https://map.cadastru.md/geoserver/index.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This source identifies an official cadastral service, NOT a verified complete Buildings layer or licensed national download. Inspect advertised WFS FeatureTypes and exact provider layer/class, geometry CRS, paging and rights. Treat any secondary Source Cooperative Cladiri mirror as derived from the same cadastre, not independent survey.

## San Marino state cadastral geospatial map services

**Candidate ID:** `sm.gov.catasto-building-map-service`  
**Provider:** Republic of San Marino Secretariat for Territory / Ufficio Catasto  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Republic of San Marino, national map-services scope  
**Temporal scope:** Live 2026 official cadastral/urban-planning service, building layer date unknown  
**Resolution / granularity:** Government ArcGIS MapServer for cadastral cartography and separately public buildings/places layers  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_gis_mapserver_view_only_licence_and_download_unverified`  
**Authoritative source:** <https://mappeonline.pa.sm/arcgis/rest/services/Cartografia/catasto_GR/MapServer>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Government layers demonstrate cartographic data, not confirmed reusable, nationwide actual individual building polygons. Separate MapServer image tiles, FeatureServer query and cadastral parcel access before assuming export. No construction-year/insured-value evidence.

## Bosnia and Herzegovina FBiH cadastral buildings metadata and web services

**Candidate ID:** `ba.fgu.federation-cadastre-metadata`  
**Provider:** Federation of Bosnia and Herzegovina Federal Geodetic Administration (FGU)  
**Categories:** `buildings`, `cadastral`, `europe`  
**Spatial scope:** Federation of Bosnia and Herzegovina only; Republika Srpska and Brčko not covered  
**Temporal scope:** Current cadastral metadata service, precise timestamp unknown  
**Resolution / granularity:** Official FBiH cadastral database metadata and Katastar.ba web services; buildings layer schema needs proof  
**Potential roles:** `building_geometry_source_review`, `national_coverage_gap_assessment`  
**Access hint:** `official_federation_only_web_services_bulk_and_commercial_rights_unverified`  
**Authoritative source:** <https://www.katastar.ba/servisi>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This provider covers ONLY FBiH and must not be labeled nationwide BiH exposure. State entities have separate cadastral authorities. Verify original building layer availability, completeness, service terms and geom before any downstream use; other parts of BiH require a distinct provider review.
