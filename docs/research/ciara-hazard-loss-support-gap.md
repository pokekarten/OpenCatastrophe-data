<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Ciara: Winddaten und Schadenumfang abgleichen

Die vorhandene EIOPA-Datei nennt für Ciara den 07.–11.02.2020.
Die vorhandene ARCO-Auswertung umfasst Stundenlabels vom 08.02. 00 UTC
bis 11.02. 23 UTC und 160 Rasterknoten zwischen 50,25–52,5°N und
5,75–9,5°E. Sie ist eine regionale Untersuchung, kein landesweiter Footprint.

Unter der ausdrücklich vorläufigen Interpretation der EIOPA-Kalendertage
als volle UTC-Tage fehlt mindestens der 7. Februar im Stundenlabelbereich.
Die tatsächliche Zeitzone und der Support der stündlichen ERA5-Maxima
müssen separat bestätigt werden. Der Labelbereich ist nicht automatisch
identisch mit den physikalischen Messintervallen.

Der neue `hazard_loss_support.assess` prüft explizite halboffene Zeitintervalle
und eine separat belegte geografische Abdeckung. Die UTC-Sensitivitätsrechnung
meldet 24 Stunden fehlende Anfangsabdeckung. Eine räumliche Freigabe ist
für den regionalen Ausschnitt gegenüber nationalen Schäden nicht gegeben.
Auch ein bestandener Zeit-/Raumtest belegt noch keinen identischen versicherten
Bestand oder korrekte Schadenaggregation.

Nächste Beschaffung: Stundenfelder für den zusätzlichen 7. Februar und die
vollständigen Zielgebiete, nach Festlegung der Ereignisgrenzen. Die vorhandene
regionale Maximalrasterdatei kann fehlende Stunden nicht rekonstruieren.
Vor einem großen Download zuerst Stundeninventar, Bounds, Preis-/Deckungsbasis
und Speicherbedarf festlegen. Für EIOPA-Ciara außerhalb des bisherigen
Ausschnitts keine Windwerte extrapolieren.
