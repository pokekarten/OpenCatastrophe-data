<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Vollständiger Ereigniskatalog: monatlicher Liefernachweis

Für den historischen Katalog wird ein einzelner Tracker und eine feste
Produktversion benötigt. Für jeden Monat müssen Originalantwort, SHA-256,
Lieferstatus und Ereignisliste vorliegen. Ein Monat ohne Datei ist kein
Monat ohne Sturm. Dasselbe physische Ereignis darf nicht mehrfach als
Auftreten zählen; seine kanonische Monatszuordnung muss vorab feststehen.
Alternative Tracker und Footprintvarianten bleiben getrennt.

`research_runners/wind_event_catalogue_completeness.py` prüft ein strikt
versioniertes internes JSON-Manifest (`WIND_EVENT_CATALOGUE_MONTHLY_INPUT_V1`):
exaktes Monatsformat, zusammenhängender Monatsbereich, konstanter Tracker
und Produktversion, eindeutige Monate/Ereignis-IDs, formatierte SHA-256-Angaben,
explizite Nullereignismonate und Boolean-Footprintstatus. Das Format ist kein
behauptetes C3S-Originalformat.

Der Prüfer bestätigt weder Originalbytes noch die Wahrheit eines vom
Aufrufer gesetzten Liefer-/Footprintstatus: er prüft nur die Schreibweise der
SHA-256-Felder und die interne Konsistenz der Angaben. Die Werte
`declared_catalogue_structure_complete` und `explicit_zero_event_months` sind
daher Manifestbehauptungen, keine verifizierten Beobachtungen. Ein separater
Originalreader muss Bytes hashen und Ereignis- und Footprintzuordnung daraus
reproduzieren. Auch eine vollständig geprüfte Lieferliste autorisiert keine
jährlichen Risikowerte ohne Auswahlregel, Zeitbasis, Häufigkeitsgewichte und
wissenschaftliche Prüfung.

Stand 17.11.2026: neun synthetische Offline-Tests prüfen auch fehlerhafte
Monatsangaben, Hashformate, Schema-/Typfehler, doppelte JSON-Schlüssel,
doppelte IDs, gemischte
Produktversionen und die Grenze zwischen Vollständigkeitsbehauptung und
wissenschaftlicher Zulassung. Es wurde weiterhin kein vollständiger realer
Monatskatalog eingelesen. Die Umgebung besitzt weder CDS-Konfiguration noch
CDSAPI_KEY. Nächster realer Schritt ist ein vollständiger Pilotjahres-Download
von Tracks und Footprints für einen festgelegten EWS-Tracker; danach dessen
Originalreader und Monatsbelege mit diesem Prüfer verbinden. Jahres-Summary-
Zahlen allein ersetzen keine Ereignisliste. Für WISC müssen zusätzlich
Ensemblezeiten und dokumentierte simulierte Monatslücken erhalten bleiben.
