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
