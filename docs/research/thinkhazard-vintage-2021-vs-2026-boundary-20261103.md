<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ThinkHazard release-vintage trap: 2021 archived score table ≠ 2026 portal

**Reviewed:** 2026-11-03. **Status:** qualified metadata/rights distinction; no downloaded data or scientific/model admission.

The already-registered source `worldbank.gfdrr.thinkhazard.screening-scores`
covers risk-screening classes for multiple natural hazards, **not**
event footprints, event recurrences, calibrated exceedance curves or insured losses.

## What the providers actually publish

1. [World Bank data catalogue record 0060151](https://datacatalog.worldbank.org/search/dataset/0060151/thinkhazard-hazard-ranking) is a 7.9 MB *Excel hazard ranking table*, with **data file last updated 2021-11-29** and catalogue metadata last updated **2025-03-07**. The record explicitly lists **CC BY 4.0** for that dated product. This is archived administrative ADM0/ADM1/ADM2 hazard classification.
2. [Current ThinkHazard portal](https://int.thinkhazard.org/en/about) explicitly reports a **2026-09-18** publication of its data. The updated [ThinkHazard documentation](https://gfdrr.github.io/thinkhazard/) describes new hazard layers, administrative ADM0/ADM1/ADM2 and about 3,000 major urban areas. This is **not proved identical** to the 2021 catalogue file; source-layer rights, taxonomy and urban boundaries require release-specific evidence.
3. [ThinkHazard source guidance](https://int.thinkhazard.org/en/faq) says it is **not** a real-time event feed or historical events database, and it applies hazard classes derived from other provider layers. The original layers retain their own licences; a class alone cannot be treated as a depth, acceleration, expected loss, storm occurrence or building damage.

## What was changed

- Kept the one existing canonical candidate ID. Edited only its temporal
  scope, spatial/granularity description and provenance note in
  [the peer source JSON register](../../landscape/sources-peer-cat-repositories-20261102.json).
  Its admission and scientific status are still `not_admitted` and
  `not_reviewed`; the rest of the previously registered sources did not
  change.
- Added a source-specific **documentation-only** access contract
  [for the 2021 World Bank catalogue record](../../access/worldbank.gfdrr.thinkhazard.screening-scores.2021-wb-catalogue.json),
  with dataset rights marked verified **only for that exact 2021 CC BY 4.0
  record**, while API service automation remains unknown and all probes
  remain disabled. It does not claim a permission to acquire the provider
  file, follow URLs or redistribute layers created by third parties.
- Preserved exact deterministic Markdown projections and added offline
  regression controls so a future edit cannot silently present the
  older Excel archive as the 2026 hazard score release.

## Why it matters for the global CAT platform

We can use the **dated score product** as a coarse external screening
or country/admin risk-priority comparison after scoped rights and format review.
We cannot use a VLO/LOW/MED/HIG classification as hazard intensity,
building-level damage or an actuarial event occurrence law. The newer
portal version requires separately pinned published data, source
methodology, spatial support, original layer licences, explicit data
quality, and versioned national boundary/urban-area semantics.

Next actual source work: verify one exact downloadable file identity and
metadata/version/byte receipt, not a full-site crawl or random
unversioned API call. A future source adapter should refuse records with
no version label or unknown administrative geometry support.

**No external provider file bytes or credentials were fetched or written
to Git, Neon or any insured portfolio.**
