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

## First actual official building polygons to NUTS2021: PASS — 2026-11-01

A single fixed bounded **live** GetFeature request succeeded in
[GitHub Actions run 41319506268](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41319506268),
main commit `c5a252567bcd182a4f2bc89894ff640dfca340a4`.

- UTC receipt: `2026-11-01T15:06:41.876233+00:00`
- Original source: Berlin ALKIS WFS 2.0.0,
  `typeNames=alkis_gebaeude:gebaeude`, `count=5`,
  `outputFormat=application/json`, fixed 200m × 200m
  EPSG:25833 query box.
- **Five** real original provider feature polygons returned,
  all five accepted as valid source building geometries.
- Original provider response **5,412 bytes**, SHA-256:
  `6359a9ea2a5ca81b7d6c8281db465b9f1e7f1a7f680bf8381d94cc9acc7b304b`.
- Trusted executing script SHA-256:
  `167edf3f1c318599001fe661cd52a7d70c8551e8ffa87c2818985584148ebd69`.
- Total sampled source footprint area: **1,344.0 m²**.
  The sampling cap does **not** make this the total number/area of
  buildings in the query box; original provider building versus
  building-part segmentation also remains a research caveat.
- Each original polygon's privately computed EPSG:25833 representative
  point was transformed to WGS84 and checked against the independent
  original CAT1 (2021 geoBoundaries) and CAT2 (2021 Eurostat NUTS1 10M)
  SQLite mapping: **5 of 5 accepted as NUTS2021 `DE3` Berlin**.
- No provider addresses, individual coordinates, original provider
  feature IDs, raw feature bytes or CAT staging databases were
  exported, committed to the public repository or persisted to
  production/Neon/Pokémon storage.

**Scientific result:** real official current-source building
polygon-to-2021-region attribution now works on a bounded five-feature
sample. Since Berlin WFS is updated regularly, neither this test nor
the older polygon boundaries proves that these exact buildings existed
in 2021. This **does not** establish any insured replacement value,
peril vulnerability, construction-year, complete Berlin inventory or
source-licensed nationwide data admission.

## CAT4 isolated original-derived building polygon staging v0

The verified official ALKIS building sample can now also generate a **new,
isolated CAT4 SQLite file** using the identical in-memory WFS response.
This keeps derived polygons usable for approved local comparison and quality
checks rather than retaining source IDs, raw original feature bytes,
addresses or property values. The caller explicitly chooses an existing
secure parent directory outside the Git checkout; no production or
Pokémon repository database is opened or overwritten.

Opt-in command (the reviewed sample's two pinned CAT databases must exist):

```bash
python -m research_runners.berlin_alkis_gebaeude_five_feature_join_v0 \\
  --live \\
  --cat1 /secure/cat-data/staging/deu-adm1-2021.cat.sqlite \\
  --cat2 /secure/cat-data/staging/deu-adm1-nuts2021.cat.sqlite \\
  --cat4-output /secure/cat-data/staging/berlin-5-buildings.cat.sqlite
```

Before writing a derived CAT building database, `stage_derived_footprints` now
**independently rechecks** each original source polygon's representative point
against the pinned CAT1 and CAT2 SQLite databases. A caller-provided array of
`DE3` labels is never sufficient to establish region proof; missing CAT paths,
mismatched 2021 version, incorrect 10M source scale and non-DE3 returned regions
block the write. The same bounded WFS bytes are reused, without another
provider request. Synthetic negative tests cover deliberately forged
region labels. This is a research-stage location integrity check, not
proof of a building's construction date or regional insured assets.

Output-only tables:

- `provenance`: official WFS source and feature type, exact response
  SHA-256/UTC, provider licence `dl-de-zero-2.0`, **unknown feature
  construction/vintage**, administrative geometry vintage 2021, and
  `model_admitted=0`.
- `building_sample`: local 1..5 index, source polygon **EPSG:25833
  WKB geometry** after validity check, footprint area in m², verified
  administrative 2021 NUTS1 code `DE3`. No original feature IDs,
  original property values, names, addresses, occupants, valuation or
  loss values; no fake buildings are synthesized.
- SQLite uses distinct application ID `BLD4` (hex `424C4434`),
  fresh-only `*.cat.sqlite` destination outside Git and atomic
  no-overwrite link. Its data are a local research snapshot, not a
  shared system-of-record migration.

A dedicated amended workflow rechecks the two original source-pinned CAT1
and CAT2 input datasets, executes **one** original official WFS request,
builds CAT4 and verifies row count, region and explicit non-admission,
then deletes all temporary original and derived files. The first real
CAT4 execution receipt must be recorded after verification.

**Caveats:** Sample cap 5 is not a complete census for the bounded
WFS box, and a cadastral building feature may represent segments or
construction parts rather than a unique insured property. The live 2026
source is not a 2021 historical snapshot. Sampling proves spatial access
and coding, not insured portfolio coverage, value, secondary uncertainty,
or vulnerability calibration. Persistent CAT database ingestion needs
separate governance and storage credentials.

## Verified CAT4 isolated derived building geometry stage — 2026-11-01

The first complete source-to-local-database execution passed in
[GitHub Actions run 41320072699](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41320072699),
main commit `2f7dd8a516899d0b441211784fbfeef3bde01221`.

- Provider receipt UTC: `2026-11-01T15:13:12.846819+00:00`.
- WFS 2.0.0 official 5-building fixed bbox actual response:
  **5,412 bytes** / SHA-256
  `347536364aef4e108c9e9f69536073297e453ccf69c303d804011322519cbfd1`.
  The SHA differs from the earlier five-feature receipt, proving the
  mutable WFS representation should **never** be implicitly treated as
  a version-frozen historic snapshot, even if its aggregate spatial
  sample values are unchanged.
- Actual feature validation: **5 of 5** geometries accepted;
  five distinct polygons in the capped sample; **1,344.0 m²**
  combined sampled footprint area.
- Source-original projected coordinates transformed, privately and
  per-feature checked against original source-pinned CAT1/CAT2:
  **five of five resolved as Berlin `DE3` (NUTS 2021 / 10M)**.
- New separate `CAT4` SQLite file was **actually constructed**,
  `app_id=1112294452`, verified five rows with only `DE3`,
  provenance, no original feature IDs/properties, and `model_admitted=0`.
  The job printed
  `PASS: bounded official Berlin buildings staged as source-derived CAT4 polygons in DE3`.
- No shared production CAT/Neon database was altered; raw WFS reply was
  not persisted and the derived CAT4 staging file was deleted after
  the job. This was a real, **ephemeral** data-staging test, not a
  durable deployment or claim that five features represent the whole box.

This establishes an executable **official real building → geometry →
source-vintage-aware NUTS1 → isolated CAT SQLite** path, which previously
did not exist. Next decisions should prioritize a separate CAT storage
destination, exact source snapshot governance, WFS paging/limit validation,
building-vs-building-part segmentation, per-attribute completeness,
and date-appropriate join versions before expanding coverage or using
any result as an insured-building portfolio.
