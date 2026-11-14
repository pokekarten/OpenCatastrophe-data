<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Integrierter Mehrsturm-Modelllauf

Der vollständige Modellpfad wurde auf allen 50 originalen ERA5-CLIMK-Stürmen
mit dem versionierten fiktiven London-/Paris-/Köln-Portfolio ausgeführt.
Ergebnis: 50 ausgeführte, null wegen ValueError blockierte Ereignisse.
Der Pfad umfasst originale Gefahrenfelder, Standortzuordnung, die expliziten
CLIMAAX-Antwortklassen, fiktive Gebäudewerte, Policen und Rückversicherung.
Die zehn Tests für Schaden-Sampling, Jahresfinanzen, integrierten Modellkern
und Jahresblock-Sampling bestanden im selben Arbeitsstand.

Der [Sweep-Runner](../../research_runners/windstorm_europe_all50_model_sweep.py)
verwendet `--hazard ORIGINAL.nc --curves ORIGINAL.csv --output EXTERN.json`.
Die Eingaben werden weiterhin durch den Modellkern auf Quellprüfsummen
geprüft. Jedes Ereignis wird einzeln als bedingtes Szenario berechnet; die
50 ausgewählten Ereignisse werden nicht als empirisches Kalenderjahr
interpretiert. Ausgabe und Eingaben bleiben außerhalb von Git.

Der Lauf beweist weder europäische Portfolioabdeckung noch Kalibrierung.
Die drei Standorte und Werte sind fiktiv; Quellenmasken können bei anderen
Standorten zu blockierten Läufen führen. Die Prozentkurven sind explizite
Antwortannahmen. Ein vollständiges jährliches Verlustmodell benötigt weiter
einen vollständigen Ereignis-/Jahreskatalog, geeignete Gebäudewerte und
beobachtete Schadenantworten. Globale Erweiterung benötigt zusätzlich eigene
Gefahren- und Vulnerabilitätsnachweise außerhalb Europas.

Die geprüfte Sweep-Fassung wurde erneut auf den Originaldaten ausgeführt:
50 abgeschlossen, null blockiert. Der Beleg enthält Fixture-, Gefahren- und
Kurven-SHA-256 sowie die Gefahrenprovenienz pro Ereignis. Blockierte Szenarien
führen zu Exitstatus 1; der Teilbeleg bleibt zur Diagnose erhalten. Der
unveränderte Modellkern wurde mit zehn gezielten Tests geprüft.
