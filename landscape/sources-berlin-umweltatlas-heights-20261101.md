<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-berlin-umweltatlas-heights-20261101.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-berlin-umweltatlas-heights-20261101.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission research record for Berlin's historical Umweltatlas building-height 2022 WFS, deliberately kept separate from monthly ALKIS and without geometry or attribute retrieval authorization.

**Entries:** 1

## Berlin Umweltatlas 2022 LoD2 building roof height WFS

**Candidate ID:** `de.berlin.umweltatlas-gebaeudehoehen-2022.wfs`  
**Provider:** Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin  
**Categories:** `buildings`, `building_attributes`, `building_height`, `roof_form`, `floor_count`, `germany`  
**Spatial scope:** Berlin, Germany; distinct citywide 2022 Umweltatlas building and building-part height layer, not the current ALKIS building WFS  
**Temporal scope:** Published 2022-04-06, dataset portal updated 2023-08-23; underlying ALKIS footprint source dated 2022-04-07 according to official methodology; not current monthly ALKIS  
**Resolution / granularity:** Individual 2D polygon building/part representations derived from 3D LoD2 with first-height metres, roof type, storeys, method and footprint-date fields; source height may be missing or imputed  
**Potential roles:** `building_height_source_challenge`, `roof_type_uncertainty_review`, `building_attribute_crosswalk_research`, `geometric_segmentation_version_audit`  
**Access hint:** `public_official_wfs_catalogue_capabilities_metadata_only_no_feature_access_approved`  
**Authoritative source:** <https://daten.berlin.de/datensaetze/gebaudehohen-umweltatlas-wfs-d918088d>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official catalogue lists dl-de-zero-2.0; exact downstream rights and API terms still require review. Source explicitly derives roof heights from Berlin LoD2 and historical ALKIS geometry; it is NOT independent ground truth or the same vintage as current monthly ALKIS WFS, and 3 m may be assigned when a height cannot be determined. Technical fields include hoehe, dachart, geschosse, role_txt, source-method and footprint-vintage indicators, but documented fields are not proof of populated live WFS attributes. Preserve missing-vs-imputed status and source method before any scientific join; no automatic identity-by-name, address or feature ID; no TIV, insured location, vulnerability, loss or model input inferred.
