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



## Named Atom child and five exact ZIP candidates — research verification

The previously verified original Atom root metadata [run
41326959147](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41326959147)
identified only an Atom child, **not** a direct ZIP download. The fixed
child is https://gdi.berlin.de/data/ua_srhk/atom/0.atom. Its public
metadata names five **distinct** ZIP objects. Exact URIs are under
the fixed prefix https://gdi.berlin.de/data/ua_srhk/atom/ :

| Official Atom ZIP filename | Scientific label in the Atom metadata |
| --- | --- |
| \`wasserstand_extrem2022.zip\` | Water depth, extreme scenario |
| \`wasserstand_aussergewoehnliches_ereignis2022.zip\` | Water depth, extraordinary scenario |
| \`fliessgeschw_extrem2022.zip\` | Flow speed, extreme scenario |
| \`fliessgeschw_aussergewoehnliches_ereignis2022.zip\` | Flow speed, extraordinary scenario |
| \`vulnerabilitaetsanalyse.zip\` | Separate persons/vehicles vulnerability product |

These are **links**, not inspected original ZIP or GeoTIFF contents.
The official Atom entry labels links \`type=image/tiff\` even though
their URLs end in \`.zip\`; this is *not* the actual ZIP transport
Content-Type or proof of a valid internal raster.

**Important source conflict:** The Atom child entry describes the
bundle as **EPSG:25833**, including an Atom category \`EPSG/0/25833\`,
whereas the Berlin 2025 official technical
[PDF](https://gdi.berlin.de/data/ua_srhk/docs/Datenformatbeschreibung_SRHK_2025.pdf)
explicitly describes the GeoTIFF files as **EPSG:25832**. The difference
is material for one-metre depth values and metre-scale building
alignment. The real ZIP's GeoTIFF internal GeoKeys / affine georeference
must settle this independently; **do not reproject, join, or assign
depth pixels** based solely on either catalogue label.

The original child combines public parent feed attribution
\`Datenlizenz Deutschland Namensnennung 2.0\`, an entry-level
\`Zero 2.0\` statement for some datasets, and a specific BKG
\`Namensnennung 2.0\` clause for water depth, speed and direction.
The source-by-source licence attribution is **not homogeneous**.
Preserve BKG attribution and source lineage for any water-depth raster;
neither this XML parse nor the provider catalogue automatically
admits a CAT model input.

\`research_runners/berlin_srhk_atom_child_preflight_v0.py\`
performs exactly one fixed child URL metadata GET; 64 KiB cap,
35s timeout, TLS, no redirects/proxies, strict Atom XML identity,
rights gate, exactly five source-specific ZIP paths and duplicate
rejection. It never follows links, downloads ZIPs, decodes TIFFs,
or writes a database. Unit tests only generate synthetic Atom XML;
the reviewed GitHub workflow
\`.github/workflows/berlin-srhk-atom-child.yml\` runs one official
metadata GET **after** the workflow change merges into main,
never on a PR. Record actual original response byte count, SHA,
source version and observed links only after that run succeeds.

**Remaining:** independently review a bounded **HEAD** of one exact
water-depth ZIP for size, MIME, redirects and modification metadata
before any original-byte or raster-window acquisition. The hazards
are simulation **scenarios**, not claims, observed events or a
stochastic catalogue. No source zip contents, pixel depth/NoData,
real building intersection, or synthetic-to-real admission is proven.


## Original official Atom child receipt — 2026-11-01

The single fixed official source-child metadata GET succeeded in
[Actions run 41329862158](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41329862158)
on main commit \`c21c81e9e6a062468924c2e472f2d0f5f23e8206\`.
Response UTC: \`2026-11-01T17:08:21.600038+00:00\`.
Full original **3,527 XML bytes**, SHA-256
\`51a58076f8880e407888c5de75d087037a3db0e99e2526421266c5014c474e37\`.
Execution code SHA-256
\`318a76a6aee0a3e74270e4e8a800ddeaf0d019b63d7c9b703190594929a191d7\`.

Exact five expected URL/role pairs passed, with two water depth,
two flow speed and separate vulnerability ZIP links. The original
Atom category/title explicitly declared EPSG:25833; the reviewed
2025 technical PDF declares EPSG:25832 for its original analysis
GeoTIFFs, so the **true original pixel CRS remains unverified**.
The original Atom links were labelled image/tiff but pointed to ZIP
objects; source MIME is not yet proven. No ZIP content was requested,
no model inputs were admitted, and no production database modified.

## Exact source ZIP HEAD preflight (metadata only)

The next reviewed source operation checks **only two exact HTTPS HEAD
requests** at the original same-host Atom prefix:

- \`wasserstand_extrem2022.zip\` — extreme scenario water-depth ZIP.
- \`wasserstand_aussergewoehnliches_ereignis2022.zip\` —
  extraordinary scenario water-depth ZIP.

\`research_runners/berlin_srhk_water_depth_zip_head_v0.py\`
uses immutable exact URLs, a 40s timeout, no redirects/proxy,
one request per source, no GET/body read, explicit identity encoding,
a declared content-length cap of **20 GiB**, and a narrow set of
ZIP/binary HTTP content types. It records only claimed size, binary
media, last-modified date, whether ETag is present, and whether
Accept-Ranges: bytes is *advertised*. It cannot verify a byte-range
GET, full-object SHA, ZIP magic, internal tiled GeoTIFF metadata,
depth units, NoData, CRS, product vintage or source-rights admission.
Any failed/redirected/missing-Length HEAD remains a **source access
blocker**, never interpreted as zero flood risk.

The isolated workflow \`.github/workflows/berlin-srhk-depth-zip-head.yml\`
runs its synthetic HTTP tests on PR, and real HEAD requests only
after a reviewed workflow revision lands on main. Original outcome: **both verified in separate first-party original requests**,
[GitHub Actions run 41330381774](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41330381774)
on main commit \`1f9f1116d3374e6f67b982bf8984da9499aef375\`.

| Original HTTPS HEAD property | Extreme water depth | Extraordinary water depth |
| --- | --- | --- |
| Content-Length (exact) | **619,211,977 B** | **563,115,763 B** |
| Declared MIME | \`application/zip\` | \`application/zip\` |
| Server Accept-Ranges | \`bytes\` (unproven GET) | \`bytes\` (unproven GET) |
| Last-Modified UTC | \`2025-02-12T06:54:20+00:00\` | \`2025-02-12T06:55:33+00:00\` |
| HTTP HEAD receipt UTC | \`2026-11-01T17:13:59.277252+00:00\` | \`2026-11-01T17:14:07.615626+00:00\` |
| ETag | present, **not** original SHA | present, **not** original SHA |
| Original source ZIP payload bytes read | **0** | **0** |

This HEAD confirms two exact provider file objects exist and report
size, type and range support. It does not establish true ZIP bytes or
internal TIFF code, labels, EPSG or raster scenarios.

## Bounded actual ZIP prefix / Range GET scientific canary

The follow-on reviewed \`research_runners/berlin_srhk_depth_zip_prefix_v0.py\`
checks the two **exact** official filenames only, with exactly one
\`GET Range: bytes=0-511\` per scenario. It requires HTTP **206**,
matching original total byte count from the prior HEAD, exactly
512 returned bytes, identity encoding and valid ZIP local header
\`PK\\x03\\x04\`. It computes SHA-256 of those **512 source bytes
only** and verifies local-header compression method and bounded filename
length without printing the member name or storing raw bytes.

Reject any ignored Range/HTTP 200, changed source URL, changed total,
unexpected MIME, ZIP encryption, malformed header or extra bytes.
A successful prefix **does not** prove complete ZIP contents, central
directory, compressed TIFF tile positions, internal pixel CRS/units,
NoData mask, hazard/vulnerability semantics, full file digest or
building-hazard modelling fitness.

Dedicated source-specific workflow:
\`.github/workflows/berlin-srhk-depth-zip-prefix.yml\` runs
synthetic tests on PR and fixed bounded original requests only
after its reviewed workflow revision is merged on main.
The original prefix outcomes were **both successfully verified** on
2026-11-01 in
[GitHub Actions 41331185963](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41331185963),
merge commit \`620d3650f779acd37faee3aef43ff7e8596ce16b\`.

| Exactly verified source fact | Extreme depth | Extraordinary depth |
| --- | --- | --- |
| Original exact HTTP range | \`bytes 0-511/619211977\` | \`bytes 0-511/563115763\` |
| HTTP status / body bytes | **206 / 512** | **206 / 512** |
| Original 512-byte SHA-256 | \`49c954a118d834e33dac1902c4df3f7df47e9022c963bd966451f9a20b3ee30f\` | \`0486e017feaf9a74b56a351f53e238ed72d45cfe23cdeeda4464fc8f774cd9c8\` |
| Original ZIP local magic | \`PK\x03\x04\` | \`PK\x03\x04\` |
| ZIP version needed | 20 | 20 |
| First ZIP member compression method | 8, Deflate | 8, Deflate |
| First member filename field length (bytes) | 38 | 39 |
| Extra field length (bytes) | 0 | 0 |
| Original read UTC | \`17:23:10.162218+00:00\` | \`17:23:21.327964+00:00\` |
| Raw provider bytes or member names persisted | **No** | **No** |

The exact executing code SHA-256 was
\`e3252822016e348299e38a960f86eb19f74ee92af171523c60e1c1135193c3f5\`.
The sample digest covers **512 bytes each**, not the complete ZIP
archives or their original TIFF contents. The known combined full
object sizes are 1,182,327,740 bytes from HEAD; only 1,024 bytes
of public source body were read across both GETs.
The ZIP local header demonstrates range access and ZIP/Deflate
structure; it does not validate ZIP central directory, archive
completeness, all file CRC-32, TIFF compression, internal
EPSG/depth units, NoData masks or values at Berlin buildings.
The discrepancy between the Atom EPSG:25833 label and the source PDF
EPSG:25832 label is **still unresolved**.

**Next proper scientific source gate:** review a second bounded,
source-version-consistent ZIP *end-of-central-directory* tail Range
(avoiding any bulk download), and enumerate exact archive member
metadata safely before selecting one limited GeoTIFF sample. Validate
full sample geometry CRS, physical depth units and missing support
against verified building polygons only under separate model admission.



**Research security invariant:** source ZIP prefix SHA-256 is a digest of exactly
512 public provider bytes, never an archive-level or GeoTIFF-level digest.
No tile names, full ZIP asset, production CAT database, or privately-held
exposure is exported in this canary. The full repository public-surface
CI must pass at the updated main merge base before any merge.


## Original Berlin water-depth ZIP central-directory EOCD: bounded source gate

The two original 512-byte ZIP prefix ranges and frozen HEAD byte counts
are already verified in
[GitHub Actions 41331185963](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41331185963).
We can safely inspect the *end-of-central-directory* of both
large ZIPs independently rather than downloading their combined
1.18 GB payload.

\`research_runners/berlin_srhk_depth_zip_eocd_tail_v0.py\` makes
**exactly one** full-URL-pinned, no-redirect HTTP GET per
explicit scenario, requesting the last **65,557 bytes** with
\`Range\`. It pins the original HEAD source-object sizes
(**619,211,977 / 563,115,763 bytes**) and the publisher's
earlier Last-Modified timestamp via \`If-Range\`. A non-206,
changed Content-Range, source version, MIME or payload byte length
blocks the operation *before* any unbounded body read.

The bounded local parser:
- Requires one unambiguous classic ZIP EOCD at the true original EOF;
  checks single disk, archive comment length, declared member count,
  exact central-directory end offset and a 1 MiB metadata budget.
  ZIP64, encryption or changed source structures require separate review.
- If the complete central directory **already fits inside the tail**,
  parses central-directory records locally and reports only **counts**
  of TIFF-suffixed and other archive members. It rejects unsafe paths,
  repeated filenames, invalid record lengths, unsupported compression
  and ZIP64 member sentinels. No internal member names/paths are printed.
- If the directory is larger than the bytes already retrieved, reports
  exactly its location and size and **does not** fetch the directory
  or pretend the members were examined.
- Reports SHA-256 of the **65,557-byte suffix only**; not original full
  ZIP archive SHA-256, member CRC, GeoTIFF bytes or physical flood depth.

On a reviewed main-workflow change, two independently bounded runs are
scheduled by \`.github/workflows/berlin-srhk-depth-zip-eocd.yml\`.
PR checks use only synthetic local ZIPs / hostile HTTP fakes, including
a central directory too large for the suffix. The **actual original Berlin source result succeeded on 2026-11-01**:
[GitHub Actions run 41332972926](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41332972926),
main commit \`fd7c2d79d48b0f385b80ab47f14d3557c10e394a\`.

| Exact original-source ZIP EOCD check | Extreme water depth | Extraordinary water depth |
| --- | ---: | ---: |
| Full source ZIP size from prior HEAD | 619,211,977 B | 563,115,763 B |
| Original 206 tail bytes fetched | **65,557** | **65,557** |
| Tail-only original SHA-256 | \`77d39ace530fd0e57e6588e278591e4bf864ddbd9236e27bf77b34bbaa711396\` | \`24b2b2dd85d552fedb13890776bfe15c2be216656f1dac674b07292cc18c9339\` |
| Classic single-disk ZIP EOCD | **Yes** | **Yes** |
| ZIP central directory offset | 619,211,835 | 563,115,620 |
| ZIP central directory byte length | **120** | **121** |
| ZIP declared member count | **1** | **1** |
| TIFF-suffixed member names in original directory | **1** | **1** |
| Unparsed other members | 0 | 0 |
| Archive comment length | 0 | 0 |
| Original UTC | 17:44:14.573418 | 17:44:15.345161 |
| Actual ZIP member payload read | **No** | **No** |

The one ZIP directory record for each source **fit inside the same
65,557-byte tail**. No second central-directory request was needed.
The two ZIPs therefore contain one TIFF-named archive member each,
**not** an independently established tiling of many ZIP members.
The actual TIFF may still be internally tiled.

The source read fetched **131,114 bytes** total, not 1.18 GB.
The ZIP data entry, source CRS, TIFF GeoKeys, internal raster tile
locations, water-depth unit, NoData and actual building overlap
remain unexamined. TIFF file suffix alone does not prove the
internal GeoTIFF scientific format, byte order, coordinate system,
coverage, or decompressibility. The two full archive SHA-256
values and member CRC-32 checks are *not* validated by this metadata
probe. Both source samples are research-only, not admitted CAT inputs.

**Next bounded source gate:** Read the source-pinned ZIP local member
header plus a tiny Deflate-stream prefix and limit decompression
separately, to inspect TIFF magic, IFD/GeoKey metadata and declared
CRS without downloading the complete archive. Preserve original
product lineage, the unresolved 25832-vs-25833 conflict, field
vintage, pixel NoData, and BKG attribution terms.


This is **not** yet a real building-hazard join: EPSG:25832 versus
EPSG:25833, 2022/2025 product naming/vintage, true raster units,
NoData masking and Berlin sample footprint coverage remain source
verification blockers. Next, if source metadata supports it,
obtain a separately reviewed minimal exact GeoTIFF-header sample
without persisting original provider ZIP data.


## First genuine GeoTIFF-header research after one-member ZIP proof

The original [EOCD source run 41332972926](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41332972926)
found exactly **one TIFF-named ZIP member** in each water-depth
scenario, and each directory fits entirely inside the already
reviewed 65,557-byte ZIP tail.

The next step is a separate, strictly bounded research-only
\`research_runners/berlin_srhk_zip_first_tiff_header_v0.py\`.
It requests **only ZIP bytes 0–65,535** of one exact pinned source
at a time. It requires original HTTP **206**, the source total
size from prior HEAD, source Last-Modified if provided,
original ZIP local Deflate method 8, and the **identical original
first-512-byte SHA-256** from run 41331185963. Only then does
it decompress locally using a strict **1 MiB output cap**.
No full source archive, TIFF pixel array or member tile is downloaded.

The parser attempts to establish original TIFF byte order,
classic TIFF versus BigTIFF magic, first-IFD offset, and, **only if
actually present in the bounded decompressed prefix**, the
GeoTIFF projected/geographic EPSG numeric key (34735).
If TIFF IFD tags or their GeoKey payload lie outside the permitted
prefix, values are reported as unavailable. A TIFF magic, or even
one projected EPSG GeoKey, **does not** validate the full raster
affine transform, depth units, NoData mask, coverage, source
licence for CAT/insurance use, event/scenario semantics or
any building overlap. The unresolved Atom/PDF
EPSG:25833/EPSG:25832 conflict cannot be declared solved without
real supporting GeoTIFF metadata.

The dedicated workflow
\`.github/workflows/berlin-srhk-tiff-header.yml\`
runs synthetic-only ZIP/TIFF/HTTP abuse tests on pull requests.
After review and merge of this workflow file, **one original
65,536-byte GET for each scenario** may establish its first TIFF
metadata without committing raw provider bytes. Any required
larger byte range, internal block decoding or full-source
hash requires a separate source-specific review.

**Original TIFF-source verification: SUCCESS, 2026-11-01.**
Both exact original-source probes completed successfully in
[GitHub Actions run 41333661217](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41333661217),
merged source revision \`d6c06812ac82ff0f7516e66b8e62e10bd1c0545f\`
and script SHA-256
\`c2b65f4ff8c4ba10d4e27c1b36d46e615612715e0828159763e84b8d8de0a045\`.

| Actual original TIFF evidence | Extreme | Extraordinary |
| --- | --- | --- |
| Original ZIP HTTP 206 source bytes read | **65,536** | **65,536** |
| SHA-256 of those 65,536 ZIP bytes only | \`9b86b039e4c0915b76f4ea64bc13c201f43483a2585dcdd8f6650d6e1a70579f\` | \`ba22dae2169f3ffab268f9411099e98c5fc3a15cfd8094d6b486b6e9a0c32149\` |
| Repeat first 512 bytes matched original pinned source receipt | **Yes** | **Yes** |
| Bounded in-memory TIFF prefix after Deflate | 110,653 bytes | 111,074 bytes |
| Local decompression 1 MiB cap reached | No | No |
| Original internal format | Classic TIFF | Classic TIFF |
| TIFF byte order | Little endian | Little endian |
| TIFF first IFD offset | **8 bytes** | **8 bytes** |
| First IFD fully read | Yes | Yes |
| GeoKeyDirectoryTag and values read | **Yes** | **Yes** |
| **Internal original TIFF projected EPSG GeoKey** | **25833** | **25833** |
| Geographic EPSG key separately present | No | No |
| UTC original source read | 17:52:36.768745 | 17:52:37.928586 |
| Actual TIFF pixel values interpreted | **No** | **No** |
| Original ZIP or TIFF data persisted | **No** | **No** |

**CRS evidence resolution, with important scope:** The original
TIFF's internal \`ProjectedCSTypeGeoKey\` (tag 34735, key 3072)
explicitly declares **EPSG:25833 on both individual source assets**.
This agrees with the exact provider Atom child label and conflicts
with the technical PDF's generalized EPSG:25832 wording.
For *these two frozen exact source objects*, internal original-file
GeoKey evidence is stronger than a catalogue-level claim. This
does **not** prove complete raster georeferencing or scientifically
approve a spatial overlay: ModelPixelScaleTag (33550),
ModelTiepointTag (33922), pixel grid bounds, NoData,
water-depth **units and scale**, physical vertical reference and
temporal scenario must be independently validated.

The bounded memory read is **not** source TIFF completeness, full
ZIP CRC/digest, correct pixel values, any historic inundation event,
property exposure or insurance CAT-model approval. The
original 2022-named ZIP products have 2025 provider Last-Modified
headers and 2026 retrieval dates; do not conflate these times.
Preserve original depth/velocity attribution to BKG, DL-DE-BY 2.0,
pending product-specific licence review.

**Next source gate:** Require exact original TIFF affine
pixel scale/tiepoints and sample extent to determine whether
the Berlin BLD4 study footprint can be geolocated without
coercing NoData to dry; then independently review depth
units and the scenario's temporal/vulnerability meaning.

