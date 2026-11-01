<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin pluvial flood: independently scoped WFS metadata and original raster routes

**2026-11-01 — source-access research only.** This is the next scientific
source gate after the 5-building source-derived Berlin BLD4 staging and the
synthetic flood-depth polygon/grid overlay. It is NOT a real building/hazard
join, a simulation result, a complete source admission, a loss estimate or
proof of coverage of the sample building box.

## Two different official original products

1. **Berlin 2025 Starkregenhinweiskarte**: authoritative open-data
   [WFS catalogue](https://daten.berlin.de/datensaetze/starkregenhinweiskarte-wfs-882d18d8),
   service `https://gdi.berlin.de/services/wfs/ua_srhk`, official
   catalogue licence **Datenlizenz Deutschland Namensnennung 2.0
   (dl-de-by-2.0)**. The hazard indication includes 2025 BKG
   rainwater-surface modelling plus other original official information.
   Its WFS technical
   [source documentation](https://gdi.berlin.de/data/ua_srhk/docs/Datenformatbeschreibung_SRHK_2025.pdf)
   explicitly identifies **four separately downloadable Atom ZIP /
   GeoTIFF** raster layers in **EPSG:25832**: water levels and
   flow velocities for extraordinary and extreme rainfall scenarios.
   This *technical raster channel is separate from WFS polygon/point
   feature access*. Do not treat a WFS layer display or a WMS colour
   pixel as a metre-valued raster sample. BKG's extreme rainfall
   scenario is not automatically an observed historical event.
2. **Berlin detailed Starkregengefahrenkarte**: authoritative
   [WFS catalogue](https://daten.berlin.de/datensaetze/starkregengefahrenkarte-wfs-1aa4f1ef),
   service `https://gdi.berlin.de/services/wfs/ua_srgk`,
   catalogue licence **CC BY 4.0** (product-specific attribution
   details). The product uses coupled **1D sewer / 2D overland flow**
   calculations for rare/extraordinary/extreme scenarios. Unlike the
   indicative map, detailed calculated coverage is **only available in
   some parts of Berlin**, not necessarily around the frozen
   central-Berlin ALKIS BLD4 box `391700,5819950,391900,5820150`.

The two maps must be treated as different source families: scenario,
topography, model-resolution, geometry vintages and known data inputs
differ. They may share upstream BKG/ALKIS/source components; thus
neither can be assumed an independent validation ground truth for
the other or used as insured losses.

## Reviewed bounded live research step

`research_runners/berlin_starkregen_wfs_capabilities_v0.py` makes
**one exact, anonymous, HTTPS WFS 2.0 GetCapabilities request per
explicitly chosen source**. Requests have a fixed full URL and
read-only GET, TLS verification, no proxy or redirects, a 35s timeout,
2 MiB XML cap and no credentials. It checks WFS XML structure, duplicate
layers, CRS advertisements and invalid XML/DTD. Only public feature
type names, CRS declarations, response byte counts/SHA-256,
retrieval UTC and code SHA are reported.

`tests/test_berlin_starkregen_wfs_capabilities_v0.py` contains
synthetic XML/HTTP abuse and exact-URL tests, with no provider calls.
The one-shot workflow `.github/workflows/berlin-starkregen-wfs-metadata.yml`
runs the synthetic checks on PRs but issues source requests **only
on a reviewed workflow revision merged to main**, or a separate
explicit manual dispatch. Each source has an independent job so
one source's failure does not suppress the other's result.

### Decision boundary

- A successful WFS capabilities response only proves that *service
  metadata* can be fetched, not that a water-depth layer or a
  meter-valued hazard grid is downloadable by WFS.
- ZIP/Atom GeoTIFF discovery and downloading require a **separate
  source-specific bounded access review**, exact object identity,
  source licence/redistribution/derivative review, file/ZIP-size
  limit, full-object SHA-256, projection and pixel/mask semantics.
- The official hint-map GeoTIFF uses **EPSG:25832**; BLD4 building
  polygons are **EPSG:25833**. Any real join needs an explicit
  reproducible, non-ballpark transformation in a reviewed raster
  runtime. Non-overlap must remain missing support, never "dry".
- Product temporal mismatch is unresolved: current monthly mutable
  ALKIS buildings vs maps derived from multi-year public/nonpublic
  inputs. Event/scenario is not a loss event or a Monte-Carlo
  stochastic catalogue.
- No source feature, raster pixel, coordinates, provider XML,
  building geometry, customer/claim data or production DB rows
  are persisted by this metadata probe.

## First original-source receipts — verified 2026-11-01

One source-specific push run successfully acquired both original official
GetCapabilities XML responses separately, with SHA-256 of exact *full XML
responses* (not source GeoTIFF pixels):
[GitHub Actions 41326524953](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41326524953),
source revision `407db39ca24929d7290b2c6030076ff46ab5904e`.

| Original verified fact | Hinweiskarte `ua_srhk` | Gefahrenkarte `ua_srgk` |
| --- | --- | --- |
| Source UTC | 16:28:49.123060 | 16:28:48.061324 |
| Exact XML bytes | **102,825** | **99,749** |
| XML SHA256 | `973949ab86bcab676d6f707bb4cbd0c90e91bb30437612f645bd28c85f3309b5` | `f5d21c48864dca82692a08bdccce0fb42d04172682ab9a35688458be5d84a0d9` |
| WFS protocol | 2.0.0 | 2.0.0 |
| Feature types actually enumerated | **7** | **4** |
| EPSG codes advertised | 25832, 25833, 3857, 4258, 4326 | 25832, 25833, 3857, 4258, 4326 |
| Original GetFeature, XML storage, hazard pixels | None | None |

**Original seven hint-map WFS layer names (public metadata):**
`ua_srhk:bb_srhk_feuerwehreinsaetze`,
`ua_srhk:ba_srhk_feuerwehreinsaetze_pkt`,
`ua_srhk:ca_fr_aussergewoehnlich`,
`ua_srhk:da_fr_extrem_max100mm`,
`ua_srhk:fa_alkis_gebaeude`,
`ua_srhk:a_srhk_starkregengefahrenkarten_vorhanden`,
`ua_srhk:g_srhk_senken`.

**Original four detailed-map WFS layer names (public metadata):**
`ua_srgk:ca_fliessgeschwindigkeit_aussergewoehnlich`,
`ua_srgk:da_fliessgeschwindigkeit_extrem`,
`ua_srgk:ba_fliessgeschwindigkeit_selten`,
`ua_srgk:a_modellgebiete`.

**Important correction to source readiness:** neither observed WFS
`FeatureTypeList` directly exposes a verified numerical GeoTIFF
water-depth analysis band. Its layer names cannot establish WFS water
depth coverage or unit semantics. For the indicative map, the official
technical description separately documents Atom GeoTIFF products; their
feed and exact ZIP object access must be independently tested. The
detailed map WFS lists flow-speed layers and model-area footprint, so
treat **partial model-area coverage** as a separate gating source.

Only service metadata accessibility is verified. Provider response
bytes were not persisted and no BLD4/insurer CAT model or DB modified.


## Exact Berlin SRHK Atom root – separate metadata access experiment

The official Berlin source information for the `Starkregenhinweiskarte`
identifies a separate Atom feed at
`https://gdi.berlin.de/data/ua_srhk/atom/`. This is distinct from
both observed WFS XML GetCapabilities endpoints and the actual
EPSG:25832 GeoTIFF depth/velocity ZIPs. The source documentation
describes download availability, **not** an exact authorized ZIP
identity or current ZIP digest.

`research_runners/berlin_srhk_atom_root_preflight_v0.py` performs a
single explicit **root-only** metadata GET after main-review workflow
update; 1 MiB max response, 35s timeout, TLS, no redirects or
proxy, strict Atom XML root, DTD/ENTITY rejection, 300-entry and
500-link caps. It **does not follow** Atom links, child feeds or
any ZIP/download. It reports only aggregate link/media counts,
response size/SHA/time and negative source-data/model-admission flags.
An HTML directory, changed URL/format, oversized feed or invalid
XML is an explicit blocker, never misclassified as downloadable
hazard pixels.

One-off workflow:
`.github/workflows/berlin-srhk-atom-root.yml`.
Only synthetic XML tests on pull requests. A reviewed workflow file
change on main authorizes **one** original root metadata request.
A subsequent ZIP selection/fetch must have its own separately
documented exact URL, rights review, hash, byte budget and
decompression/CRS/nodata/units proof before any physically meaningful
BLD4 building flood grid comparison.

**Original Atom root result: VERIFIED metadata access on 2026-11-01.**
The independent exact-source [GitHub Actions run 41326959147](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41326959147)
on merge commit `703eb660cae29c26b7f9c100e0a64c07843bb264` executed
one fixed root-only HTTPS GET, without redirects or child requests.
Original response UTC: `2026-11-01T16:33:54.698388+00:00`.
The original **3,276-byte** Atom 1.0 XML source response had SHA-256
`cd99acadcdae8c448ccd1922498cbfc2ca1f9ec3defd4c27b920c702adf36300`.
The exact execution script SHA-256 was
`52ff5b03336b47bf1952b8a8fc9683852a023fbfa363b9391065b15a680a5797`.

- XML root: valid Atom 1.0; **one entry**, **four links**.
- Link relation counts: `alternate=1`, `describedby=2`, `self=1`.
- Advertised MIME counts: `application/atom+xml=2`, `application/xml=2`.
- **Direct ZIP URLs in the root = 0**. This does not contradict
  the provider's downstream ZIP/GeoTIFF publication; the root
  appears to link further Atom metadata, which was deliberately
  **not followed** in this proof.
- No original XML was stored; no child feed, ZIP, GeoTIFF, flood
  depth pixel, source-building intersection or CAT model input
  was accessed or approved.

**Next bounded decision:** identify *which* exact same-provider Atom
entry/child feed advertises the correct 2025 extraordinary/extreme
Wasserstand analysis product, check its licence, CRS, download
format, byte budget and original ZIP product identity, then independently
approve a second fixed-source metadata query. Do not infer any depth
unit, return period, dry pixel or sample coverage from the root.

