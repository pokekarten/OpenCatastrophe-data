<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Vollständiger Ereigniskatalog: monatlicher Liefernachweis

Für den historischen Katalog wird ein einzelner Tracker und eine feste
Produktversion benötigt. Für jeden Monat müssen Originalantwort, SHA256,
Lieferstatus und Ereignisliste vorliegen. Ein Monat ohne Datei ist kein
Monat ohne Sturm. Dasselbe physische Ereignis darf nicht mehrfach als
Auftreten zählen; seine kanonische Monatszuordnung muss vorab feststehen.
Alternative Tracker und Footprintvarianten bleiben getrennt.

`research_runners/wind_event_catalogue_completeness.py` prüft diese
Lieferbehauptungen: zusammenhängender Monatsbereich, genau ein Tracker,
keine doppelten Monate/Ereignisse, explizite Nullereignismonate und fehlende
Footprints. Das JSON-Format ist unser internes Prüfmanifest, kein behauptetes
C3S-Originalformat. Die Tests zeigen die erforderlichen Felder.

Der Prüfer bestätigt weder Originalbytes noch die Wahrheit eines vom
Aufrufer gesetzten Liefer-/Footprintstatus. Diese müssen ein separater
Originalreader und die archivierten Antworten belegen. Auch eine vollständige
Lieferliste autorisiert keine jährlichen Risikowerte ohne Auswahlregel,
Zeitbasis, Häufigkeitsgewichte und wissenschaftliche Prüfung.

Stand 15.11.2026: vier synthetische Offline-Tests bestanden. Noch kein
vollständiger realer Monatskatalog eingelesen. Die Umgebung besitzt weder
CDS-Konfiguration noch CDSAPI_KEY. Nächster realer Schritt ist ein
vollständiger Pilotjahres-Download von Tracks und Footprints für einen
festgelegten EWS-Tracker; danach dessen Originalreader und Monatsbelege
mit diesem Prüfer verbinden. Jahres-Summary-Zahlen allein ersetzen keine
Ereignisliste. Für WISC müssen zusätzlich Ensemblezeiten und dokumentierte
simulierte Monatslücken erhalten bleiben.
