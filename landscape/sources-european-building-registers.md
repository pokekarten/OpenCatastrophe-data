<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-european-building-registers.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-european-building-registers.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission source discovery of European national building identifiers, footprints, 3D height, EPC/enrichment and cost context for bounded EUBUCCO crosswalk pilots; documentation does not permit source-data acquisition or model-input use.

**Entries:** 20

## Germany nationwide LoD2-DE 3D buildings

**Candidate ID:** `de.adv.lod2-de`  
**Provider:** AdV / ZSHH / BKG  
**Categories:** `buildings`, `3d_geometry`, `exposure`, `germany`  
**Spatial scope:** Germany, nationwide  
**Temporal scope:** Annual snapshots; April 2026 product documented  
**Resolution / granularity:** About 59 million official building models; unique object ID, footprint reference, height, function, roof, optional storeys/address  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `paid_national_dataset_citygml_sample_public`  
**Authoritative source:** <https://www.ldbv.bayern.de/vermessung/zshh/lod2-de_en.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Nationwide full product is offered commercially, not a general free bulk feed. Join EUBUCCO by reviewed footprint spatial matching; do not infer construction year from production date. Official object IDs may link LoD2 to 2D footprints. Separate per-state open data may offer a cheaper pilot.

## Bavaria open LoD2 3D buildings

**Candidate ID:** `de.bayern.lod2.open`  
**Provider:** Bayerisches Landesamt für Digitalisierung, Breitband und Vermessung  
**Categories:** `buildings`, `3d_geometry`, `height`, `germany`  
**Spatial scope:** Bavaria, Germany  
**Temporal scope:** Regularly updated state open-data publication; pin selected download revision  
**Resolution / granularity:** Official CityGML LoD2 building geometry with modelled roof shape; details and attributes require tile-specific checks  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `public_state_download_review_exact_tiles_and_licence`  
**Authoritative source:** <https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=lod2>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Prioritise one Bavarian pilot tile. Record licence/attribution, tile identity, CRS, building model identifiers, year and source; compare polygon geometry and height against EUBUCCO. State data does not establish insured value or verified occupancy.

## Netherlands Basic Register of Addresses and Buildings (BAG)

**Candidate ID:** `nl.kadaster.bag`  
**Provider:** Kadaster / PDOK  
**Categories:** `buildings`, `building_ids`, `addresses`, `building_age`, `netherlands`  
**Spatial scope:** Netherlands, nationwide  
**Temporal scope:** Continuously maintained administrative register; service refreshed regularly  
**Resolution / granularity:** BAG building objects (panden), addresses and associated administrative attributes; stable register IDs with lifecycle/status  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `public_ogc_api_exact_collections_limits_and_rights_review`  
**Authoritative source:** <https://api.pdok.nl/kadaster/bag/ogc/v2>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Use BAG pand identifiers for internal linkage to 3DBAG, and match EUBUCCO geometries spatially with version/time checks. Demolished/historical status must not be treated as current active buildings. Avoid publishing address-level personal linkage.

## Netherlands 3DBAG building models

**Candidate ID:** `nl.tudelft.3dbag`  
**Provider:** 3D Geoinformation Research Group / TU Delft  
**Categories:** `buildings`, `3d_geometry`, `height`, `netherlands`  
**Spatial scope:** Netherlands, nationwide  
**Temporal scope:** Versioned derived 3D releases; source snapshots must be pinned  
**Resolution / granularity:** Building-level LoD 3D geometry, elevations/heights and connections to BAG identifiers  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `public_documented_tile_download_and_webservices_rights_review`  
**Authoritative source:** <https://docs.3dbag.nl/en/delivery/webservices/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Strong BAG-ID connection to ground building geometry. 3DBAG is a derived geometry/model product; preserve point-cloud/source, release and modelling uncertainty before adopting derived heights. Suitable holdout for EUBUCCO.

## France Référentiel National des Bâtiments (RNB)

**Candidate ID:** `fr.rnb.buildings`  
**Provider:** RNB / French public administration  
**Categories:** `buildings`, `building_ids`, `geocoding`, `france`  
**Spatial scope:** France, nationwide  
**Temporal scope:** Maintained registry; published national and departmental extracts plus API  
**Resolution / granularity:** Building identities with public RNB identifiers, footprints/location and administrative change history  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `public_api_and_department_national_exports_terms_rate_review`  
**Authoritative source:** <https://www.data.gouv.fr/datasets/referentiel-national-des-batiments>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** RNB-ID is the canonical join candidate with IGN BD TOPO and some ADEME DPE observations; record match multiplicity, building status, source timestamp and any split/merge. A public identity is not a verified insurance location.

