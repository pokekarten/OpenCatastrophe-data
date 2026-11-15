-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Read-only CAT source-registry / repository-asset coverage profile.
-- Execute with explicit Neon project/branch/database selection.
-- Missing repository_asset rows mean "not indexed here", not that GitHub
-- files or upstream originals do not exist; no changes or admissions.
WITH classified AS (
  SELECT s.source_key,s.classification,s.repo,s.git_path,
         s.review_status,s.rights_status,s.admissible_for_raw,
         EXISTS (
            SELECT 1 FROM registry.repository_asset a
            WHERE a.repository=s.repo AND a.git_path=s.git_path
              AND a.git_blob_sha=s.git_blob_sha
         ) AS exact_index_match,
         EXISTS (
            SELECT 1 FROM registry.repository_asset a
            WHERE a.repository=s.repo AND a.git_path=s.git_path
         ) AS path_index_match,
         (s.canonical_url IS NULL OR btrim(s.canonical_url)='') AS no_canonical_url
  FROM registry.source_record s
)
SELECT classification,
       COUNT(*)::bigint AS registered_sources,
       COUNT(*) FILTER (WHERE exact_index_match)::bigint AS exact_blob_indexed,
       COUNT(*) FILTER (WHERE NOT exact_index_match AND path_index_match)::bigint AS path_only_different_or_unknown_blob,
       COUNT(*) FILTER (WHERE NOT path_index_match)::bigint AS not_indexed_in_repository_asset,
       COUNT(*) FILTER (WHERE no_canonical_url)::bigint AS missing_direct_source_url,
       COUNT(*) FILTER (WHERE admissible_for_raw)::bigint AS admitted_raw_sources,
       COUNT(*) FILTER (WHERE rights_status IN ('not_reviewed','unknown','restricted','conflicting','to_review') OR rights_status IS NULL)::bigint AS known_unreviewed_or_restricted_rights,
       FALSE AS source_file_missing_proven,
       FALSE AS source_admission_granted
FROM classified GROUP BY classification ORDER BY classification;
