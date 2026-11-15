<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# KNMI Schiphol: zusätzlicher originaler Stundenarchiv-Zugang

Das offizielle historische Stundenarchiv wurde ohne API-Schlüssel erfolgreich
heruntergeladen. Dieser CDN-Zugang ist getrennt von der im Quellenkatalog
beschriebenen, schlüsselpflichtigen EDR-API. Der Download belegt keine
EDR-Ausführung und hebt deren Zugangsvoraussetzungen nicht auf.

Quelle: https://cdn.knmi.nl/knmi/map/page/klimatologie/gegevens/uurgegevens/uurgeg_240_2001-2010.zip

Original-ZIP: 1769900 Bytes, SHA-256 `7e1b6ba9dfa4b10a4e8d2ae64f874d433f8789a65b759474454c612f26fd5b3c`.

Das ZIP enthält `uurgeg_240_2001-2010.txt`; die vollständige Tabelle enthält 87648 Datenzeilen.

Die eingebettete KNMI-Originalbeschreibung definiert `FX` als maximale Böe
der vorherigen Stunde, in 0,1 m/s. `HH=05` umfasst 04:00–05:00 UT; die
Stundenlabels sind daher Stundenendpunkte, nicht Stundenanfänge. FH ist
Stundenmittel und FF Zehnminutenmittel; beide ersetzen FX nicht.

Für 17.–19. Januar 2007 wurden 72 Zeilen mit 72 eindeutigen Datum-/Stundenlabels und 72 vorhandenen FX-Werten gefunden. Das Maximum beträgt 36.0 m/s.

Dies ist ein Verfügbarkeits- und Einheitencheck. Die Datei warnt ausdrücklich
vor Inhomogenität durch Standortverlagerungen und Änderungen der Messmethoden
und schließt die Verwendung der Serie für Trendanalysen aus. Die beobachtete
Böendauer, Instrumentenhistorie und Messhöhe sind noch zu prüfen; aus FX allein
wird keine 3-Sekunden-Böe abgeleitet. Ein unabhängiger Qualitätsflag für FX
wurde hier nicht nachgewiesen. Keine Kalibrierung oder Korrektur wurde gefittet.

Originaldatei und lokaler Downloadbeleg bleiben außerhalb von Git. Vor
Modellaufnahme ist die konkrete Weiterverwendungslizenz zu prüfen; die
Quellenangabe in der Datei ersetzt keine abgeschlossene Rechteprüfung.
Attribution: Royal Netherlands Meteorological Institute (KNMI).