## France IGN BD TOPO buildings and RNB crosswalk

**Candidate ID:** `fr.ign.bdtopo.buildings`  
**Provider:** Institut national de l'information géographique et forestière (IGN)  
**Categories:** `buildings`, `building_ids`, `geometry`, `france`  
**Spatial scope:** France, nationwide  
**Temporal scope:** Maintained BD TOPO releases, including 2026 documented mapping  
**Resolution / granularity:** Building polygons and a documented association between RNB identifiers and BD TOPO building identifiers  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `public_ign_documentation_dataset_release_and_reuse_review`  
**Authoritative source:** <https://bdtopoexplorer.ign.fr/batiment_rnb_lien_bdtopo>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Prefer the publisher RNB-to-BD-TOPO relation rather than an assumed universal one-to-one join. Preserve release, topology, exceptions and overlapping/multiple objects when matching EUBUCCO. Do not use mapping as identity proof without geometry checks.

## France Base de Données Nationale des Bâtiments (BDNB)

**Candidate ID:** `fr.cstb.bdnb`  
**Provider:** CSTB / BDNB  
**Categories:** `buildings`, `building_attributes`, `energy`, `france`  
**Spatial scope:** France, national and department products  
**Temporal scope:** Versioned public BDNB files including 2026-02.b published dataset  
**Resolution / granularity:** Building-level data and derived attributes from public sources, including energy and construction context; varying source confidence  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `public_bulk_and_api_source_rights_by_field_review`  
**Authoritative source:** <https://bdnb.io/download/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Potential enrichment through BDNB building IDs and mapped RNB records after verifying field-level lineage. Many columns are inferred; a same-coordinate match is not enough to assert exact year/material. Check privacy and reuse conditions per release.

## France ADEME building energy performance diagnostics (DPE)

**Candidate ID:** `fr.ademe.dpe`  
**Provider:** ADEME / French energy performance observatory  
**Categories:** `buildings`, `energy_certificates`, `building_attributes`, `france`  
**Spatial scope:** France, with coverage limited to properties having certificates  
**Temporal scope:** Ongoing certificate issuance and public-data revisions  
**Resolution / granularity:** Energy performance certificate records, some tied to RNB building IDs and address context  
**Potential roles:** `building_attribute_enrichment`, `building_stock_validation`  
**Access hint:** `public_api_open_data_exact_field_and_licence_review`  
**Authoritative source:** <https://www.data.gouv.fr/dataservices/api-dpe-logements>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** RNB-linked certificates allow controlled enrichment, but a dwelling/EPC is not always one full building. Distinguish unit from building, multiple certificates per property, source date, uncertain geocodes and private-address handling; not a universal complete stock inventory.

## Poland BDOT10k national topographic object database

**Candidate ID:** `pl.gugik.bdot10k`  
**Provider:** GUGiK / Geoportal.gov.pl  
**Categories:** `buildings`, `topography`, `footprints`, `poland`  
**Spatial scope:** Poland, nationwide  
**Temporal scope:** Maintained official topographic object coverage; freeze selected release  
**Resolution / granularity:** Vector topographic objects including 2D buildings and selected descriptive building information at 1:10,000 class  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `public_geoportal_files_by_region_rights_review`  
**Authoritative source:** <https://www.geoportal.gov.pl/pl/dane/baza-danych-obiektow-topograficznych-bdot10k/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Reference candidate for Polish EUBUCCO geometry coverage. BDOT10k footprint keys and object revisions must be retained, and scale/completeness assessed; building counts alone do not show insured exposure.

## Poland official 3D building models based on BDOT10k

**Candidate ID:** `pl.gugik.buildings3d`  
**Provider:** GUGiK / Geoportal.gov.pl  
**Categories:** `buildings`, `3d_geometry`, `height`, `poland`  
**Spatial scope:** Poland, substantial but not necessarily complete national coverage  
**Temporal scope:** Official model releases; regional availability varies  
**Resolution / granularity:** 3D building geometry compiled from BDOT10k footprints and elevation inputs  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `public_portal_bulk_or_tile_download_rights_review`  
**Authoritative source:** <https://www.geoportal.gov.pl/en/data/other-data/3d-models-of-building/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Link to the underlying BDOT10k footprint after validating object IDs, snapshot and geometry relationships. Derivative height/roof information is not independent cadastral evidence or replacement value.

## Czechia RÚIAN building and address register

