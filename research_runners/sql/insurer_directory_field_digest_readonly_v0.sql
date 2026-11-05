-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Independent read-only CAT-Neon SHA-256 for the five exact source fields.
-- Run on insurance-risk-core/main after an original 46-page source receipt.
-- Compare canonical_field_digest_sha256 from the source receipt exactly
-- with canonical_neon_row_sha256 from this query. No name-only matching,
-- data correction, provider-byte hash substitution or model admission.
WITH integrity AS (
  SELECT count(*) AS row_count,
         count(DISTINCT source_slug) AS unique_source_slugs,
         count(*) FILTER (
           WHERE source_slug IS NULL OR country_slug IS NULL OR display_name IS NULL
              OR class_code IS NULL OR provider_verification_claim IS NULL
         ) AS missing_fields,
         count(*) FILTER (
           WHERE position(chr(30) in source_slug || country_slug || display_name ||
                          class_code || provider_verification_claim) > 0
              OR position(chr(31) in source_slug || country_slug || display_name ||
                          class_code || provider_verification_claim) > 0
         ) AS reserved_delimiters,
         count(*) FILTER (WHERE model_input_approved) AS model_approvals
  FROM research.insurer_directory_candidate_v0
), digest AS (
  SELECT encode(sha256(convert_to(string_agg(
      source_slug || chr(31) || country_slug || chr(31) || display_name ||
      chr(31) || class_code || chr(31) || provider_verification_claim,
      chr(30) ORDER BY source_slug COLLATE "C"
  ), 'UTF8')), 'hex') AS raw_digest
  FROM research.insurer_directory_candidate_v0
)
SELECT i.row_count, i.unique_source_slugs, i.missing_fields,
       i.reserved_delimiters, i.model_approvals,
       CASE WHEN i.row_count = i.unique_source_slugs
                 AND i.missing_fields = 0 AND i.reserved_delimiters = 0
            THEN d.raw_digest ELSE NULL END AS canonical_neon_row_sha256,
       'source_slug,country_slug,display_name,class_code,provider_verification_claim'
         AS canonical_neon_field_order,
       '0x1f-fields-0x1e-records-utf8' AS canonical_neon_encoding,
       false AS model_admission_granted
FROM integrity i CROSS JOIN digest d;
