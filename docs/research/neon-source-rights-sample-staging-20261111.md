<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Insurance Neon source rights and bounded sample staging — 2026-11-11

## Scope and actual evidence

The public repository is the canonical source for research source identities. Its fixed-commit source-register audit was executed separately on GitHub Actions:
- [All-source and reviewed API workflow](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43070500887), SHA `a40bd05987169aa3594274eff9771a8627276aeb`: **707** source records audited (**692** landscape candidates in **107** JSON shards; **15** existing admitted manifests) and **68** source-access contracts validated.
- **11/11** explicitly reviewed, bounded, anonymous live probe jobs completed successfully. These are provider-specific capabilities, **not** blanket commercial-use, sample-download or model-admission approvals.
- The completed per-record JSON artifact is available in the workflow (artifact `all-source-coverage-audit`).

The separate insurance Neon database `insurance-risk-core` (not the Pokémon database) now includes the following **research-only** objects:

| Neon relation | Purpose |
| --- | --- |
| `research.source_candidate_review_v0` | All **692** canonical candidate records and their original notes, provider, authoritative URL, access hints, source-revision date, and unmodified `rights_review_status=not_reviewed` provenance |
| `research.source_sample_v0` | Narrow, provenance-bound sample rows: source URL, received provider SHA-256, extracted sample SHA-256, license evidence, exact scope, UTC retrieval, no CAT-model admission |
| `research.source_candidate_triage_v0` | Conservative first-pass **signals**, not legal decisions: restrictions/gates, possible open-license citations, or no evidence |
| `research.all_source_inventory_v0` | 692 research candidates + 15 existing manifest records, retaining distinct record types |

These tables **do not** change `registry.source_record`, source manifests, prior legal decisions, or CAT-model input approvals. A DB-level stored sample is not a Git/raw-data release or evidence of a scientifically calibrated hazard/exposure/financial loss.

## Current conservative triage

| Status | Count | Interpretation |
| --- | ---: | --- |
| No clear license signal | 519 | Find original-provider terms, exact version, dataset and API/service rights |
| Possible open-license signal | 126 | Existing source notes mention a license; independently verify original terms and third-party layers |
| Restrictions or access-gate signal | 43 | Treat as blocked for new samples until the exact gate is resolved |
| Source-scoped commercial reuse independently verified | 4 | GFZ Kp, GDW v1.0, USGS 3DEP, ESA WorldCover 2021 v200; attribution/terms and asset scope still apply |

This view gives **692/692** records a queue category, not **692 approved licenses**. Unknown or incompatible rights never default to commercial approval. `commercial_reuse_verdict=allowed_verified` is currently restricted to four exact products.

## Initial seven original-provider samples written to Neon (no provider bytes in Git)

