<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Originale französische Stundenbeobachtungen: Paris und Kyrill

Die offiziellen Dateien wurden am 14. November 2026 ohne API-Konto heruntergeladen. Originalbytes bleiben außerhalb von Git. Der Download ist ein Datenzugangsnachweis; die wissenschaftliche Eignung wird getrennt geprüft.

| Datei | Bytes | SHA-256 |
|---|---:|---|
| meteofrance-hourly-fields.csv | 11252 | `1ff2c0febb4a040bf8b400e422bc2bf3e9b8c3e48bdda73a67b1790c532021da` |
| H_75_2000-2009.csv.gz | 10964790 | `e42541c21153eb171733e040e1f19dbd0f3f17ea27f8e9a54496ddcfe0b99ef3` |

Quell-URLs:
- https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/H_descriptif_champs.csv
- https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/H_75_2000-2009.csv.gz

Die gzip-Datei wurde vollständig als CSV gelesen: 284,971 Zeilen. Für den Ausschnitt 17. Januar 2007 00 bis 20. Januar 2007 00 wurden 73 Zeitlabels je Station gefunden.

| Station | gültige FXI3S | QFXI3S | STATUS_FXI3S | Maximum m/s |
|---|---:|---|---|---:|
| TOUR EIFFEL | 72 | 1 | 1 | 34.8 |
| PARIS-MONTSOURIS | 73 | 1 | 1 | 22.4 |

Die offizielle Feldbeschreibung nennt FXI3S als maximale über drei Sekunden gemittelte Windgeschwindigkeit innerhalb der Stunde, in m/s. Der separate Status 1 bezeichnet laut bestehender [Feldprüfung](meteofrance-hourly-original-3second-gust-preflight-v0.md) eine Berechnung mittels Transferfunktion. Qualitätscode 1 beseitigt diese Abhängigkeit nicht. Die Werte dürfen nicht als instrumentell direkt gemessene, unabhängige 3-Sekunden-Beobachtungen bezeichnet werden.

Der Eiffelturm ist zudem ein spezieller Standort; Höhe und Instrumentengeschichte sind vor einem 10-m-Gittervergleich zu prüfen. Eine fehlende Beobachtung bleibt fehlend. Die 73-Label-Auswertung ist ein Verfügbarkeitscheck, kein bereits harmonisiertes Ereignisfenster. Weder Vulnerabilität noch Windmodell wurden damit kalibriert.

Nächster Datenentscheid: zusätzliche Stationen/Perioden auf STATUS_FXI3S=0 und vollständige Ereigniszeitreihen prüfen; auch Status 0 allein beweist keine instrumentelle Unabhängigkeit. Stationsgeschichte, Höhe, Messmethode und Zeitgrenzen müssen separat belegt sein.

Attribution: Météo-France; öffentliches BASE/HOR-Produkt, Etalab Licence Ouverte 2.0 gemäß dem bereits dokumentierten offiziellen Datensatz. Die Downloadantwort selbst ist kein zusätzlicher Lizenznachweis.

## Erweiterung 2010–2019 und Xynthia-Kandidat

Ein zweiter Originaldownload ergab `H_75_2010-2019.csv.gz`, 14.837.087 Bytes,
SHA-256 `09ab7d2b92d413ad481b0b11730ab84a1caca10eaa2dd60e6124184efbd8b511`.
Quelle: https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/H_75_2010-2019.csv.gz
Die vollständige CSV enthält 350.633 Zeilen. In Paris-Montsouris sind 87.312
FXI3S-Werte vorhanden, davon 86.917 mit Status 0 und 395 mit Status 1; alle
tragen Qualitätscode 1. Status 0 ist daher nicht für die ganze Serie konstant.
Im vorherigen Jahrzehnt gibt es dort bereits 9.368 Status-0-Werte; der erste
gefundene Zeitstempel ist 2008-12-03 14. Das bestimmt keine lückenlose
Instrumentenperiode.

Für Paris-Montsouris (75114001) wurde das Xynthia-Kandidatenfenster mit
Labels 2010-02-27 01 bis 2010-03-02 00 geprüft. Alle 72 erwarteten Labels
sind eindeutig vorhanden, mit gültigem FXI3S, Qualitätscode 1 und Status 0.
Das Maximum beträgt 29,5 m/s. Die Auswahl ist vorläufig: Die Anwendung einer
Stundenendpunktkonvention muss gegen die französische Parameterdokumentation
geprüft werden; DWD-Konventionen sind kein Beleg für Météo-France.

Das Eiffelturm-Archiv enthält im selben Jahrzehnt ausschließlich Status 1.
Longchamp enthält 1.108 Status-0-Werte, diese tragen jedoch Qualitätscode 9;
sie wurden nicht als validierte Beobachtungen ausgewählt. Die Untersuchung
zeigt, warum Qualitätscode und Transferstatus gemeinsam geprüft werden müssen.
Status 0 allein beweist weder direkte instrumentelle Erfassung noch
Unabhängigkeit von ERA5. Vor dem nächsten Windvergleich fehlen insbesondere
Stations-/Instrumentenhistorie und Messhöhe, die Bedeutung des Stundenlabels
sowie die geprüfte CLIMK-Xynthia-Ereignisidentität.
