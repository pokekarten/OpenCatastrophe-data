<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Windstorm: nächste ausführbare Datenschritte

Die [generierte Quellenübersicht](windstorm-repository-source-review.md)
verbindet vorhandene Windstorm-Kandidaten mit ihren kanonischen Katalogen.
Die folgenden Schritte nutzen bereits vorhandene Implementierungen.

| Modelllücke | Vorhandener Einstieg | Konkreter nächster Nachweis |
|---|---|---|
| CLIMK-Zeitaggregation | [ARCO-Einzelstundenleser](../../research_runners/ciara2020_google_arco_real_onehour_gust_v0.py), [96h-Leser](../../research_runners/ciara2020_google_arco_real_96h_nrw_area_v0.py) | Für ein CLIMK-Ereignis dessen Originaldatum, identische Rasterzelle und originale stündliche Böen rekonstruieren; Tages- und Dreitagesmaxima vergleichen. Vor Anpassung des festgelegten Ciara-Zeitraums müssen Ereignisidentität und Quellenvertrag versioniert werden. |
| Nationale Beobachtungen | [Offizielle Quellen und Zugangslücken](windstorm-europe-tc-official-source-gap-20261114.md), [Météo-France-Feldprüfung](meteofrance-hourly-original-3second-gust-preflight-v0.md) | Einen Originalextrakt mit FXI3S, Qualitäts- und Berechnungsstatus beschaffen; Stationsgeschichte, Höhe und Zeitintervall nachweisen. FXI und FF sind keine impliziten FXI3S-Ersatzwerte. |
| Europäische Gebäude | [EUBUCCO-Luxemburg-Metadaten](../../research_runners/eubucco_lu_original_metadata_xlsx_v0.py), [Geometrieabgleich](../../research_runners/luxembourg_geobase2026_eubucco_bounded_pair_v0.py) | Einen versionierten Länderextrakt mit nationalem Gebäudebestand abgleichen; IDs, Dubletten, Nutzung, Fläche und beobachtete versus geschätzte Attribute ausweisen. Gebäudegeometrie allein liefert keinen Ersatzwert. |
| Jahreskatalog | [WISC-Dateinamenprüfung](../../research_runners/wisc_filename_ensemble_preflight_v0.py), [NetCDF-Oasis-Adapter](../../research_runners/wisc_netcdf_oasis_tile_v0.py) | Originaldateien samt dokumentierter Iteration, Ereignis-/Jahreszuordnung und Gewichten prüfen. Die Zahl 22.980 allein definiert keine Jahresrate. C3S-Zugang und vollständige Ereignismaße bleiben offen. |
| Vulnerabilität | [LUISA-Mischkurvenvergleich](windstorm-europe-luisa-mixture-sensitivity-v0.md), [Pixel-Sensitivität](windstorm-europe-luisa-point-sensitivity-v0.md) | Die beiden Outbuilding-Zuordnungen gegen die Originalmethodik klären und Windmaß/Schadenmaß kompatibel machen. Vorhandene Kurven sind Sensitivitätsquellen; regionale Kalibrierung benötigt kompatible Schadenbeobachtungen. |

Die Reihenfolge priorisiert die Rekonstruktion der Windgröße, weil sie sowohl
Stationsvergleich als auch Kurvenanwendung beeinflusst. Danach können weitere
Länderbeobachtungen und geprüfte Gebäudeextrakte den räumlichen Umfang
vergrößern. Ein jährliches europäisches Verlustmodell benötigt zusätzlich
einen vollständigen Ereignis-/Jahreskatalog mit nachvollziehbaren Gewichten.