**Candidate ID:** `cz.cuzk.ruian.buildings`  
**Provider:** ČÚZK (Czech Office for Surveying, Mapping and Cadastre)  
**Categories:** `buildings`, `building_ids`, `geometry`, `czechia`  
**Spatial scope:** Czech Republic, nationwide  
**Temporal scope:** Continuously maintained reference register with periodic VFR public extracts  
**Resolution / granularity:** Official building objects, registered identifiers, addresses and selected spatial relationships  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `public_free_vfr_download_and_inspire_services_rights_review`  
**Authoritative source:** <https://vdp.cuzk.gov.cz/vdp/ruian>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** High-priority primary-source Czech building benchmark. Preserve RÚIAN building IDs and update timestamp and validate whether extracted geometry is building polygon or representative point. Do not conflate parcel, address and building identities.

## Spain Dirección General del Catastro INSPIRE Buildings

**Candidate ID:** `es.catastro.inspire.buildings`  
**Provider:** Dirección General del Catastro / Ministerio de Hacienda  
**Categories:** `buildings`, `cadastral`, `geometry`, `spain`  
**Spatial scope:** Spain excluding Basque Country and Navarra in this service  
**Temporal scope:** Municipality-level published ATOM files and WFS service; update frequency by service  
**Resolution / granularity:** INSPIRE building geometries and cadastre-linked identifiers, with service-specific attribute scope  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `public_wfs_atom_service_rights_and_geographic_exclusions_review`  
**Authoritative source:** <https://www.catastro.hacienda.gob.es/webinspire/index_eng.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Building footprint validation and possible cadastral-attribute joins require exact atom snapshot, municipality, identifiers and geometry structure. Catalan and other regional cases require source-specific checks; do not claim full Spain coverage from the central service.

## Switzerland swissBUILDINGS3D 3.0 Beta

**Candidate ID:** `ch.swisstopo.swissbuildings3d3`  
**Provider:** Federal Office of Topography swisstopo  
**Categories:** `buildings`, `3d_geometry`, `building_ids`, `switzerland`  
**Spatial scope:** Switzerland; official EGID integration available in a growing subset of cantons  
**Temporal scope:** Rolling beta releases; June 2026 release documented  
**Resolution / granularity:** 3D building roofs, facades and footprints, with federal building identifiers (EGID) in supported regions  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `public_official_download_version_and_terms_review`  
**Authoritative source:** <https://www.swisstopo.admin.ch/en/landscape-model-swissbuildings3d-3-0-beta>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Where EGID is present, connect to Swiss official building/address registers; where absent, use spatial geometry with explicit uncertainty. Distinguish beta geographic coverage from all-Switzerland visualization and do not project EGID completeness to all cantons.

## Denmark Building and Dwelling Register (BBR)

**Candidate ID:** `dk.datafordeler.bbr`  
**Provider:** Klimadatastyrelsen / Datafordeler  
**Categories:** `buildings`, `construction_year`, `occupancy`, `denmark`  
**Spatial scope:** Denmark, nationwide administrative register  
**Temporal scope:** Maintained administrative building and dwelling records; modern GraphQL service  
**Resolution / granularity:** BBR building, unit, floors, usage and construction attributes associated with Danish register identifiers  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `api_key_oauth_graphql_file_download_terms_review`  
**Authoritative source:** <https://datafordeler.dk/dataoversigt/bygnings-og-boligregistret-bbr/bbr-graphql/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Exact BBR identifier and address/building linkage requires the source schema. Prefer GraphQL/file download; historical REST is being retired. Verify authentication, field visibility, location precision, status and redistribution before any use.

## Finland National Land Survey INSPIRE Buildings polygons

**Candidate ID:** `fi.nls.inspire.buildings`  
**Provider:** National Land Survey of Finland  
**Categories:** `buildings`, `geometry`, `finland`  
**Spatial scope:** Finland, coverage according to NLS official INSPIRE building dataset  
**Temporal scope:** National topographic/inspire revisions; separate 3D sample areas  
**Resolution / granularity:** INSPIRE-compatible building polygon features via official download services  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `official_wfs_download_rights_version_review`  
**Authoritative source:** <https://www.maanmittauslaitos.fi/en/maps-and-spatial-data/datasets-and-interfaces/map-interface-services/inspire-directive-compliant>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Compare exact polygon definitions and region coverage with EUBUCCO. Finnish 3D buildings are not currently all-country complete; preserve model versus surveyed sources and validate CRS/IDs before automated joining.

## Norway FKB-Bygning building geometries

