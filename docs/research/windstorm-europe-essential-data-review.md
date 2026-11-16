<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Welche Daten Windstorm Europe wirklich braucht

Stand: 14. November 2026. Ziel ist ein reproduzierbares, empirisch geprüftes
Modell europäischer außertropischer Sturmschäden. Ein „perfektes“ Modell ist
kein erreichbarer Nachweis: Beobachtungen, Gebäudeeigenschaften und seltene
Ereignisse bleiben unsicher. Prüfbare Abdeckung, Fehlergrenzen und unabhängige
Validierung sind die Abnahmekriterien.

## Umfang der Quellenprüfung

Der [vollständige Katalogscan](../../research/source_screening/windstorm_whole_chain.json)
liest sämtliche 110 JSON-Dateien unter `landscape/`: 702 Einträge, davon 296
mit mindestens einem Treffer für die Modellkette. Die übrigen 406 bleiben
sichtbar und sind nicht automatisch als irrelevant verworfen. Mehrfachnennungen
bleiben erhalten; 702 Einträge sind nicht 702 verschiedene Datensätze.
Der [Reader](../../scripts/screen_windstorm_model_sources.py) speichert
Dateihashes, Position, Quellen-ID, Anbieterlink, vorhandenen Rechte-/Zulassungsstatus
und die tatsächlich getroffenen Kategorien. Er vergibt keine Zulassung.

Dies ist ein vollständiger technischer Scan dieser Kataloge, keine vollständige
fachliche Einzelprüfung aller Provider und keine Suche in sämtlichen Repositories.
Quellen nur in Markdown, Manifesten oder anderen Datenbanken sind nicht vollständig
erfasst. Die folgende fachliche Bewertung priorisiert die bereits bekannten
zentralen Quellenfamilien und ergänzt einen aktuellen Anbieterabgleich.

## Benötigte Daten und Entscheidung pro Quellenfamilie

| Baustein | Bevorzugte Quellen / bestehende Kandidaten | Benötigter Inhalt und nächster Nachweis |
|---|---|---|
| Historische Ereignisse | C3S Enhanced Windstorm Service (EWS), ERA5/ARCO; CLIMK und XWS als Vergleich | Gemeinsame grenzübergreifende Ereignis-IDs, Tracks, genaue Zeitfenster, Auswahlregeln, vollständige Jahre inklusive Nullereigniszeiten. EWS-TRACK und TempestExtremes sind Alternativen; identische Stürme nicht doppelt zählen. |
| Lokale Windfelder | EWS native und statistisch verfeinerte Footprints; CLIMK/XWS | Böendauer, Messhöhe, Einheiten, Raster, Masken und Ereignisabgrenzung festlegen. Full-domain-Maxima können andere Stürme enthalten; decontaminated-Masken brauchen eine explizite Semantik. Fehlende Werte sind kein Nullwind. |
| Seltene Ereignisse / jährliches Risiko | WISC synthetische Ereignisse, eigenes späteres stochastisches Modell | Ensemble-Mitglied, Simulationszeit, Kalibrierungsvariante, Ereignisgewicht und saisonale Selektion. Keine Häufigkeit allein aus Dateianzahl oder nominalem Datumsbereich ableiten. |
| Windbeobachtungen | DWD, KNMI, Météo-France, MIDAS Open; ECA&D als weiterer Kandidat | Stationshistorie, Standort/Höhe, Instrument/Böendauer, Zeitzone, Qualitätsflags, fehlende Stunden und Original-/abgeleiteter Messwert. Mehrere Ereignisse und Länder; unabhängige Validierung von Kalibrierstationen trennen. |
| Lokale Geländewirkung | Copernicus DEM / FABDEM, WorldCover / CORINE, nationale Höhenmodelle | Gelände, Rauigkeit, Küstenlage und gegebenenfalls Abschattung. DEM/DSM unterscheiden; Auflösungsverfeinerung erzeugt keine gemessene Windinformation. Keine zusätzliche Geländekorrektur ohne Prüfung bereits enthaltener EWS-Korrekturen. |
| Gebäudegeometrie und Bestand | Nationale Register; EUBUCCO/Overture/OSM als harmonisierte Ergänzung; GHSL als Aggregatprüfung | Stabile Gebäude-ID, Geometrie, Nutzungsart, Fläche, Höhe, Baualter, Dachform/-material und Umbauten. Historischer versus heutiger Bestand; Dubletten und Abdeckungsfehler je Land quantifizieren. |
| Nationale Anreicherung | DE LoD2/ALKIS, NL BAG/3DBAG, FR RNB/BDNB/BD TOPO, UK EPC, PL BDOT10k, CZ RÚIAN, ES Catastro, CH swissBUILDINGS3D, DK BBR, FI NLS, NO FKB, SE Lantmäteriet | Version, Länderabdeckung, Rechte und Attributdefinitionen je Produkt prüfen. EPC ist kein vollständiges Gebäuderegister; fehlende Dachattribute nicht aus Baualter als Tatsache ableiten. |
| Wiederherstellungswerte | Nationale Baukosten nach Gebäudeklasse; Eurostat für zeitliche Fortschreibung; Huizinga/JRC nur als dokumentierter Proxy | Kosten pro Fläche, Bezugsfläche, Preisjahr, Währung, Steuern, regionale Unterschiede; Gebäude, Inhalt und Betriebsunterbrechung getrennt. Baukostenindex liefert keine absoluten EUR/m²; Verkaufspreise enthalten Boden und sind kein Ersatz. |
| Vulnerabilität | CLIMAAX/Feuerstein, WISC, Schwierz/CLIMADA als explizite Referenzen | Kurven mit benannten Klassen und Winddefinition; Anteil beschädigter Objekte versus Schadenhöhe; Streuung und gemeinsame Ereignisunsicherheit. Bekannte Klassen-/Gewichtungswidersprüche auflösen; nicht durch stumme Umordnung kaschieren. |
| Tatsächliche Schäden | EIOPA, GDV, nationale Versicherungsverbände/öffentliche Schadenstatistiken; ergänzend JRC RDH, EEA, EM-DAT | Ereignisdatum, Ort, gedecktes Risiko, Zahl der Schäden und versicherten Objekte, Werte, Selbstbehalte, Preisjahr und Meldeabdeckung. Sturm/Hagel- oder Sturmflut-Summen nicht ungeprüft als Windschaden verwenden. |
| Versicherungsverträge | Explizite Portfoliodaten oder klar markierte synthetische Verträge | Deckungen, Limits, Selbstbehalte, Stundenklauseln, Aggregation, Rückversicherung und Währungen. Marktstatistiken und Prämien sind keine Policen. Vertrauliche Daten bleiben außerhalb des öffentlichen Repos. |

