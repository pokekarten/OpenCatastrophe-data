<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GRWL original 2018 ↔ 2026: direction-aware WGS84 vertex correspondence

Reviewed 2026-11-04. This is a **bounded source-science experiment**, not a geodetic accuracy certification, hydrologic crosswalk, flood map, model input or insured loss result.

## Upstream original evidence

The two original Zenodo GRWL simplified ZIPs were successfully downloaded, independently SHA-256 verified, and compared in the trusted-main GitHub workflows:

- [Original ZIP byte proof run 41822336297](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41822336297): original 2018 ZIP SHA-256 `16830e5444d47d6ba74790613533b6a81b4036a15f3ad7a7066241da28f95306`; 2026 ZIP SHA-256 `78aa43a7104d24b1696e9b1547347eec13ba5d660aa990c1e7cea98e7ae70e4a`.
- [Keyed original width and XY proof run 41852020214](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41852020214): 42,077 unique matching numeric `OBJECTID` values in identical record order; zero changed values for all five GRWL width fields at matching export `OBJECTID`; 42,077 changed `SHAPE_LENG` values; 37,355 changed SHP XY byte sequences, leaving 4,722 byte-identical pairs. See the [GRWL original aggregate receipt](grwl-original-aggregate-semantics-20261104.md).

Equal widths by export identifier do not prove that identifier is a permanent hydrologic identity. Original WGS84 XY hashes differing do not establish physically meaningful spatial relocation.

## Next causal measurement

`research_runners/grwl_original_oriented_vertex_metric_v0.py` reacquires only those two exact original source ZIPs into ephemeral runner-local temporary storage and **requires both original ZIPs' independently verified exact SHA-256**. ZIP safety and original SHP/DBF structure are inherited from the reviewed upstream validators. Only the reviewed `main` workflow may perform source downloads; PR heads run offline synthetic fixtures.

It streams original polyline SHP geometries and aligns their records by the independently verified unique candidate `OBJECTID` from the original DBF. For each candidate matched pair, it distinguishes:

1. **Byte-identical XY payloads and part structure**.
2. **Orientation-only or multipart-order-only differences**, under exact coordinate equality after reversing vertex order per part or reversing the order of multipart segments.
3. **Comparable vertex sequences that really differ**, where the part and point-count structure can be aligned after direction or complete part-order reversal. It selects the pairing with lowest sum of **squared spherical great-circle vertex separation**, then reports a *feature maximum* vertex-to-vertex separation in approximate metres.
4. **Noncomparable part/vertex topology**, for which a distance is **not** estimated, rather than incorrectly saying zero.

The code checks finite longitude/latitude ranges, original record numbering, byte lengths, part offsets and vertex limits before comparison. The positional metric uses a fixed mean Earth radius of 6,371,008.8 m and the haversine formula.

**Interpretation limits:** this is a *best-orientation pointwise correspondence* at matching vertex ordinals, not a geodesic Hausdorff or Fréchet distance, not nearest segment/river separation, not EPSG-specific reprojection, and not an estimate of flood-stage water width or hydrologic uncertainty. A shifted/densified/resegmented polyline with a changed point count is **not** assigned a displacement. A coordinate recorded with more digits may produce a nonzero but negligible metric. A reversed vertex order alone must contribute exactly zero displacement.

## Evidence output

The program publishes **only bounded aggregate metadata**: source SHA-256 identities; matched export `OBJECTID` count; counts in the four categories above; p50/p95/p99 and maximum of per-feature *maximum corresponding-vertex distance* for comparable features; and number of features exceeding each threshold (0.01, 0.1, 1, 10, 100, 1,000 m). It never prints original source IDs, exact vertices, extents, river geometry, or original records; it does not upload a source ZIP artifact or persist data outside the GitHub runner.

Synthetic tests:

```bash
python -m unittest tests.test_grwl_original_oriented_vertex_metric_v0 -v
```

Execution is intentionally disabled without the explicit `--live` option, and live acquisition runs only on reviewed main via `.github/workflows/grwl-original-oriented-vertex-metric.yml`.

## Decision boundary

These statistics can narrow whether source differences are exact orientation reversals, tiny numeric serialization differences or substantial corresponding-vertex offsets. They cannot validate feature identity, topology, riverbank alignment, hazard intensities, probabilities, insurer synthetic portfolios or net/gross OEP/IP. Real RiverATLAS conflation, independent spatial holdouts, legal attribution and explicit scientific model-input admission remain necessary.

**Current source-result status at PR creation:** the new orientation-aware *original-data* run has not yet executed; do not invent its displacement counts. Original ZIP byte hashes and the previous keyed values above are already confirmed by prior reviewed runs.
