<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NHSL v1.0: original XLSX read and Nunavut GPKG archive byte identities

**Research date:** 2026-11-04. **Provider:** Geological Survey of Canada / Natural Resources Canada via [OpenDRR original GitHub release v1.0](https://github.com/OpenDRR/national-human-settlement/releases/tag/v1.0) and [Government of Canada Open Data](https://open.canada.ca/data/en/dataset/1818cf27-03ea-4ebb-bc43-fd371b42198b).

This report **supersedes** the previous claim in [our first NHSL canary](nhsl-arcgis-original-three-area-canary-20261104.md) that the original v1.0 XLSX dictionary had not been downloaded/parsed. It now **has** been directly acquired and parsed, with a reproducible cryptographic fingerprint. The Nunavut ZIPs have also been fully acquired as bytes, hashed, and their central-directory member identities read. However, their **internal GeoPackage SQLite features have not yet been independently parsed** during this research run. The new local offline validator below performs that additional check when provided the actual files outside the repository.

## Primary original-release binary receipts

All bytes below came from the **exact** original v1.0 GitHub release download URLs. No provider ZIP/XLSX bodies or original geospatial records are committed here. ZIP member metadata (single member, method 8/deflate, size, CRC-32) are evidence from the source ZIP central directory. SHA-256 values are **locally computed** from full downloaded original file bytes, not a GitHub-signed checksum; release assets are mutable until independently versioned and retained, hence the byte pin.

| Original release asset | Byte size | SHA-256 of whole original asset |
| --- | ---: | --- |
| [`nhsl_physical_exposure_attributes_en.xlsx`](https://github.com/OpenDRR/national-human-settlement/releases/download/v1.0/nhsl_physical_exposure_attributes_en.xlsx) | 17,888 | `e191efb7662c1442c8da7379f54a86e710d6f7c63ff76b2bad89550c9ac55ca8` |
| [`nhsl_physical_exposure_indicators_s_nu.zip`](https://github.com/OpenDRR/national-human-settlement/releases/download/v1.0/nhsl_physical_exposure_indicators_s_nu.zip) | 73,663 | `8da41815457b3a163de09be24691ffaf972c4b34ced69dfacabc00723275032b` |
| [`nhsl_physical_exposure_indicators_b_nu.zip`](https://github.com/OpenDRR/national-human-settlement/releases/download/v1.0/nhsl_physical_exposure_indicators_b_nu.zip) | 113,156 | `c5b3e15bf1050712aba4d6b627f1a40bf616d4cfde8cf28f77967c9973ea0bdb` |

| ZIP filename | One embedded GeoPackage member | Original member bytes | CRC-32 from ZIP |
| --- | --- | ---: | --- |
| `..._s_nu.zip` | `nhsl_physical_exposure_indicators_s_nu.gpkg` | 233,472 | `187affd2` |
| `..._b_nu.zip` | `nhsl_physical_exposure_indicators_b_nu.gpkg` | 876,544 | `c641a5fc` |

The two ZIP assets were obtained through **bounded HTTP byte-range requests** to the same original release download URLs; each range was checked for its expected byte length before reassembly, and the complete resulting ZIPs were SHA-256 hashed. This proves whole-file retrieval and exact member inventory, **not** the correctness of any internal GPKG table or its model validity.

## Original XLSX sheets, fields and units versus the live MapServer

The official 17,888-byte XLSX was parsed from its original zipped Office XML and yielded the original publisher's `Summary`, `polygons`, and `buildings` worksheet content. The original dictionary publishes:
- **62 fields** on `polygons` (settlement-area polygons; `Et_*` aggregate stock, cost and area), and **38 fields** on `buildings` (taxonomy/archetype point attributes; `E_*`).
- Buildings/archetypes are **represented at the settled-area centroid**, not physically surveyed individual rooftops.
- `Et_BldgArea`, `E_BldgArea`: **square feet (`ft2`)**, not square metres.
- `Et_BldgValue`, `Et_StrValue`, `Et_NStrValue`, `Et_ContValue` and `Et_AssetValue`: **CAD** replacement-cost estimates, generally aggregated with `SUM`. Their use here remains 2019-CAD in accordance with original product metadata, **not insured policy TIV**.
- Important original dictionary spelling versus current [polygon MapServer layer 1](https://maps-cartes.services.geo.ca/server_serveur/rest/services/NRCan/physical_exposure_en/MapServer/1?f=pjson) and [archetype layer 0](https://maps-cartes.services.geo.ca/server_serveur/rest/services/NRCan/physical_exposure_en/MapServer/0?f=pjson):

| Product/sheet | XLSX original field | Current MapServer observation | Disposition |
| --- | --- | --- | --- |
| Polygons | `fasuid` | `fsauid` | **Source naming/version discrepancy**; must not silently map by case/guess |
| Polygons | `Et_ResHD` | `Et_Res` and other service fields | These **cannot be assumed semantically equal** |
| Buildings | `E_BlgEpoch` | `E_BldgEpoch` | Typographic/name drift; require content and epoch-code review |
| Buildings | `E_SSCZone` | `SSC_Zone` | Naming/version mismatch; cannot assume identical classification |
| Buildings | `fasuid` | `fsauid` | Different exact spelling |
| Both | source worksheets `polygons`=62; `buildings`=38 | live layer 1=64; layer 0=43 | These are **different schema surfaces**, despite substantial overlap |

**Exact source-field set comparisons:** original XLSX polygons vs live layer 1 had **53 common names**, nine XLSX-only, eleven service-only; XLSX buildings vs live layer 0 had **35 common names**, three XLSX-only, eight service-only. Do **not** confuse those original-release numbers with our earlier 66-name GitHub documentation YAML, which is a separate, possibly evolved documentation surface. A real release GeoPackage schema reconciliation is needed to determine which differences are in the distributed data and which are documentation-only.

## Executable next verification on source packages (no data committed)

[Offline binary/checksum+XLSX/GeoPackage preflight](../../scripts/nhsl_v1_original_binary_preflight_v0.py), with [synthetic-only tests](../../tests/test_nhsl_v1_original_binary_preflight_v0.py).

- Requires **all three exact original assets** and pins the locally observed original SHA-256, provider asset length, sole GPKG member name, member decompressed length and CRC. Changed bytes cannot pass by merely copying filenames.
- Reads XLSX with bounded stdlib ZIP/XML operations and checks source-critical fields from both original product sheets.
- Unzips only the two **small** Nunavut GeoPackages outside Git, checks ZIP safety and SQLite header, opens them **read-only**, validates `gpkg_contents`, `gpkg_geometry_columns`, `gpkg_spatial_ref_sys`, geometry family, CRS metadata consistency, exact critical fields and SQLite integrity.
- Reports only **schema identity and number of feature rows**; does not emit actual regional feature rows or coordinates, does not write OED CSV or insurer portfolio, and never sets `source_admitted=true`.
- Does **not** yet prove `SUM(archetype value per SAUID) = polygon SAUID value`. That needs a separate bounded cross-layer scientific reconciliation after the **actual** GPKG schemas and contents have passed.

A local researcher can reproduce by downloading *the exact three public official provider assets* to `/tmp` (for example, with `curl --fail --location --max-time 60 --max-filesize 1000000` against the links above), then:

```bash
python scripts/nhsl_v1_original_binary_preflight_v0.py \
  --dictionary-xlsx /tmp/nhsl_physical_exposure_attributes_en.xlsx \
  --polygon-zip /tmp/nhsl_physical_exposure_indicators_s_nu.zip \
  --archetype-zip /tmp/nhsl_physical_exposure_indicators_b_nu.zip

python -m unittest discover -s tests -p 'test_nhsl_v1_original_binary_preflight_v0.py' -v
```

**Observed proof this run:** full original XLSX was downloaded and parsed, and full original Nunavut ZIPs were downloaded, hashed and ZIP-central-member-inspected. **Not yet observed:** run of the validator on decoded original GPKG SQLite structures, original SAUID cross-layer conservation or reliable native CAT model execution. Do not claim completion of those steps until independent executable receipts exist.

**Rights and scientific position:** The original provider catalog identifies the Open Government Licence — Canada, with attribution and third-party caveats. Commercial use may be allowed at the publication level, but exact workflow/admission/legal suitability and scientific validation are still separately unreviewed; keep `admission_status=not_admitted`, `oed_insured_locations_exportable=false`.
