<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin independent 2022 LoD2 building-height WFS — provenance and pilot

**New, separate source from cadastral ALKIS.** Berlin Open Data official
catalogue [Gebäudehöhen (Umweltatlas) - WFS](https://daten.berlin.de/datensaetze/gebaudehohen-umweltatlas-wfs-d918088d)
lists the Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen as
publisher and **Datenlizenz Deutschland – Zero – Version 2.0**.
The dataset was published 2022-04-06 and its catalogue states an
updated product date **2023-08-23**, not 2026 live building-history
equivalence. The office explicitly states:

- Original *first/roof heights* stem from automated processing of Berlin
  LoD2 3D building models and some buildings have **no calculable height**.
- Footprints are designed to coincide with cadastral ALKIS building
  outlines, but this description alone is not a valid one-to-one ID
  crosswalk or a frozen common historic data vintage.
- Documented **`role_txt` (Gebäude vs Bauteil)**,
  **`hoehe` (Firsthöhe in metres)**, **`dachart` (generalised roof
  type)**, **`geschosse` (storey count)** and `quelle*` estimation
  provenance should be preserved and distinguished. Do not silently
  conflate the LoD2-derived 2022 source with ALKIS 2026 `aog` or
  ALKIS `bat` fields.
- The official technical field list is:
  https://gdi.berlin.de/data/ua_gebaeudehoehen/docs/Datenformatbeschreibung_06_10_1gebhoehen2022.pdf

## Exactly reviewed official access path

The official Berlin portal's **actual linked WFS resource** is
`https://gdi.berlin.de/services/wfs/ua_gebaeudehoehen`
and its official capabilities resource is

`https://gdi.berlin.de/services/wfs/ua_gebaeudehoehen?request=GetCapabilities&service=WFS`.

The source-specific reader
`research_runners/berlin_umweltatlas_height_wfs_metadata_v0.py`
performs at most one bounded 4MiB/35s HTTPS metadata request when
explicitly run with `--live`. It requires WFS 2.0.0, a nonempty
provider building/height-like feature type, published official
EPSG CRS list, correct XML media and root, and no DTD/entity,
redirects, ambient proxy use or alternative query host.

Only public **feature type name(s)**, advertised CRS, source UTC,
original metadata response SHA-256 and script SHA-256 are printed.
No actual height values, building addresses, feature geometries,
roof shapes or property identifiers are downloaded or saved.
The one-shot dedicated workflow runs synthetic-only on PR and the
single reviewed real call on a workflow-revision push to main.

This is an *access metadata proof*, not source dataset admission.
The next pilot should use **exactly one immutable source-specific
`GetFeature` typeName discovered by this live check**, and a small
fixed bbox/count, verify source CRS/field types, obtain actual role
and non-null `hoehe` counts with *values only in memory*, then
independently compare projected footprints with original ALKIS
buildings in the *same query window*. Preserve many-to-one, one-to-many,
time discrepancies, source-provenance flags and unfilled heights.
No raw downloaded feature values or geometry go to a public Git log
or Pokémon or production insurance database.

## First-party source result

Pending the first real exact-source workflow after reviewed merge.
No claim of live API usability or model-ready heights before a
successful provider receipt.
