<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Overture Maps buildings: October 2026 source-identity and non-admission checkpoint

**Review date:** 2026-11-03. **Published release:** `2026-10-21.0`.
**Schema:** `v2.0.0`. This is a source registry and identity research note;
no original Parquet, building geometry, insurer data, coordinates, event loss
or external provider bytes are committed.

## Direct publisher references and checked claims

- [Official release calendar](https://docs.overturemaps.org/release-calendar/):
  `2026-10-21.0` is the current published October release at this review;
  the next release is only **proposed**, not verified present.
- [Official buildings guide](https://docs.overturemaps.org/guides/buildings/):
  `building` footprints and `building_part` features have different
  identifier semantics. Global GeoParquet is publicly listed on S3/Azure under
  the **exact versioned release path**, not a permanently fixed unversioned
  alias. The building theme conflates OSM/community, public and machine-learned
  footprints and is distributed under **ODbL** with source attribution and
  compatible-source requirements.
- [Official GERS identifier definition](https://docs.overturemaps.org/gers/):
  **A UUID alone does not establish GERS membership**. The `building` type
  participates in the [GERS registry](https://docs.overturemaps.org/gers/registry/);
  `building_part` has its own deterministic UUID without the same stability
  promise. The published GERS bridge file covers **one-to-one matches**; other
  ambiguous or conflated relationships require separate resolution.
- [Official October 2026 release notes](https://docs.overturemaps.org/blog/2026/10/21/release-notes/):
  the provider reports **2,533,842,612 buildings** and **4,486,107 building
  parts**, unchanged in that release from the September building data.
  These are **provider-reported release totals**, not an independently
  downloaded or validated count of unique insured structures.

## Required independent identity and CAT gates

1. Freeze a **versioned original object path**, size and SHA-256 receipt,
   track source-family provenance and verify region/feature partition budgets.
   A public bucket URL or matching filename is not the same as a verified
   downloaded original.
2. Resolve `building` GERS membership **through the registry** and use
   bridge files only for their documented one-to-one semantics. Preserve
   original contributor identity and release; do not double-count the
   Microsoft/Google/OSM/Esri inputs that Overture itself conflates.
3. Evaluate ODbL attribution, derivative-data and commercial-use obligations
   for the *actual proposed* export and combination. The catalogue status
   remains `rights_review_status=not_reviewed`,
   `scientific_review_status=not_reviewed` and `admission_status=not_admitted`.
4. Test asset footprint validity, locality and **historical** source vintage.
   A roof polygon is not an insurer asset, occupancy, insured value, policy
   attachment or matched catastrophe hazard cell; distinguish buildings
   from building parts and prove real exposure completeness separately.
5. Keep any future geospatial joins, provider original bytes, operator tokens
   and insurer exposure outside this **public references-only repository**.
   Explicitly review database landing, access and source rights in an isolated
   authorized environment before any scientific/model admission.

## Repository integration

This narrow registry update copies **only the existing Overture entry**
refresh in canonical `landscape/sources-exposure-impact-validation.json` and
its generated Markdown projection from research draft
[PR #1107](https://github.com/pokekarten/OpenCatastrophe-data/pull/1107).
All other registry entries and their admission status are unchanged.

The parent research draft separately contains source acquisition, Overture
building/ACT geospatial checks and dependencies. Those are **not** approved,
copied or run by this candidate metadata update. The October release refresh
must not be misreported as a fully world-available CAT building exposure.
