<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Originalprüfung vom 15.11.2026

37 heruntergeladene Dateien wurden gegen Größen und SHA256-Quittungen geprüft.
20 KNMI-Archive wurden auf Station, Dekade, Dubletten und fehlende Böen geprüft;
Météo-France-GZIPs vollständig auf CSV-Zeilenbreite gelesen und zehn NetCDFs
auf Variablen, Masken und numerische Wertebereiche untersucht.
Weitere Begleitdateien/Tracks wurden nur auf Integrität geprüft.

Nicht endliche Werte (Datei, Variable, Anzahl):

- ('CCLM_ERA5_EUR-11_StormFootprint_Database_Europe_Winter_1995-2015.nc', 'LI_gridpoint', 18654)
- ('CCLM_ERA5_CEU-3_StormFootprint_Database_Europe_Winter_1995-2015.nc', 'LI_gridpoint', 59841)
- ('COSMO-REA6_StormFootprint_Database_Europe_Winter_1995-2015.nc', 'LI_gridpoint', 97097)
- ('ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc', 'LI_gridpoint', 3732)

Diese Werte bleiben fehlend; sie sind kein Nullwind. Keine wissenschaftliche
oder rechtliche Zulassung. Vollständige lokale Ausgabe: `/dev/shm/wind-source-validation-complete.json`.
Reproduktion: `python research_runners/validate_downloaded_wind_sources.py --directory /external/originals --output /external/validation.json`.
Benötigt numpy und netCDF4. Zwei lokale Integritätsregressionen bestanden.

## Ereignisidentitäten und LI gegenüber Wind

Originaldiagnose mit `climk_event_identity_diagnostics.py`: 200 Quellansichten
bilden 96 rein wörtliche Name-/Datumsgruppen. 18 Namen haben unterschiedliche
Datumslabels. Besonders auffällig: Gunter mit 20050110 und 20150110.
Der unten verknüpfte frühere Originalvergleich löst diesen konkreten Datumswiderspruch auf; die rohe Quelldatei bleibt unverändert.
Andere Unterschiede betragen häufig einen Tag und können mit der Auswahl
von Ereignisfenstern zusammenhängen. Keine automatische physische Zusammenführung.
Vollständiges lokales Diagnoseergebnis: `/dev/shm/climk-identity-diagnostics.json`.

An allen nicht endlichen LI_gridpoint-Stellen sind absolute_maxwindgusts
endlich und positiv: ERA5 3.732, EUR-11 18.654, CEU-3 59.841,
COSMO-REA6 97.097 Stellen. LI_gridpoint ist laut Originalmetadaten ein
berechneter Verlustindex, kein Windfeld. Seine fehlenden Werte dürfen daher
nicht als fehlende Windabdeckung oder Nullwind interpretiert werden.
Der Grund der fehlenden Indexwerte ist damit noch nicht erklärt.

## GUNTER: vorhandenen repositoryübergreifenden Nachweis verknüpft

Die [maschinenlesbare Referenz](../../research/observations/climk_gunter_date_resolution_reference.json)
verweist auf einen konkreten Commit im Modellrepository. Der dortige
DWD-HoKliSim-Vergleich fand 142.004/142.004 positive CEU-3-Zellen identisch
zum Maximum 09.–11.01.2015 und 0 passende Zellen für 09.–11.01.2005.
Die SHA256 der aktuell geladenen CEU-3-Datei stimmt exakt mit der geprüften
Quelldatei dieses Nachweises überein. Daher ist 20150110 für diese konkrete
Datei und GUNTER als belegtes Join-Datum verwendbar; 20050110 bleibt das
unveränderte rohe Metadatum. Der DWD-Feldvergleich wurde in diesem Lauf
nicht erneut ausgeführt. Andere Datumsabweichungen bleiben separat zu prüfen.
Diese Auflösung erzeugt weder neue Ereignisse noch jährliche Häufigkeiten.