Die größten Datenlücken sind damit **Ereignisfrequenz, länder-/gebäudeklassenspezifische
Schadenbeobachtungen mit Expositionsnenner und absolute Wiederherstellungskosten**.
Noch mehr Polygone oder generische Kurven lösen diese Lücken nicht.

## Aktueller Anbieterabgleich und Konsequenzen

### EWS als erste Route für die historische Basis

Die [aktuelle EWS-Beschreibung](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-reanalysis?tab=overview)
beschreibt 1940 bis heute, alle Jahreszeiten, monatliche Aktualisierung,
TRACK/TempestExtremes, 72-Stunden-Maxima sowie 0,25° und statistisch verfeinerte
0,016°-Raster. Die Footprint-Abdeckung beträgt 25°W–35°E, 30°N–70°N.
Das deckt nicht automatisch jedes als „Europa“ verstandene Gebiet ab.
Zielgebiet und ausgeschlossene Vermögenswerte müssen explizit sein.
Die Katalogauswahl hat meteorologische Filter; „vollständig“ bedeutet zunächst
vollständig bezüglich dieser dokumentierten Filter, nicht jeder mögliche Windschaden.

Nächster Download ist ein vollständiges Jahrespaket mit Tracks und Footprints
für einen festgelegten Algorithmus, danach die gesamten benötigten Jahre.
Vor einem Massendownload: Rechte, Zugangsweg, Dateischema, Masken und Mengen prüfen.
Top-50-CLIMK und einzelne XWS-Stürme bleiben wertvolle Vergleichsfälle, ersetzen
aber diese Jahresbasis nicht. ARCO kann Stundenfelder rekonstruieren; ein eigener
Ereigniskatalog daraus benötigt zusätzlich ein geprüftes Tracking-/Separationsverfahren.

### WISC: 22.980 Footprints sind keine 22.980 unabhängigen beobachteten Stürme

