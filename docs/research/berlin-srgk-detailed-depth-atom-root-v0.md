<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin detailed SRGK Atom root: depth-data catalogue preflight

**Research-only: root metadata access only; live source result pending
reviewed workflow merge.**

We now have a *second* official detailed-model-area source pilot
with verified polygon overlap from two independent WFS queries:
[original run 41363537076](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41363537076),
EPSG:25833 box `391860,5816840,392060,5817040`,
**40,000 m²** independent source-filtered polygon intersection.
No actual depth data, actual event, insurer TIV or CAT loss has yet
been verified in this region.

The
[official Berlin technical data format description](https://gdi.berlin.de/data/ua_srgk/docs/Datenformatbeschreibung_02_24_2srgk2023.pdf)
identifies the model-area WFS separately from the water-level
GeoTIFF data, which are published through an **Atom feed**. The
[official catalogue](https://daten.berlin.de/datensaetze/starkregengefahrenkarte-wfs-1aa4f1ef)
publishes CC BY 4.0 attribution requirements with source-specific
origin statements. A WFS licence is not by itself a complete
product-by-product rights and redistribution proof for every linked ZIP.

`research_runners/berlin_srgk_detailed_atom_root_v0.py`
performs **one fixed** HTTPS GET to
`https://gdi.berlin.de/data/ua_srgk/atom/`, which is
intentionally different from the separately verified
`ua_srhk` 2025 Hinweiskarte Atom root. It forbids redirects,
proxies and external-source follow-up, limits transfer to 256 KiB,
rejects XML DTD/entities and unbounded link/entry lists, and only
reports aggregate Atom link/media/ZIP counts, byte count, original
XML SHA-256 and original retrieval UTC. The original source XML is
not saved in the repo or CAT/insurance database.

One valid Atom root does **not** prove any specific 1D/2D depth
GeoTIFF is retrievable for the new 200m pilot. The next source
gate is an independently reviewed exact child-feed/ZIP product
identity, scenario and vintage mapping, attribution, internal
GeoTIFF CRS/unit/NoData and **actual intersection of its pixels
with the proven second pilot**. That must be distinct from the
BKG KOSTRA signed Int16 depth-scaling blocker
[issue #1086](https://github.com/pokekarten/OpenCatastrophe-data/issues/1086).

No large ZIP, TIFF, raw cell, source model geometry, customer
location, stochastic catalogue, vulnerability function, loss, insurance
contract or model-admitted asset is fetched or registered by this probe.
