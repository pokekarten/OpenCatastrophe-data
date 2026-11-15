<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Croatian DGU cadastral Buildings WFS — original GML geometry gate (2026-11-15)

**State:** bounded research preflight, **not** an admitted exposure dataset or verified original GML run. Related source-science issue: [#1458](https://github.com/pokekarten/OpenCatastrophe-data/issues/1458). No downloaded feature data, addresses, coordinates, identifiers or third-party original bytes are committed.

## Verified publisher / catalogue evidence (reviewed 2026-11-15)

- The **DGU-owned NIPP source catalogue**, [dataset 1543](https://registri.nipp.hr/izvori/1709), explicitly describes 2D building polygons from the **Digital Cadastral Map**, advertised INSPIRE `BU:Building`, GML and an open-licence link. The dataset is not a claim that every current building is represented.
- The **paired WFS service**, [NIPP registry ID 1545](https://registri.nipp.hr/izvori/1711), identifies the original endpoint `https://api.uredjenazemlja.hr/services/inspire/bu/wfs`, Croatia-wide geographic scope, cadastral source, a 2023-12-18 listing date and [Croatian Open Licence](https://data.gov.hr/otvorena-dozvola) as its reuse-terms pointer.
- DGU's [official geoportal](https://geoportal.dgu.hr/cms/en/data-and-services/) lists anonymous **Digital cadastral map Buildings WFS** separately from an anonymous **INSPIRE Buildings ATOM** feed under `geoportal.dgu.hr/services/atom/bu-core2d/xml`. The latter is recorded by the [NIPP 1123 dataset](https://registri.nipp.hr/izvori/1138) as sourced from the **Basic Topographic Database**. They are **not** two verified byte-identical representations of the same buildings.
- Registry records advertise an open licence, but the exact operative licence text, commercial automated/bulk access terms, attribution/derivative requirements and individual-artifact redistribution scope were **not independently completed** in this task. Those gates stay blocked. A catalogue date is not a data-vintage date.

## Original service geometry problem

Issue #1458 records a previous **one-feature GeoJSON** Zagreb-area response with `geometry: null`; a separate earlier GML request timed out. Null GeoJSON does not establish absent source GML polygons. Nor does publisher catalogue language establish actual usable polygon bytes in the requested window.

The 2026-11-15 attempted **one-feature original GML request** via remote HTTP fetch timed out after a 20-second limit. The Linux execution environment could not resolve the provider hostname. Accordingly **no live WFS GML polygon was verified this run**, no feature geometry, national count, coverage or original-byte hash is claimed here.

## Executable fail-closed challenge

`scripts/probe_hr_dgu_buildings_gml_window_v0.py` provides an explicit opt-in `--live` request and an `--offline-file` mode. The only allowed live URL is constructed from the exact official WFS endpoint and a fixed 600 m × 600 m **EPSG:3765** Zagreb research window, `bu:Building`, WFS 2.0, `COUNT=1`, `STARTINDEX=0`; no arbitrary URL, feature ID, authenticated service, unbounded paging or full-country acquisition. WFS request diagonal is approximately 849 m. Network has a 15-second timeout, a 512-KiB response ceiling and refuses redirects, compressed transfer, malformed HTTP framing and unsafe XML declarations.

The XML preflight deliberately supports **only a single explicit inline 2D GML Polygon exterior**: exactly one WFS member, the expected INSPIRE Building namespace, positive nondegenerate closed ring, finite plausible projected XY coordinates, declared EPSG:3765 and an envelope overlapping the fixed window. It rejects missing geometries, wrong classes, unknown geometry encodings, 3D, axis swaps, out-of-window results, multipart payloads and exception reports. Positive output records only source response length/hash and pass/fail claims; no original feature IDs, polygon coordinates, personal data, addresses or building attributes are printed.

Usage (explicit live network only when a reviewer intentionally invokes it):

```bash
python scripts/probe_hr_dgu_buildings_gml_window_v0.py --offline-file /path/outside/repo/original.xml
python scripts/probe_hr_dgu_buildings_gml_window_v0.py --live
python -m unittest tests.test_probe_hr_dgu_buildings_gml_window_v0
```

An offline success is **not proof of provider origin**; only a successful actual `--live` run can mark `live_original_fetch_in_this_run: true`. Even a live positive preflight would confirm just one bounded GML polygon form, not topology/holes, full Croatia coverage, licence clearance, polygon accuracy, insured TIV or CAT-model readiness.

## Next causal evidence

1. Re-run the explicit `--live` command in a network-capable, provider-permitted environment; check original byte count, SHA-256 and the precise GML geometry type. If the original uses GML MultiSurface/Surface rather than Polygon, **retain failure** and add a separately tested exact shape profile; do not weaken the classifier generically.
2. Read the official Croatian Open Licence and DGU service-specific usage conditions in full, capture their dated authoritative evidence, and separate normal dataset reuse rights from automated WFS service restrictions before any bulk retrieval.
3. Independently test multiple small original-provider windows and compare cadastral WFS geometry with **separate** topographic ATOM lineage and EUBUCCO/Overture before any deduplication or exposure admission.
