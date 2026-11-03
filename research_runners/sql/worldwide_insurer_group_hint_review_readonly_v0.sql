-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY: triage existing insurer organization_candidate.group_hint clusters
-- in the user's independent insurance-risk-core / insurance Neon database.
-- These are unverified research *hints*, not regulator group codes, company
-- identity, accounting consolidation, corporate ownership, or CAT exposure.
--
-- An already-resolved candidate refers to an existing verified legal entity.
-- It DOES NOT verify any relationship between that entity and the hint.
--
-- This query is intentionally a standalone SELECT; no writes, views or tables.
WITH hint_clusters AS (
  SELECT
    btrim(group_hint) AS group_hint,
    count(*) AS candidate_rows,
    count(*) FILTER (
      WHERE identity_resolution_status = 'unmatched'
    ) AS unmatched_candidate_rows,
    count(*) FILTER (
      WHERE verified_organization_id IS NOT NULL
    ) AS already_resolved_candidates,
    count(DISTINCT NULLIF(btrim(home_market), '')) AS distinct_home_market_hints,
    count(*) FILTER (WHERE record_type = 'branch') AS explicit_branch_type_candidates
  FROM entity.organization_candidate
  WHERE group_hint IS NOT NULL AND btrim(group_hint) <> ''
  GROUP BY btrim(group_hint)
)
SELECT
  group_hint,
  candidate_rows,
  unmatched_candidate_rows,
  already_resolved_candidates,
  distinct_home_market_hints,
  explicit_branch_type_candidates,
  CASE
    WHEN unmatched_candidate_rows > 0 AND already_resolved_candidates > 0
      THEN 'P1_MANUAL_IDENTITY_RECONCILIATION'
    WHEN unmatched_candidate_rows >= 3
      THEN 'P2_MULTI_CANDIDATE_REGULATOR_RESEARCH'
    WHEN unmatched_candidate_rows > 0
      THEN 'P3_SINGLE_CANDIDATE_REGULATOR_RESEARCH'
    ELSE 'P4_NO_UNMATCHED_CANDIDATE'
  END AS review_priority,
  false AS regulator_group_code_verified,
  false AS legal_parent_child_relationship_verified,
  false AS model_input_approved
FROM hint_clusters
WHERE unmatched_candidate_rows > 0
ORDER BY
  CASE
    WHEN unmatched_candidate_rows > 0 AND already_resolved_candidates > 0 THEN 1
    WHEN unmatched_candidate_rows >= 3 THEN 2
    ELSE 3
  END,
  unmatched_candidate_rows DESC,
  group_hint ASC
LIMIT 30;
