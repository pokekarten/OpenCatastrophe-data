<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-berlin-alkis-pilot-20261101.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-berlin-alkis-pilot-20261101.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission research registration of the exact official Berlin ALKIS building WFS product already tested in a bounded fixed five-feature canary; source-derived footprint staging and CAT4 discovery metadata remain strictly separate.

**Entries:** 1

## Berlin ALKIS official buildings WFS (monthly mutable)

**Candidate ID:** `de.berlin.alkis-gebaeude.wfs`  
**Provider:** Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin  
**Categories:** `buildings`, `building_footprints`, `exposure`, `germany`, `government_register`  
**Spatial scope:** Berlin, Germany; official cadastral building and building-part WFS; one fixed 200 m by 200 m research bbox verified  
**Temporal scope:** Current mutable WFS, updated monthly; original per-building validity and 2021 presence unknown; research receipt 2026-11-01  
**Resolution / granularity:** Individual source Polygon/MultiPolygon features in requested EPSG:25833; fixed five-feature anonymous sample; no complete census  
**Potential roles:** `building_geometry_validation`, `regional_exposure_source_provenance`, `cat4_derived_footprint_stage`  
**Access hint:** `public_official_wfs_exact_bounded_existing_canary_only_rights_review_before_scaled_acquisition`  
**Authoritative source:** <https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official provider catalogue states Datenlizenz Deutschland Zero 2.0 for the published layer; confirm feature/derivative scope and any attribute restrictions before scaled reuse. Existing source-specific fixed WFS GetCapabilities and five-feature GetFeature canaries verified five source polygons in Berlin DE3, with checksum and original-source geography. The optional BLD4 SQLite stores source-derived polygons and aggregate provenance only; it is NOT the CAT4 source research registry and not a policy, insured location, 2021 building census, building age, replacement value, independent hazard validation, or CAT model input. Preserve monthly update identity, source SHA/time, EPSG:25833, CAT1/CAT2 2021 boundary vintage, and the no-admission boundary.