**Candidate ID:** `no.geonorge.fkb-bygning`  
**Provider:** Kartverket / Geovekst / Geonorge  
**Categories:** `buildings`, `geometry`, `norway`  
**Spatial scope:** Norway, high-resolution mapped regions  
**Temporal scope:** Continuously updated FKB source; delivery/access depend on user class  
**Resolution / granularity:** Official FKB building geometry with source/topographic characteristics distributed through Geonorge formats and APIs  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `conditional_access_licence_and_possible_fees_review`  
**Authoritative source:** <https://kartkatalog.geonorge.no/metadata/fkb-bygning/8b4304ea-4fb0-479c-a24d-fa225e2c6e97>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Access can be conditional or paid depending on user; catalogue visibility is not permission to bulk download. Evaluate building object IDs and survey vintages only after obtaining an authorised asset and rights decision.

## Sweden Lantmäteriet Building Download / INSPIRE

**Candidate ID:** `se.lantmateriet.buildings`  
**Provider:** Lantmäteriet  
**Categories:** `buildings`, `building_register`, `sweden`  
**Spatial scope:** Sweden, municipalities/INSPIRE distribution  
**Temporal scope:** Maintained Swedish building/register data; access via national provider distribution  
**Resolution / granularity:** Official building products include Building Direct and municipal INSPIRE downloads with some purposes/use classes  
**Potential roles:** `eubucco_footprint_crosswalk`, `building_feature_enrichment`, `building_stock_validation`  
**Access hint:** `provider_authorization_and_fees_possible_terms_review`  
**Authoritative source:** <https://www.lantmateriet.se/en/geodata/our-products/product-list/building-download-inspire>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Do not equate Lantmäteriet discoverability with a no-cost full commercial data grant. Confirm which geometry fields and persistent ids are available at exact municipal release; compare to EUBUCCO with source and temporal alignment.

## England and Wales official Energy Performance Certificates bulk data

**Candidate ID:** `uk.gov.epc.england-wales`  
**Provider:** UK Department for Levelling Up / GOV.UK  
**Categories:** `buildings`, `energy_certificates`, `building_attributes`, `uk`  
**Spatial scope:** England and Wales, certified buildings only  
**Temporal scope:** Rolling EPC data releases, multiple certificate vintages  
**Resolution / granularity:** Domestic/non-domestic energy certificates with construction and energy attributes for covered properties  
**Potential roles:** `building_attribute_enrichment`, `building_stock_validation`  
**Access hint:** `account_registration_bulk_access_licence_privacy_review`  
**Authoritative source:** <https://get-energy-performance-data.communities.gov.uk/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Not a comprehensive building inventory or authoritative footprint layer. Linking to building geometry requires carefully validated UPRN/address mapping, one-to-many EPC relationships and permitted data use; no identity-based release without privacy review.

## Eurostat construction costs of new residential buildings

**Candidate ID:** `eu.eurostat.construction-cost-index`  
**Provider:** Eurostat / European Commission  
**Categories:** `economic_statistics`, `construction_cost`, `value_context`, `europe`  
**Spatial scope:** European statistical reporting countries  
**Temporal scope:** Time-series construction cost/producer price indicators; revisions possible  
**Resolution / granularity:** Country- and period-specific index values for residential construction cost developments  
**Potential roles:** `replacement_cost_index_context`, `regional_exposure_validation`  
**Access hint:** `public_eurostat_api_bulk_statistics_rights_review`  
**Authoritative source:** <https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Construction_producer_price_and_construction_cost_indices_overview>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Use only to index externally validated replacement cost benchmarks to a specific price year. An index is NOT an absolute cost per square metre, building-level replacement value or insurance sum. Distinguish materials, labor and producer price definitions and country coverage.

## crossCERT open database for energy performance certificate testing

**Candidate ID:** `eu.crosscert.epc.reference`  
**Provider:** crossCERT EU project consortium  
**Categories:** `energy_certificates`, `building_attributes`, `validation`, `europe`  
**Spatial scope:** Selected European and UK study countries; project sample not comprehensive  
**Temporal scope:** Research project dataset, version and covered sample dates to be reviewed  
**Resolution / granularity:** Selected buildings with comparable EPC-related variables used for cross-country methodology tests  
**Potential roles:** `building_attribute_enrichment`, `building_stock_validation`  
**Access hint:** `public_research_dataset_rights_and_sample_access_review`  
**Authoritative source:** <https://www.crosscert.eu/our-solutions/open-database-for-epc-testing>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Potential independent benchmarking of attribute semantics and imputation, not a complete building inventory. Preserve participating countries, observational selection bias, privacy/licence constraints and no invented building-level matches when no stable identifier exists.
