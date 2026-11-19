<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hessen ALKIS direct WFS Building: original XSD schema proof

**Original provider run:** [GitHub Actions 41335520724](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41335520724), executed 2026-11-01 18:13:59 UTC.

The reviewed, anonymously accessible official direct source is the Hessisches Landesamt für Bodenmanagement und Geoinformation's WFS 2.0.0 INSPIRE ALKIS 2D Building service. Its [official provider catalogue](https://www.geoportal.hessen.de/spatial-objects/711) labels the layer with the Datenlizenz Deutschland Zero 2.0. This operation requests only one **metadata XSD**, not a feature or geometric polygon.

## Exactly bounded original source evidence

Frozen HTTP GET:

`https://inspire-hessen.de/ows/services/org.2.1f07430b-f7b0-4c4e-a698-fb6c60384f59_wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=DescribeFeatureType&TYPENAMES=bu-core2d:Building`

- Original HTTP **200**, W3C XML Schema, **4,261** bytes.
- Exact source XSD response SHA-256: `52d2e463b40db6bc29fc7dd8ea1a3500eaa7fc24e208fbec3cc52dc407726296`.
- Exact request SHA-256: `23bab0cd01b9b89ab05d8076f39fb79131d65ce242593afcea0eb8cb4f7077ef`.
- Reproducible source code SHA-256: `ae6ce7be30cebe6df36410a1160dfca91c51e582662f8d2dde74b5554cfd3d0d`.
- Target XML namespace **`http://inspire.ec.europa.eu/schemas/bu-core2d/4.0`**.
- **Two** global element declarations were parsed, including `Building`, with type QName **`bu-core2d:BuildingType`**.
- **Two** XSD imports are declared and were **not** followed; zero other source requests were performed. The complete nested building-property and GML geometry schema is **not yet resolved**.
- Six synthetic security tests passed, including malformed XML, XML entities/DTD, unrelated schema namespace, duplicate global Building element, source URL changes and unbounded response.

The previously verified provider evidence remains unchanged:
`GetCapabilities` advertised Building and BuildingPart, default **EPSG:4258 (ETRS89)**; a one-geometry request returned one `Building` XML member but claimed `numberReturned=0`; a separate `resultType=hits` request for the exact Hosenfeld small-area box reported **29** matching records. These facts come from separate source requests and **do not jointly certify 29 actual building footprints**. The provider's contradictory count is still unresolved.

## Safe next source step

The next narrow action is one independent, bounded **GML ring-structure diagnostic** of the already reviewed exact `GetFeature COUNT=1` original source URL. It should require exactly one `Building` in the correct namespace, count GML exterior and interior rings, declare the original CRS/axis order explicitly, validate finite and closed coordinate sequences, compute bounded topology and flags, and **retain the provider `numberReturned=0` inconsistency as an explicit blocker**. Do not export feature IDs, raw GML, WGS84 coordinates, addresses or building attribute values.

No raw XSD, source GML or feature bytes were committed or saved.
`building_type_structure_fully_resolved=false`, `source_building_polygon_validated=false`, `provider_getfeature_number_returned_discrepancy_resolved=false`, `model_input_approved=false`. No insurer or Pokémon database writes.
