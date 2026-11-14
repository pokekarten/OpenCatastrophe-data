<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# EIOPA: tatsächlicher Inhalt der vorhandenen Originalworkbooks

Originalprüfung am 14. November 2026 mit
`research_runners/eiopa_wind_workbook_inventory.py`. Die Dateien liegen extern
unter `/tmp/pr-ci/germany-wind-data`; Originalzellen werden nicht veröffentlicht.

- Exposure-Original SHA256:
  `f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79`.
  498 befüllte Datenzeilen, davon 250 Windstorm und 248 Flood, sämtlich
  mit Bezugsjahr 2020. Spalten: Jahr, Risiko, Land, NUTS, NUTS-Name,
  Versicherungssumme in EUR. Keine gebäudegenauen Werte und keine LoB-Spalte.
- Schaden-Original SHA256:
  `201bef4a15dccf4cb56edfe80fd2327b9bcd51ce3d815befb0730ffec5394fd6`.
  54 Datenzeilen, davon 39 Storm, ausschließlich Ciara Februar 2020;
  weitere Zeilen betreffen Hochwasser und Waldbrand. Keine vollständige
  historische Windschadenzeitreihe.

Die LoB-Kategorien des gesamten Schadenblatts umfassen ALL, COM, RES und
RES+COM. Vor einer Aggregation muss je Land/Ereignis geklärt werden,
welche Kategorien alternative Summen oder disjunkte Bestandteile sind.
Auch die Bedeutung von `Other`, Marktdeckung, Schadenstand, Preisbasis,
NUTS-Version und Deckungen sind vor einem Expositionsnenner-Abgleich offen.
Keine automatische Schadenquote aus diesen beiden Dateien berechnen.

**Nutzbarer nächster Modellfall:** Ciara 2020 mit einem zeitgleichen,
vollständigen Hazard-Footprint und landesweise abgeglichenem versichertem
Bestand. Die vorhandenen CLIMK-Ereignisse 1995–2015 decken Ciara nicht ab;
ein bloßer Index-Join wäre falsch. Das vorhandene ARCO-Stundenexperiment
kann eine Gefährdungsdiagnose unterstützen, ersetzt aber die Ereignis- und
Abdeckungsprüfung nicht. Ciara als Holdout oder Kalibrierfall vorab festlegen.

Der Reader ignoriert formatierungsbedingte Excel-Maximaldimensionen und
zählt tatsächlich befüllte Zeilen. Er inventarisiert Kategorien, liefert
aber weder eine fachliche Zulassung noch eine automatische Schadenaggregation.
Die lokale Ausgabe `/dev/shm/eiopa-wind-inventory.json` enthält das vollständige
Inventar. `openpyxl` ist für den Reader erforderlich.
