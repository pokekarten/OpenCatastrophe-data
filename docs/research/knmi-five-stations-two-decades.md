<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zehn weitere originale KNMI-Stundenarchive

Die offiziellen CDN-Archive der Stationen 235, 260, 280, 310 und 330 wurden
für 2001–2010 und 2011–2020 heruntergeladen und vollständig dekodiert.
Alle zehn Downloads waren erfolgreich: 17240816 Bytes komprimiert,
876600 Stationsstunden, davon 876578 mit vorhandenem FX-Wert.
Die 22 fehlenden FX-Werte betreffen Station 235 im Zeitraum 2001–2010.
Vorhanden bedeutet hier befülltes Feld, nicht geprüfte Messqualität.

Der [maschinenlesbare Downloadbeleg](../../research/observations/knmi_five_station_hourly_downloads.toml)
enthält je Datei URL, Original-SHA-256, Größe, Zeitraum und Zählwerte.
Die originale ZIP-Mitgliedschaft und eingebettete Stations-ID wurden beim
Lesen kontrolliert. Die Rohdateien liegen außerhalb von Git unter dem
externen temporären Datenverzeichnis; ein dauerhafter Archivierungsort
bleibt erforderlich. Es wurde kein Jahresereigniskatalog aus den
Stationsstunden abgeleitet.

Die Felddefinition ist wie beim [Schiphol-Original](knmi-schiphol-original-hourly-acquisition.md):
FX bezeichnet die höchste Böe der vorherigen Stunde in 0,1 m/s. Fehlende
Werte werden nicht als Windstille interpretiert. Historische Messmethoden,
Stationsstandorte, Instrumentenhöhe, Böenmittelung, Qualität und Rechte
müssen vor einer wissenschaftlichen Modellaufnahme geprüft werden.
Die Serie darf laut eingebetteter Originalwarnung nicht ungeprüft für
Trendanalysen verwendet werden. Mehrere Stationen desselben Sturms sind
auch keine unabhängigen Ereignisse.

Nächster Rechenschritt: vollständige Stundenendpunktfenster je geprüftem
Sturm bilden, Ereignisidentität mit CLIMK abgleichen und Stationen auf
historisch korrekte native Gitterzellen zuordnen. Der aktuelle Download
verbessert die Beobachtungsabdeckung, kalibriert aber noch keine
Schadenantwort oder jährliche Sturmrate.

Attribution: Royal Netherlands Meteorological Institute (KNMI).
