<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EFFIS observed wildfire burned-area polygon research probe

Source: European Commission Joint Research Centre, EFFIS public REST v2, official service at https://api.effis.emergency.copernicus.eu/rest/2/burntareas/current/

Exact schema probe: `?id=646790`, an NL reported burned-area event dated 2026-08-25. Provider returns pagination, a unique event ID, ISO country, timezone-bearing firedate, `area_ha`, `centroid`, `bbox` and a GeoJSON `MultiPolygon` with longitude-latitude coordinates. The service is the **current mutable operational API**; we do not claim the event remains available forever or that the payload is a pinned immutable archival edition.

The code validates event ID, date/timezone, positive area, shape and ring geometry, source host, size cap, and fails closed on missing/duplicate/malformed data. It emits only event-level metadata and a source-payload SHA-256; it never saves raw coordinates or redistributes polygons.

Reproduce:

    python scripts/inspect_effis_burnt_area_v0.py --fetch --event-id 646790

Synthetic regression tests:

    python -m unittest tests.test_inspect_effis_burnt_area_v0 -v

**Semantics:** observed burned-area polygons are not insurer ground-up damage, not vegetation vulnerability and not active fire perimeter at a known instant. For NextGen, events would still require a versioned snapshot, exposure overlap, appropriate vulnerability, coverage terms, suppression effects and independently derived loss data. EFFIS attribution and EU data reuse policy: https://forest-fire.emergency.copernicus.eu/about-effis/data-license. No rights or scientific admission conferred by this probe.
