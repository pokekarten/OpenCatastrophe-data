<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Historical France 2016: original BD TOPO D077 building polygons vs present-day RNB

**Research-only investigation, 2026-11-01.** The [source intake PR #937](https://github.com/pokekarten/OpenCatastrophe-data/pull/937) now contains an actual 3×2 historical/current polygon comparison, not merely a source-archive download. Both original-source 2016 historical geometry and 2026 RNB current footprints were read live **outside the Git checkout**, and the temporary provider data were deleted. No insurer-specific TIV, property losses, policy data or CAT model admission has been asserted.

## Pinned source and independently executed evidence

The official-origin **BD TOPO 2.1**, department **D077 Seine-et-Marne**, release **24 March 2016**, is present at the [public historical archive mirror](https://files.opendatarchives.fr/professionnels.ign.fr/bdtopo/BDTOPO_2-1_2016-03-24/). The exact 110,738,399-byte mirror archive was downloaded, fully checked with `7z t`, and SHA-256-pinned as `ab3e1bab127d0e71e372d736572d80e6a8a9578131992475c23a1f0ee1871a06`. **This is an independently remeasured mirror SHA, not a published signed IGN original checksum.**

From the 321 archive entries, only twelve original SHP/SHX/DBF/PRJ building components of three historical building families are unpacked to temporary runner scratch. All original `.prj` files validate against **EPSG:2154 Lambert-93**. A bounded WGS84 test box `2.5465–2.5490, 48.5360–48.5380` intersects **three** original 2016 `BATI_INDIFFERENCIE` mapped footprints; `BATI_INDUSTRIEL` and `BATI_REMARQUABLE` add none.

Two exact public **current** RNB building records, `5TR6PNH2YQPT` and `TCHNNF59Y27V`, were separately fetched from the [official public building-lookup API](https://rnb-fr.gitbook.io/documentation/api-et-outils/api-batiments/consulter-un-batiment) with strict status/ID/geographic checks. The API returned valid current MultiPolygons and the status `constructed`; their raw JSON response SHA values are included in the [machine-readable research receipt](fr-bdtopo-d077-2016-rnb-polygon-bridge-receipt-20261101.toml). Those *2026* polygons are not independently historic.

The [successful complete live 2016-vs-current polygon comparison](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41354770553) ran against exactly six possible historical/current pairs. A subsequent run with more precise equality, Hausdorff and symmetric-difference metrics is linked in the receipt; its completion status must be checked independently.

## Six candidate geometric pairings

| Historic original `BATI_INDIFFERENCIE` candidate | 2016 mapped area | Current RNB 5TR6PNH2YQPT | Current RNB TCHNNF59Y27V |
| --- | ---: | ---: | ---: |
| Bounded-selected ordinal 0 (not stable provider ID) | 1,480.23 m² | IoU 0, gap 58.40 m | IoU 0, gap 22.20 m |
| Bounded-selected ordinal 1 | 116.52 m² | IoU 0, gap 54.03 m | **IoU 0.9999999999, overlap 116.52 m²** |
| Bounded-selected ordinal 2 | 59.61 m² | **IoU 0.9999999998, overlap 59.60 m²** | IoU 0, gap 54.03 m |

These near-exact shape overlaps are much stronger temporal-map-footprint evidence than simply comparing two centroids. Nevertheless, precise Shapely `equals()` was false for both near-identical source/current pairings (the symmetric difference area and Hausdorff distances both **round to zero at six decimal places**). Neither result is evidence of mathematical bit-for-bit identity. Historic and current geometries can share upstream IGN/BD TOPO lineage, and therefore are **not independent measurements**.

The third, much larger archived polygon is a separate mapped object, not an additional identified insured risk, and must not be confused with either current RNB ID. Assignment of long-lived building identities, demolition/construction timing and possible splits/merges requires source identity/temporal provenance review.

## Scientific admission constraints

The target is a vintage-aligned historic footprint comparison, **not** validated 2016 physical building status or a financial insurance risk record. In particular:

- The **archive release date** is known to precede the June 2016 flooding, but source-feature observation dates, building construction dates, status and mapping-error history remain to be independently qualified.
- The old **original 2016 archive-specific** rights and authenticity against a verified IGN-origin original hash remain open. Today's Open Licence for modern BD TOPO is not proof that all historical mirror bytes and products are unrestricted.
- Both 2016 buildings and current RNB records have potentially shared BD TOPO geometry lineage. High IoU cannot be used as two independent geometry witnesses.
- The already tested Copernicus `Flooded_area` is topologically invalid in the original FileGDB and distinct from `Estimated_Max_Flood_Extent`. These modelled/observed products have no approved, rights-reviewed, AOI04-specific historic inundation and depth join.
- Neither source establishes historical insured sum, insurer, policy, retention, reinsurance, secondary uncertainty or actual loss.

The matrix is intentionally **research-only**; no archive, SHP, full RNB response or polygon is committed. It explicitly outputs `historic_to_modern_identity_automatically_assigned=false`, `source_independence_proven=false`, `model_input_admitted=false`. No Neon schema or research source approval was modified.

## Next proof step

Use original source feature IDs and edition-specific semantics to distinguish long-lived identity from recycled BD TOPO footprint geometry; confirm exact archival rights and historical vintage. Later, evaluate AOI04 observed satellite flood footprint against verified 2016 polygons with its own timestamp/topology/rights gates. No historical flood damage, individual property loss or 10,000-run CAT model can be inferred from polygon IoU alone.

**Implementation:**
[historic↔RNB geometry bridge](../../research_runners/fr_bdtopo_2016_rnb_polygon_bridge_v0.py),
[synthetic regression suite](../../tests/test_fr_bdtopo_2016_rnb_polygon_bridge_v0.py),
[pinned, temporary-data workflow](../../.github/workflows/ign-bdtopo-2016-d077-receipt.yml).
