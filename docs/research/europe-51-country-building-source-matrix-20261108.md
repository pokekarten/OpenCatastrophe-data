<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Europe building exposure: all 51 country / jurisdiction scope audit (2026-11-08)

**Status:** human-authored, evidence-scoped **research**, not data/model admission. **Primary task:** [#1441](https://github.com/pokekarten/OpenCatastrophe-data/issues/1441). **Country definition:** EU 27, the UK, Norway, Switzerland and 21 additional states/jurisdictions including Kosovo and the European portions of Kazakhstan, Russia and Türkiye. Armenia, Azerbaijan and Georgia included as wider European/European-neighbourhood scope. This is a **51-row research scope**, not a claim about official UN definitions or sovereignty. Non-sovereign territories are below.

## Method and important limits

1. The common baseline is [EUBUCCO v0.2](https://eubucco.com/data/download/v0.2) with **30 countries (EU27, UK, Norway, Switzerland)** and over 322 million harmonised building records. Building type, height and floors coverage reflect substantial *estimated or merged* values; **construction-year coverage only 15.9%**. EUBUCCO documentation [data format](https://docs.eubucco.com/v0.2/data-format/) and [provider-source shares](https://docs.eubucco.com/latest/).
2. [OpenStreetMap/Geofabrik](https://download.geofabrik.de/europe.html) and [Overture Maps buildings](https://docs.overturemaps.org/guides/buildings/) are fallbacks across Europe, but coverage and building meaning are variable, and source geometry can be shared. [Microsoft GlobalMLBuildingFootprints](https://github.com/microsoft/GlobalMLBuildingFootprints) is another original-derived global family (CDLA Permissive 2.0); do not sum duplicate source polygons.
3. The primary link in each table row is the **best catalogued source lead for the country**, **not** proof of a nationwide current free-to-download building-polygon file. Access labels distinguish actual documented downloadable official assets from INSPIRE/service or viewer-only leads. No raw provider bytes, API feature records or insurer data were obtained in this research artifact.
4. EUBUCCO 'Ja' means in its advertised 30-country scope, **not** full current official cadastre, every region or historical consistency. Licences and commercial rights must be reviewed at the **original product/file level**, even when a government site is public. Record each provider's exact release, original URL, licence, CRS, geometry, building-part semantics, build date, spatial subset, dedup crosswalk and source provenance before a user-model input approval.
5. Source identifiers for additional original national providers live canonically in [`landscape/sources-europe-national-building-gaps-20261108.json`](../../landscape/sources-europe-national-building-gaps-20261108.json). Previously catalogued original sources remain canonical in [european-building-registers](../../landscape/sources-european-building-registers.json), [validation-context](../../landscape/sources-europe-building-validation-context.json), [building-attribute-discovery](../../landscape/sources-europe-building-attribute-discovery.json) and [cross-domain-exposure-enrichment](../../landscape/sources-cross-domain-exposure-enrichment.json). This is a **narrative country-gap audit**, not a second source-of-truth registry.

## All 51 scope countries

| ISO / country | EUBUCCO v0.2 | Best primary original national / regional source or fallback | Access evidence | Unresolved limitation |
|---|---:|---|---|---|
| AL Albanien | Nein | [ASIG / ASHK cadastral buildings](https://geoportal.asig.gov.al/en/node/3372) | Geoportal/Teilbestand | Nur bearbeitete Katasterzonen; kein vollständiger Bulk-Nachweis |
| AD Andorra | Nein | [IEA Situació d’edificis](https://www.iea.ad/situacio-d-edificis) | Historischer Download | Polygon-Archiv auf Basis von Luftbildern 1995, nicht aktuell |
| AM Armenien | Nein | [National Geoportal / Kadaster-Komitee](https://www.cadastre.am/en/improvement/improvement3) | Geoportal | Gebäudelayer und freie Downloadrechte nicht bestätigt |
| AT Österreich | Ja | [BEV INSPIRE; Landes- und Stadtportale](https://www.bev.gv.at/Services/Geoinformationsdienste/INSPIRE-Geodatendienste/INSPIRE-Downloaddienste.html) | Dienst/Vertrag | Produktentgelte/Registrierung abhängig vom Produkt; Wien eigene 3D-Daten |
| AZ Aserbaidschan | Nein | [State Service on Property Issues](https://emlak.gov.az/mapmodule/) | Kartenviewer | Kein frei lizenzierter Gebäudemassendownload nachgewiesen |
| BY Belarus | Nein | [National Cadastral Agency (PKK)](https://www.nca.by/services/resources-services/publichnaya-kadastrovaya-karta/) | Kartenviewer | Nur Viewer nachgewiesen; Lizenz und Export ungeklärt |
| BE Belgien | Ja | [Flandern Gebouwenregister; Brüssel UrbIS; Wallonie PICC](https://geo.api.vlaanderen.be/Gebouwenregister/ogc/features/v1/) | Regionale API | Drei regional verschiedene Geometrien, Lizenzen und Objekt-IDs |
| BA Bosnien und Herzegowina | Nein | [Katastar.ba / FBiH](https://www.katastar.ba/servisi) | Regionalportal | FBiH ist nicht ganz BiH; RS und Brčko fehlen |
| BG Bulgarien | Ja | [Cadastre Agency INSPIRE Building service](https://inspire.cadastre.bg/arcgis/rest/services/Building/MapServer/exts/InspireView/service) | INSPIRE-Dienst | Viewer/Feature-Dienst und nationale Downloadrechte prüfen |
| HR Kroatien | Ja | [DGU INSPIRE Buildings WFS & ATOM](https://geoportal.dgu.hr/cms/en/data-and-services/) | OGC/ATOM | Amtlicher öffentlicher WFS; Objektabdeckung/Rechte pro Datei prüfen |
| CY Zypern | Ja | [DLS INSPIRE Buildings](https://www.data.gov.cy/el/dataset/ktiria-inspire) | INSPIRE-Dienst | Geografische Teilabdeckung/Status und Downloadrechte prüfen |
| CZ Tschechien | Ja | [ČÚZK RÚIAN Gebäude](https://vdp.cuzk.gov.cz/vdp/ruian) | Register/Download | Registeridentität vs tatsächlicher Footprint prüfen |
| DK Dänemark | Ja | [Datafordeler BBR Buildings & Dwellings](https://datafordeler.dk/dataoversigt/bygnings-og-boligregistret-bbr/bbr-graphql/) | Register/API | Authentifizierung, Adresseinheiten und Gebäude-IDs trennen |
| EE Estland | Ja | [Estonian Geoportal BU; EHR](https://www.geoportaal.ee/eng/INSPIRE/INSPIRE-services/BU-Buildings-p762.html) | INSPIRE/API | EHR-Klassen, Status und WFS-Rechte prüfen |
| FI Finnland | Ja | [SYKE Ryhti completed-building data](https://ryhti.syke.fi/en/front-page/services/) | OGC/Bulk | Tägliche CSV/JSON-Daten; gesondert von NLS-Topografiedaten |
| FR Frankreich | Ja | [RNB + IGN BD TOPO + BDNB](https://www.data.gouv.fr/datasets/referentiel-national-des-batiments) | Register/Bulk | RNB-ID Crosswalk und Einheiten vs Gebäude prüfen |
| GE Georgien | Nein | [NAPR NSDI Registered Building](https://nsdi.gov.ge/en/geoportal) | Geoportal/Layer | Gebäudelayer gelistet; Vollständigkeit, Rechte, umstrittene Gebiete prüfen |
| DE Deutschland | Ja | [AdV LoD2/ALKIS nach Bundesland](https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=lod2) | Landesdownloads | Frei je Bundesland, nationales BKG Zentralprodukt separat lizenziert |
| GR Griechenland | Ja | [Hellenic Cadastre INSPIRE](https://www.gov.gr/en/services/1001183/geopule-geokhorikon-dedomenon-inspire-ellenikou-ktematologiou) | Geoportal | Gebäudeflächenprodukt nicht ausdrücklich verifiziert; Katasterparzellen ≠ Gebäude |
| HU Ungarn | Ja | [Lechner Buildings](https://data.lechnerkozpont.hu/en/datasets/buildings) | Katalog/Vertrag | Katalog nachgewiesen; voller lizenzierter Export unbestätigt |
| IS Island | Nein | [IS 50V Buildings](https://www.natt.is/en/resources/geospatial-data/base-map-data) | Vektordownload | Topografische Generalisierung 1:50.000, keine Katasterparität |
| IE Irland | Ja | [Tailte Éireann HVD Buildings](https://data.gov.ie/dataset/high-value-dataset-buildings1) | INSPIRE/HVD | Geometrie/Downloadlizenz prüfen; Nordirland separat |
| IT Italien | Ja | [Piemonte BDTRE Building WFS](https://www.geoportale.piemonte.it/geonetwork/serv/api/records/c_l219:5737e8a3-0804-45d2-bfcd-5e318c3155f2) | Regionale Dienste | Regionale Unterschiede; Grundstückskatasterschnittstelle ≠ Gebäude |
| KZ Kasachstan (europäischer Teil) | Nein | [National geospatial portal](https://map.gov.kz/account/login/) | Portal/Registrierung | Keine europateilspezifischen amtlichen Gebäudepolygone verifiziert |
| XK Kosovo | Nein | [Kosovo Cadastral Agency Geoportal](https://geoportal.rks-gov.net/en) | Kartenviewer | Kein offener Massendownload verifiziert; separat von Serbien geführt |
| LV Lettland | Ja | [VZD Ēkas (INSPIRE)](https://data.gov.lv/dati/dataset/ekas-inspire) | INSPIRE-Dienst | WFS-Layer und Rechte mit Originaleinträgen prüfen |
| LI Liechtenstein | Nein | [Gebäude- und Wohnungsregister](https://opendata.swiss/en/dataset/gebaude-und-wohnungsregister-liechtenstein) | Register | Gebäuderegister ist nicht zwingend gebäudeflächengetreuer Polygonbestand |
| LT Litauen | Ja | [Lithuanian INSPIRE Buildings](https://www.inspire-geoportal.lt/geonetwork/srv/api/records/3722b45f-5fa0-4f60-8c6f-c27f69619b1e) | INSPIRE-Dienst | Original-Geometrie-Download und Rechte noch zu prüfen |
| LU Luxemburg | Ja | [ACT BD-L-BATI3D](https://data.public.lu/en/datasets/base-de-donnees-nationale-des-batiments-3d-2023/) | GeoPackage/3D | Regionen/Modelljahre und fehlende Kleinbauwerke unterscheiden |
| MT Malta | Ja | [Malta INSPIRE Spatial Data Download](https://www.servizz.gov.mt/en/Services/web-00506) | Antragsverfahren | Geodatenentnahme kann Antrag und Nutzungsvereinbarung erfordern |
| MD Moldau | Nein | [IP CBI cadastre GeoServer](https://map.cadastru.md/geoserver/index.html) | OGC-Server | Anonymer WFS-Server bestätigt, Gebäude-FeatureType nicht verifiziert |
| MC Monaco | Nein | [OpenStreetMap/Overture Fallback](https://download.geofabrik.de/europe.html) | Kein amtlicher Bulk-Nachweis | Keinen amtlichen eigenständigen Gebäudedownload gefunden |
| ME Montenegro | Nein | [Geoportal CG](https://geoportal.co.me/geoportal/geoportal_eng.html) | Kartenviewer | Katasterkarten, aber GebäudewFS/Downloadrecht unbestätigt |
| NL Niederlande | Ja | [Kadaster BAG / PDOK](https://api.pdok.nl/kadaster/bag/ogc/v2) | Register/API | Gebäude-ID vs Adresseinheit, 3DBAG gemeinsame BAG-Linie |
| MK Nordmazedonien | Nein | [AREC INSPIRE Buildings OGC](https://gisserver.gdi.mk/arcgis/rest/services/INSPIRE/Buildings/OGCFeatureServer/conformance?f=html) | OGC-Service | Conformance kein Beweis für vollständigen Download |
| NO Norwegen | Ja | [Kartverket FKB-Bygning](https://kartkatalog.geonorge.no/metadata/fkb-bygning/8b4304ea-4fb0-479c-a24d-fa225e2c6e97) | Kataster/Restricted | Kommerzielle Nutzung kann Vertrag/Entgelt erfordern |
| PL Polen | Ja | [GUGiK EGiB official buildings 2026](https://www.gov.pl/web/gugik/budynki-z-egib-dostepne-do-pobrania-w-serwisie-wwwgeoportalgovpl) | GeoParquet/GPKG | Bundesweite Lieferung beruht auf teils unterschiedlichen Kreis-WFS |
| PT Portugal | Ja | [Base Geográfica de Edifícios](https://dados.gov.pt/pt/datasets/base-geografica-de-edificios/) | Amtliches Dataset | Klassendefinition und Abdeckung Madeira/Azoren prüfen |
| RO Rumänien | Ja | [ANCPI INSPIRE Geoportal](https://geoportal.ancpi.ro/inspireview/rest/services) | Nationalportal | Gebäude-Footprints und freie Downloadrechte nicht nachgewiesen |
| RU Russland (europäischer Teil) | Nein | [Rosreestr / nationale räumliche Datenplattform](https://rosreestr.gov.ru/) | Katasterportal | Aktuelle Gebäudedaten-API/Export, Jurisdiktion und Rechte offen |
| SM San Marino | Nein | [Staatliches Kataster MapServer](https://mappeonline.pa.sm/arcgis/rest/services/Cartografia/catasto_GR/MapServer) | GIS-Kartenviewer | Keine belastbar freie Gebäudepolygon-Massenlieferung bestätigt |
| RS Serbien | Nein | [GeoSrbija Buildings WFS](https://metakatalog.geosrbija.rs/geonetwork/srv/api/records/a2d6936c-2b95-42cf-b55f-d5fbff7da19d) | INSPIRE-Metadaten | WFS-Zugriff/Abdeckung separat prüfen; Kosovo separat |
| SK Slowakei | Ja | [GKÚ INSPIRE HVD Buildings](https://www.skgeodesy.sk/geoportal-en/inspire/download-data/) | GPKG/GML/GDB | Offizielle CC BY 4.0 Downloadseite, Release-ID/Schema noch prüfen |
| SI Slowenien | Ja | [GURS Real estate cadastre](https://eprostor.gov.si/imps/srv/api/records/9a8fd241-9162-407c-94e7-c98e05766881/formatters/xsl-view?portalLink=&view=inspire) | WFS/Kataster | OGC-Layer, IDs, Gebäude vs Einheit und Nutzungsrecht prüfen |
| ES Spanien | Ja | [Dirección General del Catastro Buildings](https://www.catastro.hacienda.gob.es/webinspire/index_eng.html) | INSPIRE WFS/ATOM | Regionale Katasterausnahmen und Objektidentitäten beachten |
| SE Schweden | Ja | [Lantmäteriet Building Download](https://www.lantmateriet.se/en/geodata/our-products/product-list/building-download-inspire) | INSPIRE-Download | Produktbezogene Rechte prüfen; allgemeine Open-Data-Aussage nicht automatisch für alle Produkte |
| CH Schweiz | Ja | [swisstopo swissBUILDINGS3D](https://www.swisstopo.admin.ch/en/landscape-model-swissbuildings3d-3-0-beta) | 3D/Register | EGID-Abdeckung und Beta-Geltungsbereich variieren |
| TR Türkei (europäischer Teil) | Nein | [TUCBS National Geographic Information System](https://tucbs.gov.tr/) | Geoportal | Gebäudepolygon-Export/Lizenz und Europateil-Filter nicht verifiziert |
| UA Ukraine | Nein | [National Spatial Data Infrastructure / urban cadastre](https://nsdi.gov.ua/) | Nationalportal | Gebäudefeatures, Zugänge und territoriale Abdeckung kriegsbedingt zu verifizieren |
| GB Vereinigtes Königreich | Ja | [OS OpenMap Local + OSNI Fusion (NI)](https://osdatahub.os.uk/downloads/open/OpenMapLocal) | Open/Restricted | OpenMap Local generalisiert GB; OSNI Fusion separat lizenziert |
| VA Vatikanstadt | Nein | [OpenStreetMap/Overture](https://www.openstreetmap.org/) | Nur OSM-Fallback | Kein amtlicher veröffentlichter Gebäudedownload verifiziert |

## Additional European geographic territories (not included in 51)

| Territory | Evidence lead | Note |
|---|---|---|
| Åland Islands | [Åland open data](https://www.regeringen.ax/) | Finland-linked territory; Ryhti and NLS mainland assumptions not sufficient to claim identical Åland content |
| Faroe Islands | [Umhvørvisstovan building register](https://www.us.fo/kort/bygningsskra/) | Separate Faroese building registry; OGC/download/rights review needed |
| Greenland | [Greenland GIS portal](https://nunagis.gl/) | Part of the Danish realm but geographically outside continental Europe; building access not reviewed |
| Gibraltar | [Gibraltar government GIS](https://viewers.geoportal.gov.gi/) | Government map viewer does not imply licensed building-vector download |
| Isle of Man | [Isle of Man government](https://www.gov.im/) | No verified official publicly downloadable building polygon product in this audit |
| Jersey | [Jersey Digital Mapping Service](https://www.gov.je/PlanningBuilding/JerseyMappingService/Pages/Digital.aspx) | State mapping services; contract/asset scope review needed |
| Guernsey | [States of Guernsey Digimap](https://www.digimap.gg/) | Cadastral map access/rights to verify, not GB OS OpenMap Local by default |

## Recommended provider-byte pilots and next gates

| Priority | Pilot | Why it matters | Minimum admission blocker |
|---|---|---|
| P0 | **Poland GUGiK EGiB 2026** | Official nationwide GeoParquet/GPKG (distinct from BDOT10k) | Exact country archive URL, hash, CRS, per-county coverage, licence |
| P0 | **Slovakia GKÚ Buildings GPKG** | Official CC BY 4.0 original full-country downloadable vector source | Original ZIP hash, schema, building IDs/parts and counts |
| P0 | **Finland Ryhti** | Daily updated completed buildings in original CSV/JSON; effective historical/ID test | Actual bytes, scheme/version, completion status and geometry fields |
| P1 | **Croatia DGU WFS** | Government original INSPIRE buildings, machine-readable | WFS bounded read, licence/coverage and source object meaning |
| P1 | **Iceland IS50V** | Open non-EUBUCCO geography | Generalisation, actual geom class, open licence |
| P1 | **Albania / North Macedonia / Serbia** | Real national building layers outside EUBUCCO | Live anonymous WFS/OGC GetFeatures; exact regional coverage; reuse rights |
| P1 | **Liechtenstein** | National building register outside EUBUCCO | Geocoding/shape, units-vs-buildings, original licence |
| P2 | **Moldova, Georgia, Montenegro, Bosnia** | Fills eastern/south-east gaps | Viewer vs actual original feature downloads and rights |

**Hard scientific guards:** a building footprint is not an insured location; a dwelling or cadastral point need not equal one footprint; the same upstream government building may appear in EUBUCCO, Overture and OSM; do not infer actual carrier shares/TIV or calibration from area or map visibility alone. For potentially restricted or conflict-area sources, avoid automatic access where terms/security are unclear. No external provider data or rights-cleared assets are committed here.
