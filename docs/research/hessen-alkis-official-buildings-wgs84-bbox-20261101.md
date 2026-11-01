<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hessen ALKIS official 2D buildings: WGS84 source-service canary

**Research date:** 2026-11-01. **Status:** official source catalogue and
bounded live service reachability verified; **zero** features returned in
the one tested bounding box. No actual building-to-WorldCover validation
is claimed or admitted.

## Primary publisher identity and rights

The [Hessen OGC API catalogue](https://www.geoportal.hessen.de/spatial-objects/711)
explicitly names provider **Hessisches Landesamt für Bodenmanagement und
Geoinformation**, product **INSPIRE-WFS HE Gebäude – 2D ALKIS**, two
collections **Gebäude** and **Gebäudeteil**, the WFS backend
`https://inspire-hessen.de/ows/services/org.2.1f07430b-f7b0-4c4e-a698-fb6c60384f59_wfs?`,
and the catalogue's licence **Datenlizenz Deutschland – Zero – Version 2.0**.

The same official catalogue exposes an
[OpenAPI 3.0 specification](https://www.geoportal.hessen.de/spatial-objects/711/api)
containing `GET /collections/bu-core2d:Building/items` and query
parameters for `bbox`, `limit`, `offset` and output format.
The [official Hessen open-data policy](https://hvbg.hessen.de/geoinformation/open-data)
states automated public access is cost-free except where legitimate
interest for personal information must be checked. This pilot uses
the **non-personal building polygon service** only; it stores no
addresses, feature IDs or owner attributes.

Important: the live service feature's **exact survey/source vintage**
is not determined by these catalogue facts; the mutable ALKIS data
may differ from 2021 ESA WorldCover imagery.

## Original source execution

[GitHub Actions run 41330189760](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41330189760)
completed all **seven** synthetic security/API-geometry tests and a
single constrained original request:

- Source: `https://www.geoportal.hessen.de/spatial-objects/711/collections/bu-core2d:Building/items`
- Frozen WGS84 query: `f=json&limit=5&bbox=9.427,50.489,9.511,50.573`.
- The bbox lies strictly within the previously verified WorldCover
  2021 v200 N48E009 internal block 185.
- UTC: `2026-11-01T17:11:32.263043+00:00`.
- HTTP **200**, GeoJSON **FeatureCollection**, original body **1,001 bytes**.
- Exact raw-source-response SHA-256:
  `8702288c73e43dbd2a265f1bf6b49f0da984901fd7620e2045b89acb39a08dc7`.
- Exact GET request SHA-256:
  `a3dd19b1a6e452361288ce61cb196acde168630dcf8ff0b8fdc39fa945ef4941`.
- Probe code SHA-256:
  `03bdea448ae1bf3012f3d5dd45f9f5de60912335172d32c6c35f9eff40ca2289`.
- Returned features **0**; polygon/multipolygon records **0**;
  coordinate pairs **0**; `numberMatched` not provided as a
  nonnegative integer; no next-page link was followed.

The original metadata-only receipt initially used a vacuous Boolean
`returned_geometry_envelope_intersects_exact_bbox=true` even when
the response contained **zero** features. This is deliberately corrected
in the source probe to return `null` (no geometry checked) and
`geometry_available_in_this_sample=false`. There is no observed
geometry or validated location within this particular sample.

**Do not interpret zero results as confirmed no buildings** within the
bbox, city, region or state, and do not infer the current population,
land use, insurance risk or WorldCover classification from this response.
This proves only that the specified public endpoint accepted the
bounded request and returned a syntactically valid *empty* feature
collection on the execution date. Provider collection coverage,
WFS/backend mapping, feature query semantics, temporal consistency,
true EPSG:4326 coordinates and real geometry quality remain unverified.

## Next bounded research decision

Check an independently chosen, fixed small bbox inside the documented
Hosenfeld settlement area, **within the same WorldCover source block**,
without crawling the Hessen catalogue. If the OGC Features API remains
empty, inspect the official WFS `GetCapabilities` response and
`DescribeFeatureType` under a separate capped original response
contract instead of manufacturing buildings.

A successful **nonempty** bounded official feature response would still
require exact source CRS, polygon validity and geometry geometry-vintage
checks before any comparison to the 2021 WorldCover classes. Building
parts, multipart structures and one-to-many property association must
not be collapsed silently. Retain `model_input_approved=false` and
no insurer/claim/TIV writes until science and provenance review.

## Data-handling boundary

This canary acquires at most five features and a 256-KiB response,
does not follow page links or redirects, and hashes raw source bytes
without logging or persisting original feature IDs, attributes,
raw polygons or geographic coordinates. The immutable source-based
registry is separate from Pokémon databases. No model risk input,
building match or live database mutation was performed.
