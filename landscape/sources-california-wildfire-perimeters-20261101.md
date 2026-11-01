<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-california-wildfire-perimeters-20261101.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-california-wildfire-perimeters-20261101.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission discovery of an original multi-agency CAL FIRE historical wildfire perimeter archive that can be evaluated as a separate, incomplete event geometry counterpart to DINS inspected structure damage; rights, event joins and science approval are deliberately not granted.

**Entries:** 1

## CAL FIRE FRAP Historical Fire Perimeters release firep25_1

**Candidate ID:** `us.calfire.frap.historical-fire-perimeters.firep25-1`  
**Provider:** California Department of Forestry and Fire Protection / Fire and Resource Assessment Program (FRAP)  
**Categories:** `wildfire`, `historical_perimeters`, `event_footprints`, `hazard_validation`, `california`  
**Spatial scope:** California wildland fire perimeter database across public/private lands and multiagency jurisdictions; event completeness and geometry vary  
**Temporal scope:** Source histories back to 1878; frozen published edition firep25_1 released April 2026, records through 2025 (source portal maintained later in 2026)  
**Resolution / granularity:** Polygon per historical wildfire, with event attributes, added tracking Global ID and release-specific collection rules; provider distributes ArcGIS services, CSV, GeoJSON and geospatial archives  
**Potential roles:** `wildfire_event_perimeter_challenge`, `calfire_dins_incident_crosswalk_research`, `historic_area_coverage_and_missingness_qc`, `pre_and_post_fire_exposure_overlay`  
**Access hint:** `public_cc_attribution_portal_arcgis_services_exact_firep25_1_asset_license_api_and_version_review`  
**Authoritative source:** <https://publish.data.ca.gov/dataset/california-fire-perimeters-all>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The provider identifies edition firep25_1, updated annual history and records back to 1878; the perimeters are NOT fire intensity, burned fraction of each building, insured loss, a full census of all wildfires, or an independent DINS building observation. Collection thresholds differ by submitting agency and fuel: CAL FIRE generally &gt;=10 acres timber, &gt;=50 acres brush or &gt;=300 acres grass, OR &gt;=3 impacted structures OR &gt;=1 death, and cooperating agencies &gt;=10 acres. Some perimeters are missing (including documented 2025 Tule), duplicate, imprecise or overly generalized; an old polygon can contain unburned islands. Require exact version, geometry CRS, event year/start date, tracking Global ID/IRWIN ID, official incident-number crosswalk and temporal validity before any DINS point-in-polygon join; joining solely on name is forbidden. Portal labels Creative Commons Attribution and no general public-use restrictions, but exact service access and reuse rights remain unreviewed.
