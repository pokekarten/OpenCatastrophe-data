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

## Räumliche Erweiterung: Tages- gegen Dreitagesmaximum

Ein weiterer Originaldownload derselben 73 Stunden wurde auf dem gemeinsamen
0,25°-Raster 0–16° E und 45–56° N ausgewertet. Die Zuordnung verwendet
CLIMK-Zeilen 64:109 und Spalten 88:153 sowie ARCO-Zeilen 136:181 und
Spalten 0:65. Die unterschiedlichen Ursprünge der beiden Raster sind dabei
explizit berücksichtigt. Ausgewertet wurden 2.090 positive CLIMK-Zellen;
Nullwerte außerhalb des ausgewählten Footprints wurden ausgeschlossen.

| ARCO-Fenster | Zellen mit absoluter Differenz <0,01 m/s | Mittlere absolute Differenz (m/s) |
|---|---:|---:|
| 18. Januar, Labels 00–23 | 1834 | 0,807258 |
| 18. Januar, Endpunkte 01–24 | 1902 | 0,582004 |
| 17.–19. Januar, Labels 00–23 | 2090 | 0,000467 |
| 17.–19. Januar, Endpunkte 01–24 | 2090 | 0,000467 |

In 201 Zellen unterscheidet sich das Dreitagesmaximum um mehr als 1 m/s vom
Maximum der 18.-Januar-Labels 00–23. Die räumliche Erweiterung kann daher die
Tageshypothese tatsächlich prüfen. Die Ergebnisse unterstützen für Kyrill
in diesem Ausschnitt die Interpretation als Maximum über drei Tage aus
täglichen Maxima. Die frühere Ableitung, CLIMK sei allein wegen der
Formulierung „daily maximum“ ein einzelnes Tagesfeld, war nicht ausreichend
belegt. Ein Vergleich ausschließlich mit dem DWD-Storm_Dates-Tag ist eine
Sensitivität und darf nicht als nachgewiesene zeitliche Harmonisierung gelten.

Beide Dreitagesgrenzen liefern dieselben Maxima. Die Untersuchung entscheidet
daher weiterhin nicht zwischen Stundenlabels 00–23 und Endpunkten 01–24.
Auch andere Ereignisse, Quellenfamilien und außerhalb des Ausschnitts liegende
Zellen sind damit nicht nachgewiesen. Die geringe Restabweichung ist keine
Byteparität und identifiziert keine bestimmte Packungs- oder Versionsursache.
