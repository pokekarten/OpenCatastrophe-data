<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EFFIS observed burnt-area synthetic point overlap v0

Research-only bridge between validated EFFIS source GeoJSON MultiPolygon and explicitly synthetic longitude/latitude point markers. **Not** a real policy/site crosswalk, insurance loss model, economic exposure dataset or production CAT connector.

## Native scientific semantics

The original EFFIS REST v2 current endpoint provides an observed burned-area polygon, not an instantaneous wildfire intensity, building damage, fire arrival time or insured claim. The event identity is effis:burntarea:<ID>, whereas the original source payload SHA-256 pins one ephemeral exact response. The current endpoint may change and cannot serve as an immutable historical archive.

Use OGC:CRS84 GeoJSON point coordinates (longitude, latitude); do not silently swap to latitude-longitude. Per RFC 7946 the first ring is exterior and subsequent rings represent holes. This implementation handles hole exclusions and multipolygons; refuses sites on/near a polygon boundary, antimeridian-crossing polygons, invalid input coordinates, duplicate site IDs and unapproved fields. No area/metric-distance or full topology guarantees are claimed.

## Reproduce online

First save an explicitly synthetic input file with the following JSON structure:

    {
      "schema_version": "oc-effis-synthetic-sites-v0",
      "crs": "OGC:CRS84",
      "synthetic_only": true,
      "sites": [
        {"site_id": "SYNTH_A", "longitude": 5.958677287830914, "latitude": 52.41546239242131},
        {"site_id": "SYNTH_B", "longitude": 6.02, "latitude": 52.47}
      ]
    }

Then run:

    python scripts/effis_synthetic_point_overlay_v0.py --event-id 646790 --fetch --synthetic-sites /tmp/sites.json

Output contains only source hash, stable event ID, synthetic roster hash, per-site boolean membership and aggregate counts, **never** polygon coordinates, site coordinates, TIV, Cedant identity, vulnerability or loss. Live CI fetches the mutable EFFIS event and checks two synthetic markers; offline unit tests cover polygon holes, outside, ambiguous boundaries and malformed input.

## NextGen integration gate

The existing NextGen C3S wind stage expects a specific 72-hour maximum 3-second wind-gust measure and a distinct vulnerability model. It must not be repurposed to accept EFFIS polygon membership as physical wind intensity. Before any true insurer exposure overlay or loss calculation, require rights review, immutable event snapshots, independently sourced location-to-asset mapping, true fire intensity/arrival and validated wildfire-specific VLT, loss stage and uncertainty model.

Sources: https://www.rfc-editor.org/rfc/rfc7946 ; https://forest-fire.emergency.copernicus.eu/about-effis/data-license
