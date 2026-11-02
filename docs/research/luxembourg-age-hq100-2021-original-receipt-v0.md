<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg AGE HQ100: exact original 2021-model / 2022-release archive receipt

**Status: read-only provider file-format and provenance gate. No flood depth / hazard footprint admission.**

## Publisher source and version

Publisher is the Administration de la gestion de l'eau (AGE). The official
[HWGK2021 HQ100 catalogue](https://data.public.lu/en/datasets/flood-hazard-maps-100-year-flood/)
describes *modelled 100-year floodplain and water depth* pursuant to Directive 2007/60/EC.
It lists the original [ZIP resource](https://download.data.public.lu/resources/flood-hazard-maps-100-year-flood/20220613-154804/hwgk2021-hq100.zip)
as **3.9MB** with resource UUID `1f529004-dd4d-42f1-8bd3-3b33a3f54ffd`,
publisher SHA-1 `41b58cb5e0c9509d39824919dce85702ceda0540`,
updated **13 June 2022** and catalogue label **CC0**. The paired 63.4MB
GeoJSON resource has a *separate* original SHA-1 and must not be assumed
byte- or object-equivalent before independent comparison.

**Separate product:** The INSPIRE Natural Risk Zones HQ100 catalogue
https://data.public.lu/en/datasets/inspire-annex-iii-theme-natural-risk-zones-flood-hazard-maps-100-year-flood-3/
lists its GML asset as **modified 8 December 2025**, not 11 August 2026.
Its separately listed WMS service was updated **16 February 2026**.
A WMS publication date is not an underlying hazard model date; never assume
those products share feature IDs, depth intensity semantics or vintage.

## Reproducible exact-original source gate

`research_runners/luxembourg_age_hq100_2021_original_preflight_v0.py`:

1. Requires a regular non-symlink ZIP within a fixed byte limit, exact
   **publisher SHA-1**, and records an additional SHA-256 receipt. SHA-1 is
   publisher-reported version identity, not a secure signature or independent
   authenticity guarantee.
2. Rejects ZIP path traversal, symlinks, encryption, duplicate members,
   decompression bombs, oversized expansion and inconsistent or malformed
   SHP/DBF/PRJ headers.
3. Fully streams every member for CRC checking. Reads *only* SHP main
   header (shape type), DBF metadata/field descriptor names and declared row
   count, and bounded PRJ text for **keyword hints**, without emitting any
   source feature, coordinate, geometry, depth measurement or identifier.
4. Prints only archive-level member suffix counts and bounded file-header
   findings, with explicit `depth_units_verified=false`,
   `actual_hazard_geometry_read=false` and
   `model_input_admitted=false`. Original bytes are deleted in the
   GitHub runner, not stored in Git/Neon, or exposed in action artifacts.
5. Uses synthetic-only regressions to reject changed source SHA, unsafe
   ZIP paths, symlinks and corrupt inputs.

The separately scoped GitHub Actions workflow
`.github/workflows/luxembourg-age-hq100-2021-original.yml` fetches only
the exact resource at the fixed official HTTPS URL, and runs this script
after its synthetic gate. **Actual file structure and observations must be
taken from a successful real-original run, not inferred from the catalogue
description.**

## Next scientific steps

- Verify the original actual file format, complete record and field counts,
  CRS and axis ordering; identify how the provider encodes simulated
  water depths and units (or whether the ZIP contains only polygons).
- Freeze source release, coordinate transformation, scenario, depth units,
  and numeric decoding rules with a separate, small *real original-feature*
  inspection, whose detailed locations never enter Git.
- Make a bounded exact-source spatial overlap study against the separately
  tested Luxembourg ACT 2026 GeoBase physical polygons; distinguish
  independent source vintages and interpretation of 100-year scenario.
- **No real insurance portfolio or insured property value is available from
  official flood and building geometry alone.** A model loss requires
  separately sourced physical exposure meaning, vulnerability, insurer TIV,
  policy and reinsurance conditions and an admitted hazard intensity layer.

