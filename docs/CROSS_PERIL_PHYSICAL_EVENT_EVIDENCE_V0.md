<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source-bound research physical event evidence v0

**Status: real provider data validation, synthetic point observations, NOT model admission, not a financial ELT/YLT.** This contract is the *hazard stage before* a calibrated insurer/portfolio/VLT and any NextGen reinsurance, rather than a parallel implementation of NextGen's synthetic multi-peril loss aggregator.

Two independently fetched original sources are evaluated against the **same, synthetic-only longitude-latitude site roster**:

- EFFIS REST v2/current `?id=646790`: official observed burned-area MultiPolygon; synthetic point membership boolean. The original provider payload is mutable. Its SHA-256 identifies **bytes seen at this time**, not an immutable provider release. The EFFIS firedate has an explicit timezone and is normalized to UTC.
- CLIMK–WINDS v2 ERA5 `storm_number=50`, selected index 0: SHA-256 `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102` pinned original NetCDF; maximum gust m/s and separate dimensionless 98th-percentile climatological ratio at nearest native grid centers. No storm-to-COSMO/CCLM event matching.

Each output event has its **own** provider-scoped event key, raw source-byte SHA-256, peril, event-time state, spatial/physical observation semantics, and an ordered roster of observations. A deterministic SHA-256 receipt of the normalized bundle permits byte-exact output comparison.

## Deliberate missing evidence (no guessing)

The existing CLIMK source sampler exports a zero-based storm index but **does not yet export its Storm_Dates calendar value**; `event_time.utc=null` and the status is explicit. It is incorrect to copy EFFIS' date onto CLIMK, to synthesize an annual rate from 50 selected extreme storms, or to claim two different source events are one jointly correlated event. EFFIS burning membership is **not** physical wildfire heat intensity, insured exposure or building destruction. No vulnerability, location ownership, financial sum, RI/retro, or loss probability is applied.

## Reproduction on an internet-enabled runner

Install the existing pinned netCDF4 acquisition-only dependency:

    python -m pip install -r requirements-glofas-acquisition.txt

Create a strictly synthetic site manifest (same schema as the EFFIS and CLIMK point probes):

    {
      "schema_version": "oc-effis-synthetic-sites-v0",
      "crs": "OGC:CRS84",
      "synthetic_only": true,
      "sites": [
        {"site_id":"SYNTH_FIRE_A", "longitude":5.958677287830914, "latitude":52.41546239242131},
        {"site_id":"SYNTH_FIRE_B", "longitude":6.02, "latitude":52.47}
      ]
    }

Run:

    python scripts/reconcile_cat_physical_event_evidence_v0.py --fetch --effis-event-id 646790 --climk-storm-index 0 --sites /tmp/sites.json

The script independently passes both original source files through their already-tested SHA/byte and strict format validators, and compares all synthetic site identities. The EFFIS `current` event may be changed or removed by its publisher, which would require a separately reviewed versioned snapshot; a failed live check must not be disguised as success. The output includes no provider polygon coordinates, source raster arrays, underlying asset values or insurance company identifiers.

CI runs 17 isolated synthetic cases plus a **live** exact-source pair test. These tests should not be interpreted as scientific admission or proof of a joint Monte-Carlo event generator.

## Integration into NextGen

Future work: (1) source-authoritative CLIMK storm dates and matching to independent event IDs, (2) explicit canonical time windows and source-specific hazard units, (3) admitted geographically precise insurer exposure rights/crosswalks, (4) peril-specific calibrated vulnerability and loss sampling with shared random event seeds, (5) treaty/retro ordering. Do not pass this v0 evidence directly into NextGen's C3S 72-hour 3-second-gust stage; it has a different physical unit/measurement contract.

Sources: https://zenodo.org/records/15305753 ; https://forest-fire.emergency.copernicus.eu/about-effis/data-license
