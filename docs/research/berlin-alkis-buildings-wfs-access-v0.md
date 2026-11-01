<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin ALKIS building polygons: official WFS access preflight

## Official verified discovery, not an assumed building ingest

Publisher: Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin.
Official catalogue:
https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a
declares **Datenlizenz Deutschland – Zero – Version 2.0**.
The authority's catalogue describes actual cadastral **buildings and
building parts**, official download service, and the known WFS endpoint
https://gdi.berlin.de/services/wfs/alkis_gebaeude .

Independent Berlin government metadata says ALKIS WFS downloads are
updated **monthly**, and lists source native CRS **EPSG:25833**.
The official catalogue is not a claim that the WFS returns an EPSG:4326
GeoJSON building payload or that its feature type names are permanently
stable. The official government migration document warns that WFS
feature type names changed in the new Geoserver services.

Official publisher statements:
- https://www.berlin.de/sen/stadt/stadtdaten/geoinformation/liegenschaftskataster/geobasisdaten-online/datenbereitstellung/
- https://www.govdata.de/dl-de/zero-2-0
- https://gdi.berlin.de/services/wfs/alkis_gebaeude?request=GetCapabilities&service=WFS

## Exact implemented canary

`research_runners/berlin_alkis_gebaeude_wfs_capabilities_v0.py` makes
**exactly one** fixed anonymous HTTPS `GetCapabilities` request only
when explicitly run with `--live`:

```bash
python -m unittest tests.test_berlin_alkis_gebaeude_wfs_capabilities_v0 -v
python -m research_runners.berlin_alkis_gebaeude_wfs_capabilities_v0 --live
```

The 35-second, 4-MiB-limited request disables redirects and ambient
proxies, checks HTTP 200, expected XML media type, valid WFS protocol
version, no DTD/entity expansion, nonempty bounded FeatureTypeList and
at least one building-like feature type. A receipt prints UTC, exact
request, response bytes/SHA-256, WFS version, discovered building layer
**type names and declared CRS**, and source-code SHA-256. Public service
layer metadata is not the same as provider-owned building geometry or
addresses; no actual individual building/object data are requested or
persisted. A different service, a 404/403, oversized response, unsupported
protocol or XML exception must fail closed.

The GitHub Actions workflow is synthetic-only in PR review, then performs
one explicitly reviewed exact source check on the push that changes its
own workflow file in `main`. Ordinary pushes and scheduled jobs do
not request provider data. No API keys are needed.

## Precise next admitted-sample requirements

The result of the first live capabilities test should identify the
*current* real WFS GetFeature `typeNames`, advertised CRS and service
version. The next independently scoped implementation may fetch **a small
fixed central-Berlin bounding box with count limit**, but it must freeze
that type/CRS from live receipt, fix axis-order semantics for requested
WFS version, refuse arbitrary bbox/host/SQL filters, and strictly limit
data bytes, feature count and geometry validity. Detect building versus
building-part segmentation and the identifiers' actual namespace before
joining anything.

A genuine building footprint must be transformed from the *confirmed*
source coordinate CRS (commonly EPSG:25833), then tested by an exact
polygon/representative-point join against independently staged
geoBoundaries `DEU-ADM1-10402087` and the source-validated Eurostat
NUTS1 2021 `10M` crosswalk. Preserve all three **different source
vintages** and any land-border ambiguities. Berlin ALKIS buildings are
not a geospatial implementation of a provider-modified EUBUCCO 2016
NUTS2 partition. A building is not evidence of insured replacement
value, occupancy or loss.

This preflight does not modify Neon, Pokémon storage, any persistent CAT
database, or release provider object geometries. Do not mark Germany
building datasets as ingested until real feature bytes have passed their
own fixed access/rights/science gates.