| Source / research-only sample | Scoped license and evidence | Original response SHA-256 |
| --- | --- | --- |
| GFZ definitive Kp, 2024-01-01, eight 3-hour values | [GFZ source CC BY 4.0](https://kp.gfz.de/) | `f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a` |
| geoBoundaries **DEU ADM1** metadata, 16 units | [German Data Licence BY 2.0](https://www.govdata.de/dl-de/by-2-0); Germany-specific, **not** blanket worldwide gbOpen clearance | `65af06f80e837028997c396d2c67d74fb1e1752d884e9a0638d5c736ee8c345a` |
| NOAA CO-OPS San Francisco station 9414290, 2026-01-01, first six water-level values, GMT and MLLW metres | [NOAA general reuse caveats](https://www.noaa.gov/office-education/outreach-communication/faq) and [CO-OPS API limits](https://www.tidesandcurrents.noaa.gov/web_services_info.html); no implied official validation | `3ae940b4f9632b1e37fec1009381f85e38fa961a4cea04dc21a1939ca47ae295` |
| STORM IBTrACS v4 **DataCite DOI metadata only** | [DataCite CC0 metadata policy](https://support.datacite.org/docs/datacite-data-file-use-policy) **does not cover linked original storm-track files** | `90bbb620c7e04632e45b5c86c2998b3b023a55d246b56c2c7f09cc1a66c62f66` |
| Global Dam Watch v1.0 Figshare files/version metadata | [GDW original publisher CC BY](https://www.globaldamwatch.org/database); archive GIS bytes not downloaded | `16739c79caa320eb0be27a0486040efb5fdcf02db4416a1493d6f9fac93b77ef` |
| USGS 3DEP Florida S1M catalogue metadata | [USGS public-domain 3DEP](https://www.usgs.gov/3d-elevation-program/); actual elevation raster not downloaded | `a4f2397d06242e702d63ca627379daadeb915d9bdd3c378dbcc761cc7a325c48` |
| ESA WorldCover 2021 v200 N48E009 original TIFF 4096-byte header metadata (no pixels stored) | [ESA original source CC BY 4.0](https://esa-worldcover.org/en/data-access), mandatory WorldCover/Sentinel attribution; GeoTIFF partial-header evidence only | `a74fc1ff4733c3afff09328e014c0731eba2f1912f3f5cbc330ed0700f3f3529` |

The original-response hashes above match the prior successful fixed GitHub Actions probes. Any stored subset has its own derived SHA in Neon; all seven sample rows are explicitly `model_input_approved=false`. Original raw response retention is permitted only by the source-scoped decision, and no individual building coordinates, insurer records, confidential portfolios, large archives, licensed downstream vendor assets, or provider secrets were added.

## Required next causal steps

1. Process the 126 open-license *signals* via exact provider/version and third-party checks; do not mass-promote labels based on string matches. Resolve the 43 restriction signals separately.
2. For each cleared exact product, select one narrowly bounded download and verify source identity, response byte SHA-256, media/format, units, timestamps, license and attribution. Keep data that is not freely redistributable out of Git and any unauthorized Neon sample table.
3. Cover the remaining 520 entries through original-provider access/terms research, not blind URL crawling. A source with no valid contract remains documentation-only.
4. Add actual hazard/exposure model-admission tests **after** rights and source-specific scientific checks. Public metadata availability is not evidence of usable catastrophe losses.

No provider data, secrets or database credentials are present in this document.


## Fortsetzung: zehn weitere Quellenproben und Rechteprüfung (11.11.2026)

Dieses Update ergänzt die sieben oben dokumentierten Samples. **Neon-Live-Prüfstand:** **707** Registereinträge, **692** Kandidaten, **17** source-scoped Samples, **11** kommerziell für das **exakt bezeichnete Produkt** geprüfte Rechteentscheidungen, **0** für CAT-Modelle zugelassene Samples.

Die neuen zehn Zeilen sind ausschließlich im getrennten Forschungsbereich `research.source_sample_v0` abgelegt, und jeder Receipt-Hash ist der SHA-256 der **Originalanbieter-Antwort**, nicht die Hashsumme des gekürzten Neon-Datensatzes.

| Sample-ID | Quelle | Gespeicherter Inhalt | Versionierte Lizenz/Scope | Original-Antwort-SHA-256 |
| ---: | --- | --- | --- | --- |
| 8 | `dlr.wsf.2019` | Metadaten | CC BY 4.0 | `678c469c311e536b65b8f5cc27fe77bc2423651a6fc26c9650b343ba77bd2981` |
| 9 | `ec-jrc.ghsl.ghs-built-s.r2023a` | Metadaten | CC BY 4.0 | `f20723519a580fb35b3499870f0b1baea54f483195105416e547f0014f1610d2` |
| 10 | `ec-jrc.ghsl.ghs-built-v.r2023a` | Metadaten | CC BY 4.0 | `f20723519a580fb35b3499870f0b1baea54f483195105416e547f0014f1610d2` |
| 11 | `eu.jrc.eurocropsv2.gsa-parcels` | Metadaten | JRC EuroCropsV2 release CC BY 4.0; national input rights review pending | `416bdfcb29464682670bbdc050ee8cca0a39f4afeadfeed4f8d1a3fb5211e688` |
| 12 | `emsc.seismicportal.fdsn-event` | Messdaten | CC BY 4.0 | `0d6a957864b2eb47e8de01520bf25d617970637763ae4740d6a6c69ec0ea9b28` |
| 13 | `wsv.pegelonline.elbe-dresden-discharge.2020-2023` | Metadaten | DL-DE Zero 2.0 | `afaeea603a827482888f6fd4e68b4152ac34ea3dc9598e05b14f513515ae2a0e` |
| 14 | `fao.cropgrids.2020.global` | Metadaten | CC BY 4.0 | `283b2bcdf570e4032327c52a44325a79dd380eaf96ca120c9332733c8ad63c16` |
| 15 | `dlr.eoc.wsf-tracker.2016-2026` | Metadaten | CC BY 4.0 | `b5bb0f1bef6dac208ced9698c1815ba135e36562ee9440bf4e412f892fa8e507` |
| 16 | `dlr.wsf.evolution.1985-2015` | Metadaten | CC BY 4.0 | `f4fe5243a3563594e523d2f368cdf7088d71e3120f586d44c3253160cf32e3a8` |
| 17 | `dlr.eoc.wsf-3d-material-stock.2024` | Metadaten | CC BY 4.0 | `e586b05efc0d70663cf44b2c55feed3891904960bcb72398f965df4557669d69` |

**Exakte originale Lizenz-/API-Belege und fachliche Grenzen:**

- **DLR WSF 2019:** Offizieller [Produktkatalog](https://geoservice.dlr.de/web/datasets/wsf_2019) und die originale STAC-Collection `WSF_2019` lizenzieren das 10-m-Siedlungsraster unter **CC BY 4.0**. Kein Gebäudekataster, keine Einzelgebäudewerte und keine Originalrasterpixel in der DB.
- **EC-JRC GHSL BUILT-S/BUILT-V R2023A:** Beide exakt benannten [BUILT-S](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/copyright.txt)- und [BUILT-V](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_V_GLOBE_R2023A/copyright.txt)-Copyright-Dateien datieren auf 2026-03-05 und erklären CC BY 4.0 mit Nennung/Änderungskennzeichnung. In Neon liegen **nur die Rights-Metadaten/Original-Hash-Receipts**, keine Rasterpixel: BUILT-S ist Fläche (`m²`), BUILT-V Volumen (`m³`), beides **kein TIV**.
- **JRC EuroCropsV2:** Die originale [Copyright-Datei](https://jeodpp.jrc.ec.europa.eu/ftp/public/JRC-OpenData/DRLL/EuroCropsV2/copyright.txt) gibt CC BY 4.0 für die JRC-Veröffentlichung an. Die [Dateiliste](https://jeodpp.jrc.ec.europa.eu/ftp/public/JRC-OpenData/DRLL/EuroCropsV2/all_gpqt_files.csv) wurde nach der Header-/Dateinamensprüfung **auf zwölf Zeilen begrenzt**. Nationale Zahlstellen und genaue Parquet-Versionen/Parzellenrechte sind **nicht** vollständig geklärt; `commercial_reuse_verdict=unresolved`, keine Parzellengeometrien/Personendaten gespeichert.
- **EMSC FDSN Event:** Ein originaler, schmaler [Ein-Ereignis-Abfrageweg](https://www.seismicportal.eu/fdsn-wsevent.html) liefert GeoJSON-Metadaten und ein einzelnes öffentliches Erdbebenereignis. Der Service erklärt ausdrücklich **CC BY 4.0** mit EMSC-CSEM-Attribution. Für eine Hazard-/Loss-Kalibrierung fehlen Unsicherheit, Zensierung und Vollständigkeit.
- **WSV PEGELONLINE:** Die [Dresden/Elbe-Metadaten](https://pegelonline.wsv.de/webservice/downloads) stammen aus der freigegebenen stationären REST-v2-Routenkennung. Die WSV nennt **DL-DE Zero 2.0**. **Keine** Abflussmessreihe geladen; amtliche Rohdaten können ungeprüft sein.
- **CROPGRIDS Figshare v9:** Die [exakte Figshare-Datensatzversion](https://figshare.com/articles/dataset/CROPGRIDS/22491997) `10.6084/m9.figshare.22491997.v9` erklärt CC BY 4.0; gespeichert wurden DOI und ein Verzeichnis mit **sechs veröffentlichten Datei-Einträgen**, keine NetCDF-Werte. Die eigenständigen FAO/CGIAR-Derivate von 2026 besitzen andere Versions-/Dateiidentitäten, weshalb die **familienweite** kommerzielle Nutzung `unresolved` bleibt.
- **DLR WSF Tracker:** [STAC `WSF_TRACKER`](https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_TRACKER?f=json) CC BY 4.0. Zeitstempel der Siedlungserkennung sind **keine** gesicherten Baujahre; Source-Cooperative-GeoZarr/COG-Georeferenzierung darf nicht ohne Abgleich zusammengeführt werden.
- **DLR WSF Evolution:** [STAC `WSF_Evolution`](https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_Evolution?f=json) CC BY 4.0. Die historische Datenqualität (IDC-Score) ist bei jeder echten Modellnutzung erforderlich.
- **DLR WSF 3D Material Stock:** [STAC `WSF3D_MATSTOCK`](https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF3D_MATSTOCK?f=json) CC BY 4.0. Werte wären modellierte kg Material pro 90-m-Pixel, nicht Gebäude-TIV, Gebäudepreise oder tragwerksgeprüfte Materialwerte.

**Aktuelle Lizenz-Triage (692 Kandidaten, keinerlei automatische Freigabe durch Textmuster):**

- `no_clear_licence_signal`: **519**.
- `open_licence_claim_not_verified`: **119**.
- `restrictions_or_access_gate_signal_review`: **43**.
- `source_scoped_rights_verified`: **11**.

**Konkrete Blocker** bleiben bestehen: `ec-jrc.ghsl.ghs-obat.r2024a` wegen widersprüchlicher ODbL/CC-BY-Ressourcenetiketten; `usgs.anss.comcat` wegen unterschiedlicher Beiträger-Rechte und ungeklärter API-Automatisierungsbedingungen; `eurostat.gisco.census-population-grid.2021` wegen dokumentierter statischer, aber noch nicht genehmigter automatisierter V3-ZIP-Route; `eu.jrc.eurocropsv2.gsa-parcels` und `fao.cropgrids.2020.global` wegen überprüfungsbedürftiger Quell-/Derivatversionen. Keine dieser Lücken darf als Probenfreigabe interpretiert werden.

**Reproduzierbare DB-Abnahme (Neon `insurance-risk-core`):**

```sql
SELECT (SELECT count(*) FROM research.all_source_inventory_v0) AS all_sources,
       (SELECT count(*) FROM research.source_sample_v0) AS sample_count,
       (SELECT count(*) FROM research.source_candidate_review_v0
        WHERE commercial_reuse_verdict='allowed_verified') AS source_scoped_licensed,
       (SELECT count(*) FROM research.source_sample_v0
        WHERE model_input_approved) AS model_input_approved;
SELECT source_id, sample_kind, provider_response_sha256, licence_evidence_url,
       model_input_approved
FROM research.source_sample_v0 ORDER BY sample_id;
```

Es wurden **keine Zugangsschlüssel**, Originalraster, nationalen Parzellen oder Versicherungsdaten in Git abgelegt. Die Quelleingänge sind nicht automatisch genehmigte wissenschaftliche Modellinputs.


### Integritätskorrektur und dauerhafte DB-Sicherung

Die abschließende Prüfung `sample_sha256 = SHA256(sample_json::text)` zeigte bei den Altproben **GFZ Kp** und **geoBoundaries DEU ADM1** einen Methodenfehler: Der `sample_sha256` enthielt ursprünglich den SHA der **unformatierten Originalantwort**, nicht den SHA der von PostgreSQL normalisierten JSONB-Probe. Diese zwei abgeleiteten Sample-Hashfelder wurden korrigiert; `provider_response_sha256`, Datenwerte und Lizenznachweise sind unverändert. Ergebnis: **17/17** gültige kanonische Sample-Hashes.

Die Research-Tabelle `research.source_sample_v0` hat dafür jetzt den datenbankseitigen Constraint:

```sql
CONSTRAINT source_sample_canonical_jsonb_sha256_check
CHECK (sample_sha256 =
  encode(sha256(convert_to(sample_json::text, 'UTF8')), 'hex'))
```

Die Originalantwort-SHA-256-Receipts dienen der Upstream-Byte-Identität. Die **eigenen** Sample-Hashes sichern unabhängig davon den verarbeiteten DB-Inhalt. Dieser Unterschied ist verpflichtend für alle weiteren Imports.

## Fortsetzung II: DLR WMS-Minikarten und Dresden Q, 11.11.2026

Neon-Live-Abnahme: 707 registrierte Quellen, 692 Landschaftskandidaten, 25 Samples aus 18 Quellenkennungen; 12 produktbezogene kommerzielle Lizenzprüfungen. Die SHA-256-Constraint besteht für 25/25 JSONB-Samples; null Samples sind als produktive CAT-Modelleingaben zugelassen.

### Neu gespeicherte Samples

| Neon sample_id | Quellkennung | Layer / Station | Art | SHA-256 der Originalanbieter-Antwort |
| ---: | --- | --- | --- | --- |
| 18 | dlr.wsf.2019 | WSF_2019 | geospatial_preview | b1da1fab04a2fa83fe4f848797ab8fd7e7a992a747e4cdac680d56f66c9b54d1 |
| 19 | dlr.eoc.wsf-tracker.2016-2026 | WSF_TRACKER | geospatial_preview | 4f8c22ef1a30dfccaa54866c714f3a6392caf19a165e874574c3038c8b5b771d |
| 20 | dlr.wsf.evolution.1985-2015 | WSF_Evolution | geospatial_preview | d7b130996240a51a3deae76826384b6afd70002407b21934710c1307d59333be |
| 21 | wsv.pegelonline.elbe-dresden-discharge.2020-2023 | DRESDEN | observed_values | df2196186aae192d0ccf7cc867451094f472a223c314885050241919d7e38a4d |
| 22 | dlr.wsf.3d.v02 | WSF3D_V02_BUILDINGAREA | geospatial_preview | 00c740303c7a6bd05f4a01eecf6b81e4c43c9f96f598cc1cbdc55bb663b6ae52 |
| 23 | dlr.wsf.3d.v02 | WSF3D_V02_BUILDINGVOLUME | geospatial_preview | 46d9256b651dcab2414a561c495d0c20d6d73df9ea2c307a60869172e9d9aed4 |
| 24 | dlr.wsf.3d.v02 | WSF3D_V02_BUILDINGFRACTION | geospatial_preview | 9604323c9d43543eb0d83cb0219df73bef60634465149c6da955b59f5ed636d1 |
| 25 | dlr.wsf.3d.v02 | WSF3D_V02_BUILDINGHEIGHT | geospatial_preview | 07055b96dd34d99edb559c9d3d7354bc3d2fa922cd8c43cf2b502e5cccf4f6c3 |

Die sieben DLR-Karten sind echte gerenderte 32×32-PNG-Antworten des originalen DLR-WMS, keine nativen TIFF-Pixel oder numerischen Gebäudeattribute. Eingefrorene Requestparameter: HTTPS geoservice.dlr.de/eoc/land/wms, WMS 1.1.1, BBOX 11.52,48.10,11.60,48.18 (EPSG:4326, Lon/Lat), WIDTH=HEIGHT=32, FORMAT=image/png. Versioniert und rechtlich produktbezogen: WSF 2019, WSF Tracker, WSF Evolution und WSF 3D v02 (Area, Volume, Fraction, Height). DLR bestätigt CC BY 4.0 auf den jeweiligen offiziellen Produktseiten:

- https://geoservice.dlr.de/web/datasets/wsf_2019
- https://geoservice.dlr.de/web/datasets/wsf_tracker
- https://geoservice.dlr.de/web/datasets/wsf_evo
- https://geoservice.dlr.de/web/datasets/wsf_3d

Der neue GitHub-Actions-Probe mit festem Layer-Allowlist, No-Redirect-Gate, PNG-CRC-/IHDR-Prüfung und maximal 16 KiB je Antwort lief erfolgreich für **alle sieben** Layer. Alle **7/7** in Actions berichteten Response-SHA-256 stimmen mit den in Neon gespeicherten Mini-PNG-Originalbytes überein. Keine fremden PNG-Daten werden in Git gespeichert oder geloggt.

Beweis: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43084497058

**Wichtige WSV-Zeitgrenze:** Dresden Elbe Q wurde über die offizielle PEGELONLINE-API (DL-DE Zero 2.0) mit einem einzigen relativen P1D-Fenster abgerufen. Der 15-Minuten-Abfluss in m³/s lag als 95 Messungen vom 10. bis 11.11.2026 vor; genau die ersten 12 echten Werte sind als Sample #21 abgelegt. Der vorhandene Quellen-ID-Suffix 2020-2023 **ist dadurch nicht historisch validiert**. Rohmessungen bleiben provisorisch und sind kein Hochwasser-/Versicherungsverlustmodell. https://wasserstaende.de/webservice/guideRestapi

Rechte-Triage weiterhin offen: 118 positive, aber ungeprüfte Lizenzhinweise; 43 Restriktions-/Zugangssignale; 519 ohne eindeutige Lizenz; 12 exakt produktbezogen bestätigt. Externe Anbieter-Assets, TIV, personenbezogene Adressen oder Roharchive wurden nicht nach Git übernommen.

Die nächsten fachlichen Hürden sind die native pixelgenaue GeoTIFF-Probe mit CRS/NoData statt WMS-Farbbild, DWD-CDC Windböenwerte, und der GHS-OBAT ODbL/CC-BY-Lizenzkonflikt.

## Fortsetzung III: DWD CatRaRE 2026.01, erste echte Starkregen-Ereignisproben

Der neue DWD-CDC W3-Eta-v2026.01-Datensatz ist exakt quellenversioniert. Der 2026.01 DOI-Landingpage-Link zur CSV verweist fehlerhaft auf die veraltete Datei der 2025.01-Version (HTTP 404). Das echte offizielle Verzeichnis ist:

https://opendata.dwd.de/climate_environment/CDC/event_catalogues/germany/precipitation/CatRaRE_v2026.01/data/

Exakte CSV-Identität: CatRaRE_2001_2025_W3_Eta_v2026_01.csv; 12.410.601 Bytes laut Originalverzeichnis. Die aktuelle DWD-CDC-Lizenz lautet CC BY 4.0 mit Quellenvermerk (offizielle Nutzungsbedingungen https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf).

Ein anbietergebundener HTTP Range=bytes=0-4095 lieferte genau 4.096 Originalbytes; SHA-256 a3e02cb676b855390c0a9b69f41352c7c3dff74c7c25e2578727e8397f9d9b12. Der Ausschnitt enthält 67 originale semikolongetrennte CSV-Felder und mindestens drei vollständige historische Starkregenereignisse. Genau drei Zeilen liegen in Neon als Sample-ID 26 (observed_values), einschließlich W3-Eta-Version, KEY_FIELD/Event_ID und unveränderter Quellfelder. Der SHA-256 deckt NUR den 4-KiB-Ausschnitt ab. Der vollständige 12,4-MB-Quell-Digest, Polygone, RADKLIM-CRS, Zeitzone, wissenschaftliche Qualitätsgates, Modelladmission und T5-vs-W3-Deduplikation sind ausdrücklich weiterhin NICHT bestätigt.

Im kanonischen Quellenregister landscape/sources-observation-context.json wurde gezielt nur der W3-v2026.01-Kandidat korrigiert: tatsächlich erreichbarer Original-CSV-Pfad, Lizenznachweis, dokumentierter toter Landingpage-Link, 4-KiB-SHA, restriktiver Quell-/Versionsstatus, Rechte nach Originalprüfungsumfang als verified. Der entsprechende Neon-Quellkandidaten-Eintrag wurde an genau diesen neuen Forschungsstand angeglichen. Alle anderen Kandidaten bleiben unberührt.

Reproduzierbare GitHub-Prüfung: scripts/probe_dwd_catrare_w3_range_v0.py; tests/test_probe_dwd_catrare_w3_range_v0.py; .github/workflows/dwd-catrare-w3-range.yml. Vier Offline-Tests prüfen Identität, Version, CSV-Schema, HTTP 206 mit Content-Range, Domain, Weiterleitungen und 4-KiB-Limit. Die erste korrigierte Live-Action ist erfolgreich:

https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43085939447

Die Action bestätigt erneut den exakt gleichen Originalresponse-SHA-256 wie Neon. Keine Providerdaten in Git; kein offener Bulk-Download; kein CAT-Modellinput.

**Neon-Live-Stand nach diesem Schritt:** 707 kanonische Quellen, 692 Kandidaten; 26 Samples aus 19 unterschiedlichen Quellenkennungen; 13 exakt produktbezogen kommerziell geprüfte Kandidaten; 26/26 JSONB-Integritätsprüfungen; 0 CAT-modellzugelassene Samples. Lizenz-Triage: 118 positive Lizenzhinweise ohne Einzelprüfung, 43 Restriktions-/Zugangssignale und 518 ohne klare Lizenzsignale. Diese Gruppierungen belegen keinen automatischen Rechteentscheid.

## Fortsetzung IV: zwei gekoppelte CatRaRE-Releases und Abschlussprüfung

Der T5-Eta-v2026.01-Datensatz wurde getrennt von W3 anhand des echten Original-DWD-Verzeichnisses, der offiziellen DWD-CDC-CC-BY-4.0-Lizenz und des fixierten Produktnamens geprüft:

https://opendata.dwd.de/climate_environment/CDC/event_catalogues/germany/precipitation/CatRaRE_v2026.01/data/CatRaRE_2001_2025_T5_Eta_v2026_01.csv

Originaldatei-Länge laut DWD-Verzeichnis: 17.208.653 Bytes. Nur ein 4096-Byte-HTTP-Range wurde original abgerufen. Prefix-SHA-256: 5dc4b6f0dac14f0a442103b78c16f647556bd870898aabff6d9f62aa4534f542. 67 gültige CSV-Spalten, erste drei vollständige T5-Eta-Ereigniszeilen mit unveränderten Quellfeldwerten. In Neon Research als Sample #27, produktgenau mit CC BY 4.0 und Recherche-Sperre erfasst; keine vollständige Datei, keine Geometrie und keine unbewiesene TIV-/Loss-Information.

Im Originalquellenregister landscape/sources-observation-context.json wurden T5 und W3 jeweils einzeln von originalem not_reviewed auf verified für die exakte Datenlizenz angehoben. Beide Quellen bleiben **not_admitted**. Die Research-Quellrecords in insurance-risk-core wurden entsprechend aktualisiert.

Das jetzt zweimal variantenspezifische Werkzeug scripts/probe_dwd_catrare_w3_range_v0.py lässt ausschließlich die beiden festgelegten Quellen W3 und T5 zu und prüft vollständige HEAD/Range-Identität via HTTP 206, Content-Range in Version und Größe, exakt 4096 Bytes, 67 Spalten und drei Version-gerechte Originalereignisse. Der automatisierte GitHub-Actions-Lauf hat alle 5 Offline-Tests und beide externen 4-KiB-Abfragen bestanden; die Antwort-SHA stimmen bei **2/2** mit Neon überein:

https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43086921155

**Nicht unabhängige Ereignisse:** T5 und W3 beruhen auf demselben RADKLIM-RW v2017.002. Eine additive Zusammenführung würde potenziell Ereignisse doppelt zählen. Vor produktiver Gefahrensimulation: Ereignis- und Zeitüberlappung, Polygone und hydrologische Verluste unabhängig und mit einem definierten Event-ID-/Zeit-Schema prüfen.

**Neon-Endstand 11.11.2026:** 707 kanonische Quellen, davon 692 Forschungsquellen; 27 Samples von 20 unterscheidbaren Quellen; 14 produktbezogen lizenzgeprüfte Kandidaten; 27/27 JSONB-Hashchecks bestanden; 0 CAT-Modelleingaben zugelassen. Rechte-Triage: 118 potenzielle Lizenzen noch ungeprüft, 43 Zugang/Restriktionssignale und 517 ohne klare Lizenzhinweise.
