<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WBM 2026: official TED procedure-family sibling discovery

**Research-only, 2026-11-05.** The validated [original BT-04 comparison research](berlin-wbm-2026-ted-bt04-procedure-lineage.md) showed an official *indexed* discrepancy: April competition `286307-2026` was published under procedure BT-04 `7df98c35-4cae-41ff-8385-141125426a4a`, September contract award `668506-2026` under **different** BT-04 `0988b2e4-9489-4b3b-9487-cd3a2a624cf5`. The official publisher Search API exact publication receipts and date are [captured separately](../../research/observations/ted_wbm_2026_search_bt04_lineage_observation_v0.toml). Original simultaneous XML cross-replay was blocked by HTTP 202 and remains stronger evidence than an API index.

## Research question

**Which earlier or later TED notices are indexed under the same exact BT-04 procedure UUID as the September award?** A matching April title or WBM internal procedure ID is insufficient to infer a shared global procedure UUID. Instead of implicitly treating `286307-2026` as September's original competition, search the official TED index for all notices with **exact `procedure-identifier = 0988b2e4-9489-4b3b-9487-cd3a2a624cf5`**. Independently query the April procedure UUID as a control.

The [source-index family reader](../../research_runners/ted_wbm_2026_procedure_family_discovery_v0.py) requests just these two known BT-04 UUIDs from the **official** `POST https://api.ted.europa.eu/v3/notices/search` with a single first page, explicit maximum of 25 results, no syntax-only mode and `onlyLatestVersions: false`. It refuses more than one page of evidence rather than silently truncating; the official result count must match the fully loaded result list. It also rejects wrong-host redirects, duplicate publication rows, mismatching procedure UUIDs, non-WBM buyers, unbounded JSON or missing titles. All response values are *indexed publication metadata*, not the original publisher eForms bytes.

It emits the exact notice numbers, TED official notice-page URLs, indexed publication dates and notice titles for **each procedure family separately**, with source JSON SHA + byte-size as dated audit receipts. It requires the already known anchor notice in each procedure's result family and never merges the two families. It does not store full API JSON, attempt source XML import or declare that every indexed sibling is a confirmed legal predecessor; publication chronology, eForms `previous-notice-id-proc` and finally SHA-pinned original XML need their own independent review.

## Reproduction

```bash
python -m unittest discover -s tests -p "test_ted_wbm_2026_procedure_family_discovery_v0.py" -v
python -m research_runners.ted_wbm_2026_procedure_family_discovery_v0
```

The 21 no-network tests cover exact query scope, original indexed BT-04 allowlists, same family versus different family, wrong provenance, source size and URL abuse, publication duplicates, missing or wrong company and procedure, non-exhaustive pagination and no insurer risk admission. The [dedicated TED provenance workflow](../../.github/workflows/berlin-insurance-ted-original-xml-preflight.yml) runs these tests and an advisory real source query.

**Do not claim:** The April 30/15 tender minimum and residual exception legally governed the September award, actual HDI/Helvetia/R+V policy shares were 50/40/10, nine real site addresses or individual TIVs are known, or actual CAT loss inputs have been validated. This research is exclusively the procurement source lineage needed before those future claims could be investigated.
