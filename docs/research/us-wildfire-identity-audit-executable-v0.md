<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# US wildfire: synthetic-only bounded original-ID audit v0

**Research-only. No model-input admission, real provider download or source-rights assertion.**

This adds an executable, fail-closed **identifier-audit research interface** after the merged [MTBS + FPA FOD discovery review](../research/us-wildfire-mtbs-fpa-fod-crosswalk-20261103.md). The **two normalized projection CSVs are caller-prepared private inputs**; column names below are our local research schema and **not** representations of full original FPA FOD or MTBS native tables. No data is embedded or fetched by the tool.

- FPA: exactly `fpa_record_id,mtbs_id,fire_year`; source must be pinned `FPA_FOD_20260615` (the 2026 Seventh Edition).
- MTBS: exactly `mtbs_component_id,mtbs_id,fire_year,event_kind`, with `event_kind` explicitly verified as one of `wildfire`, `prescribed` or `unknown`. MTBS original field mapping must be reviewed separately and the original source release must be fixed, e.g. `MTBS-2026Q3-publisher-reprocessed` **only if proven** by original source metadata.
- Every local CSV must have an externally pinned SHA-256 covering the **actual supplied bytes**. This does not prove original publisher byte identity, since the projection was derived from external assets outside Git and is not yet accompanied by admitted transformation evidence.

The audit reports only **aggregate disjoint FPA row dispositions** and a conservative candidate count. It does not output event IDs, create source-event links, infer physical equality, emit frequency/loss estimates or write to a database.

```sh
python -m research_runners.us_wildfire_mtbs_fpa_fod_crosswalk_v0 \
  --fpa-projection /private/fpa-projection.csv \
  --fpa-sha256 REPLACE_WITH_PINNED_64_CHAR_LOWERCASE_SHA256 \
  --mtbs-projection /private/mtbs-projection.csv \
  --mtbs-sha256 REPLACE_WITH_PINNED_64_CHAR_LOWERCASE_SHA256 \
  --fpa-release FPA_FOD_20260615 \
  --mtbs-release MTBS-EXACT-PUBLISHER-PRODUCT-VINTAGE
```

The research auditor bounds each input to 2 MB and 20,000 rows; these are **small, intentionally selected test slices**, not a full 2.66-million-record FPA FOD analysis. Exit 0 means no selected join contradiction, even if no candidate can be linked; exit 1 means review-needed ambiguity; exit 2 means untrustworthy or invalid input. **None** signals that source admission, scientific independence, insurer event occurrence or rights have been approved.

### Guarded semantics

- `fpa_record_id` and `mtbs_component_id` must be unique *within their own supplied projection*; duplicate records fail.
- An absent MTBS source ID is missing evidence, not absence of wildfire. ID present in FPA but absent from a bounded MTBS subset is not proof of no fire.
- Repeated `mtbs_id` on either side blocks an automatic one-to-one candidate; a wildfire complex with several polygons is not multiple independent CAT events.
- An identical ID with an inconsistent year is flagged, not quietly reconciled; prescribed fire and unknown fire kind are excluded from confident wildfire candidates.
- A candidate selected by source original ID does **not** justify a `same_event` relation for actuarial aggregation, or independent source confirmation. Further documentation is required for MTBS's 2026 reprocessing, native CRS/units, area, fire type mapping, provenance and value-date.
- MTBS burn severity and CAL FIRE observed structure damage remain distinct from financial insurance claims and simulated insured losses.

Deterministic offline negative controls run with:

```sh
python -m unittest tests.test_us_wildfire_mtbs_fpa_fod_crosswalk_v0 -v
python scripts/check_all.py
```

The strict schema, original identifier mappings and source extraction are future reviewed steps. Do not publish real address, policy or insured portfolio observations in fixtures, tests or PR logs.