Der [Produktleitfaden](https://confluence.ecmwf.int/display/CKB/Synthetic+Windstorm+Events+for+Europe+from+1986+to+2011%3A+Product+User+Guide)
beschreibt fünf UPSCALE-Ensemblemitglieder und drei Kalibrierungssets aus der
synthetischen Basis mit 7.660 Ereignissen. Die Sets sind zur gemeinsamen Nutzung
vorgesehen; sie sind keine historischen Ereigniswiederholungen und ihre Varianten
liefern nicht ohne weitere Gewichtungsprüfung zusätzliche unabhängige Simulationsjahre.
Der Leitfaden nennt außerdem `eventset_summary.csv` als Ereignis-/Schwereinventar.
Dieses Inventar samt Mitglied-/Variantenidentität ist vor großen Rasterdownloads
besonders wertvoll. September–Mai ist keine ganzjährige Abdeckung.

Prüfen: Zuordnung der Varianten zu Basisereignissen, exakte abgedeckte Zeit je
Ensemble, Randjahre, Saisonfilter und veröffentlichte Häufigkeitsmethodik.
Erst danach gemeinsame Auftretensgewichte festlegen; die Rohzahl 22.980 niemals
einfach durch den nominalen Zeitraum teilen.

### Modellierte Schäden sind kein unabhängiger Schadenbeleg

Der [C3S-Tier-3-Leitfaden](https://confluence.ecmwf.int/spaces/CKB/pages/253724006/Loss+indicators+Tier+3+Product+User+Guide)
beschreibt berechnete Verluste aus Windfootprints, OSM, CORINE, PAGER,
Feuerstein-Kurven und Wiederaufbaukosten-Proxys. Diese Ergebnisse eignen sich
für Methodenvergleiche. Sie sind keine beobachteten Versicherungsansprüche.
Wenn unser Modell dieselben Kurven und Gebäude verwendet, wäre ein Vergleich
als „unabhängige Validierung“ zirkulär. Der Leitfaden nennt zudem ODbL-Bedingungen;
ein pauschaler Copernicus-Verweis ersetzt keine produktgenaue Rechteprüfung.

Tropische Wirbelsturmkurven, etwa Winston/Fiji, und US-Hurrikandaten bleiben
Transferforschungs-Kandidaten: Gebäudebauweise, Winddefinition, Schadenmechanismen
und Deckung müssen passen. Sie werden nicht automatisch europäische Sturmkurven.

## Arbeitsreihenfolge mit konkretem Abschlusskriterium

1. **Hazard-Definition und Jahresinventar:** ein EWS-Algorithmus, Gebiet,
   Zeitfenster, Raster und Datenversion; jedes selektierte Ereignis hat einen
   Footprint oder einen expliziten Fehler. Vollständige Monate/Jahre nachweisen.
2. **Messvalidierung:** bestehende KNMI/DWD/Frankreich-Originale mit Stationshistorie
   und identischen Zeitfenstern verbinden; zurückgehaltene Ereignisse und Länder
   prüfen. Zell-/Punktunterschiede und verbleibende Bias ausweisen.
3. **Gebäude und Werte:** zunächst DE/NL/FR/UK als vorgeschlagene Pilotländer,
   danach je Land dieselben Kriterien. Flächen/Bestände gegen Register und GHSL
   abgleichen, Werte gegen belegte Baukosten. Dies ist eine Ausbaufolge, keine
   Behauptung einer europäischen Vollabdeckung.
4. **Schadenkalibrierung:** Ereignis × Region × Klasse mit vergleichbarer Exposition,
   einschließlich nicht beschädigter Risiken. Ereignis-/Länder-Holdouts verhindern
   ein bloßes Nachbilden der Kalibrierfälle. Kein universeller Grenzwert ohne
   Messunsicherheit und Verwendungszweck.
5. **Stochastik und Finanzen:** nachvollziehbare Jahresgewichte, Sturmserien und
   grenzübergreifende Abhängigkeit, gemeinsame Unsicherheiten; AAL/OEP/AEP mit
   Konvergenz- und Sensitivitätsanalyse. Physische, versicherte und rückversicherte
   Verluste getrennt gegen Rechenorakel prüfen.

Downloads werden in externem, dauerhaftem Speicher mit Prüfsumme, URL,
Version, Rechtebeleg und Transformationsrezept archiviert. Temporäre Dateien
unter `/tmp` oder `/dev/shm` sind kein belastbares Datenarchiv. Große Raster nur
gezielt räumlich/zeitlich beziehen; zuerst Inventare, Metadaten und kleine
Originalproben prüfen. Alle hier genannten Kandidaten bleiben bis zum jeweiligen
Nachweis Kandidaten; diese Prüfung erklärt das Modell nicht für fertig.
