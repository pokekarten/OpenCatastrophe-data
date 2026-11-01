<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin official ALKIS building attributes — XSD and source completeness evidence

**Date: 2026-11-01.** Research field gate, not a complete building/insured
risk model. Source and publisher: Berlin's Senatsverwaltung für
Stadtentwicklung, Bauen und Wohnen; official
[ALKIS building WFS catalogue](https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a),
dataset licence **Datenlizenz Deutschland – Zero 2.0**.

## Separate source-backed attribute namespaces

The [original Berlin ALKIS technical field list, June 2022](https://gdi.berlin.de/data/alkis/docs/datenformatbeschreibung_alkis_berlin.pdf)
documents the following **possible** fields for ALKIS building records:
`gfk`/ `bezgfk` (building function code/label),
`aog`/ `aug` (upper/lower floors), `ofl` (above/below ground),
`hoh` (high-rise indicator), `bat` (construction type),
`baw` (construction arrangement), `zus` (condition), plus
source identifiers and address fields. **Possible in the field
dictionary does not mean present and non-null in WFS.** This source
dictionary does NOT establish a uniformly available building
year or exact roof/first height.

A **different** Berlin [Umweltatlas 2022 building-height WFS
technical document](https://gdi.berlin.de/data/ua_gebaeudehoehen/docs/Datenformatbeschreibung_06_10_1gebhoehen2022.pdf)
defines `role_txt` for building vs building-part,
`hoehe` for measured/modelled first height in metres,
`dachart` for roof kind, `geschosse` for storeys
and separate method/footprint-date labels.
**These are NOT ALKIS source fields by default.**
The height/roof product is independent source/vintage/segmentation
and needs its own official rights, live metadata and original-polygon
spatial crosswalk; no name-only joins or synthetic missing-value fill.

## Implemented bounded proof

`research_runners/berlin_alkis_building_attribute_schema_v0.py`
performs **exactly two fixed official HTTPS requests**:

1. WFS 2.0.0 `DescribeFeatureType` for the previously live-confirmed
   `alkis_gebaeude:gebaeude` layer, limited to 2 MiB of XSD.
2. The already reviewed five-feature EPSG:25833 GetFeature sample in a
   200m × 200m bounded Berlin box, limited to 512 KiB of GeoJSON.
   It calls the existing source geometry validation instead of assuming
   valid, independent buildings.

The XML parser forbids DTD/entity injection and service exceptions;
both requests deny redirects, proxies and changed source hosts;
maximal content sizes, media types and UTC/source hashes are checked.
Only an **allowlist of non-personal field names** appears in the output.
For each official candidate field, the public evidence is just the
count of sampled source objects with the property and the count
with a nonempty scalar value. Never log raw values, source IDs,
location coordinates, residential street/house numbers, personal
names or original provider polygons.

Additional `bja/hoehe/role_txt/dachart/geschosse` fields are
separately flagged as **other-product candidates**, not asserted present
in ALKIS. Missing values are retained as unknown. Counts from at most
five WFS features are **not population estimates for Berlin**, nor
equivalent to unique physical buildings, nor evidence of insurer
coverage, building age, vulnerability or replacement value. This
does not modify CAT1/CAT2/CAT4 or any persistent Pokémon/insurance DB.

Execute offline tests:

```bash
python -m pip install -r requirements-eu-flood-spatial.txt
python -m unittest tests.test_berlin_alkis_building_attribute_schema_v0 -v
```

One reviewed first-party source test is performed by the
`.github/workflows/berlin-alkis-attribute-schema-receipt.yml` workflow,
only on its own `main` workflow-file revision or manual dispatch.
A successful first true source run must be entered below with real
response hashes, source official field-list availability and non-null
counts. It must NOT be claimed successful based on synthetic tests.

## Research follow-ups

Do not join by `uuid`, building name, address, feature position, or
ALkIS building feature ID to an Umweltatlas roof facet without
independent geometry, segmentation and provenance checks.
For a useful financial/physical CAT exposure model, inspect source
completeness by geography, identify primary building vs building
part, test building heights/vintages and maintain an explicit
uncertainty label for measured vs derived attributes. Inferred floors
multiplied by footprint are *not observed gross floor area* and
are not automatically insured values.
