<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Kyrill: erster Vergleich mit originalen stündlichen ARCO-ERA5-Böen

Am 14. November 2026 wurden 73 originale stündliche Zarr-Chunks aus Googles
öffentlicher ARCO-ERA5-Verteilung heruntergeladen und dekodiert. Zeitraum:
17. Januar 2007 00:00 bis 20. Januar 2007 00:00, einschließlich beider
Endpunkte. Pro Feld wurde die Zelle 50,75° N / 7,25° E ausgewertet.

Quelle: https://storage.googleapis.com/gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3/
Variable: `10m_wind_gust_since_previous_post_processing`; originale
Zarr-Metadaten: Shape 1323648 × 721 × 1440, Chunks 1 × 721 × 1440,
Float32 little endian, Blosc/lz4. Zeitkoordinate: Stunden seit
1900-01-01 00:00:00, proleptischer gregorianischer Kalender.
ARCO-Zellindex: Zeile 157, Spalte 29. Der Vergleich verwendet CLIMK-Kyrill
Index 0, Zeile 85, Spalte 117; die Originalkoordinaten wurden kontrolliert.
CLIMK SHA-256:
`92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`.

| Größe | m/s |
|---|---:|
| CLIMK absolute_maxwindgusts | 33.744832584311055 |
| ARCO-Maximum über 73 Stundenlabels | 33.744041442871094 |
| ARCO-Maximum 18. Januar, Labels 00–23 | 33.744041442871094 |
| ARCO-Maximum 18. Januar, Stundenendpunkte 01–24 | 33.744041442871094 |

Die Differenz CLIMK minus ARCO beträgt rund 0,000791 m/s. Das ist eine
numerische Nähe für eine einzelne Zelle und ein Ereignis. Sie beweist keine
Bytegleichheit oder identische ERA5-Version: CLIMK und ARCO können andere
Packungs-/Verarbeitungsschritte haben. Insbesondere liefern alle drei
getesteten Zeitfenster denselben Maximalwert. Dieser Versuch kann daher
Tagesmaximum und Mehrtagesmaximum sowie die beiden Tagesgrenzen nicht
unterscheiden. Für eine Entscheidung müssen vorab weitere Zellen/Ereignisse
mit Maxima an unterschiedlichen Tagen bzw. Randstunden ausgewertet werden.
Die fehlende Böenmittelungsdefinition wird durch diese numerische Nähe
nicht ersetzt.

Die Untersuchung hielt Quellenwerte und Chunk-Prüfsummen außerhalb von Git.
Der lokale explorative Lauf ist noch kein versionierter Produktionsadapter;
eine erneute Umgebung benötigt einen reproduzierbaren Leser mit Prüfung der
Originalkoordinaten, Zeitausschitte, Einheiten und Metadaten. Es wurden keine
Schadenkurven oder Frequenzen kalibriert.

Attribution: Copernicus Climate Change Service (C3S), Google Research
ARCO-ERA5; Copernicus Licence. CLIMK-WINDS: Flynn et al. (2025), Zenodo
15305753, CC BY 4.0.
