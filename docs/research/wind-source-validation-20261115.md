<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Originalprüfung vom 15.11.2026

37 heruntergeladene Dateien wurden gegen Größen und SHA256-Quittungen geprüft.
20 KNMI-Archive wurden auf Station, Dekade, Dubletten und fehlende Böen geprüft;
Météo-France-GZIPs vollständig auf CSV-Zeilenbreite gelesen und zehn NetCDFs
auf Variablen, Masken und numerische Wertebereiche untersucht.
Weitere Begleitdateien/Tracks wurden nur auf Integrität geprüft.

Nicht endliche Werte (Datei, Variable, Anzahl):

- ('CCLM_ERA5_EUR-11_StormFootprint_Database_Europe_Winter_1995-2015.nc', 'LI_gridpoint', 18654)
- ('CCLM_ERA5_CEU-3_StormFootprint_Database_Europe_Winter_1995-2015.nc', 'LI_gridpoint', 59841)
- ('COSMO-REA6_StormFootprint_Database_Europe_Winter_1995-2015.nc', 'LI_gridpoint', 97097)
- ('ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc', 'LI_gridpoint', 3732)

Diese Werte bleiben fehlend; sie sind kein Nullwind. Keine wissenschaftliche
oder rechtliche Zulassung. Vollständige lokale Ausgabe: `/dev/shm/wind-source-validation-complete.json`.
Reproduktion: `python research_runners/validate_downloaded_wind_sources.py --directory /external/originals --output /external/validation.json`.
Benötigt numpy und netCDF4. Zwei lokale Integritätsregressionen bestanden.
