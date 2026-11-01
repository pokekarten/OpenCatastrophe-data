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

## First verified official WFS capabilities response — 2026-11-01

The dedicated [GitHub Actions run 41318893338](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41318893338)
succeeded on main commit `6e1e0cbe1858e64633ce11d8857e9ac5fd7c444f`.

- UTC retrieval: `2026-11-01T15:00:06.479342+00:00`
- Original WFS response: **95,453 bytes**, SHA-256
  `c464d67da3b4b35637ba48fd375c1cb4579268536404a36cd80d478df7f78584`
- Official WFS version: **2.0.0**
- Advertised feature types: **1**, exact
  `alkis_gebaeude:gebaeude`.
- Advertised CRS: EPSG **25832**, **25833**, **3857**, **4258**, **4326**.
- No building data/feature geometries were acquired in this metadata-only check.
- Provider XML original bytes were not retained, no model inputs approved.

This now authorizes a separate, source-specific *reviewed pilot*, not an
unlimited GetFeature adapter or retrospective parcel/building evidence.

## Fixed bounded original feature sample and CAT1/CAT2 linkage v0

The optional source-specific research runner
`research_runners/berlin_alkis_gebaeude_five_feature_join_v0.py`
asks **one** anonymous WFS 2.0.0 `GetFeature`, exact feature name
`alkis_gebaeude:gebaeude`, `count=5`, fixed EPSG:25833
200m × 200m bbox `391700,5819950,391900,5820150`, and
`outputFormat=application/json`. There are no user-supplied arbitrary
query/BBOX/host/filter options. The WFS reply is bounded at 512 KiB.

The sample must consist of 1 to 5 structurally valid Berlin building
Polygon/MultiPolygon features in the fixed bounding box, plausible source
EPSG:25833 numeric axes and valid metric areas. Features, source
identifiers, source addresses, individual building coordinates and
private attributes are neither logged nor saved. Polygon representative
points are transformed from EPSG:25833 to WGS84 *in memory*, then
assigned through source-pinned local CAT1 geoBoundaries / CAT2 Eurostat
NUTS2021-10M. Every sampled building must resolve to `DE3` Berlin.
Failures preserve the source error rather than fabricate locations.

The dedicated GitHub Actions workflow
`.github/workflows/berlin-alkis-five-buildings-de3.yml` executes only
synthetic tests on PRs; one exact live request is permitted after
reviewed merge of the workflow revision, with the 6.25MB/0.37MB
reference geometry inputs verified and held in temporary storage.
All original and derived CAT bytes are deleted after the run. A pass
would demonstrate only successful regional assignment of at most five
*current provider WFS* building footprints to **2021 boundary regions**.
Because the provider WFS is live and monthly updated, no claim is made
that the individual buildings themselves existed in 2021, that geometry
has not changed since then, that a building equals an insured risk or
that an EUBUCCO modified-NUTS2016 partition is represented.

The first real original-feature receipt must be appended after the
run, including the true response hash, number of successfully validated
polygons, sample-area aggregate and whether all joins passed.
